#!/usr/bin/env python3
"""Validate the repository's structured and text files."""

from __future__ import annotations

import json
import re
import sys
import tomllib
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIPPED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
TEXT_SUFFIXES = {
    ".json",
    ".md",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains a duplicate key."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def repository_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not SKIPPED_DIRECTORIES.intersection(path.relative_to(ROOT).parts)
    )


def validate_text(path: Path, errors: list[str]) -> str | None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None

    relative = path.relative_to(ROOT)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{relative}: not valid UTF-8 ({exc})")
        return None

    if text and not text.endswith("\n"):
        errors.append(f"{relative}: missing final newline")
    for number, line in enumerate(text.splitlines(), start=1):
        if line != line.rstrip():
            errors.append(f"{relative}:{number}: trailing whitespace")
    return text


def validate_json(path: Path, text: str, errors: list[str]) -> None:
    try:
        json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")


def validate_toml(path: Path, text: str, errors: list[str]) -> None:
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid TOML ({exc})")


def validate_yaml(path: Path, text: str, errors: list[str]) -> None:
    try:
        yaml.safe_load(text)
    except yaml.YAMLError as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid YAML ({exc})")


def validate_svg(path: Path, errors: list[str]) -> None:
    try:
        ET.parse(path)
    except ET.ParseError as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid XML/SVG ({exc})")


def markdown_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    elif " " in target:
        target = target.split(" ", maxsplit=1)[0]
    return urllib.parse.unquote(target.split("#", maxsplit=1)[0])


def validate_markdown_links(path: Path, text: str, errors: list[str]) -> None:
    for match in MARKDOWN_LINK.finditer(text):
        target = markdown_target(match.group(1))
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"{path.relative_to(ROOT)}: broken local link {target!r}")


def validate_skill(path: Path, text: str, errors: list[str]) -> None:
    relative = path.relative_to(ROOT)
    if not text.startswith("---\n"):
        errors.append(f"{relative}: missing YAML frontmatter")
        return
    try:
        frontmatter, _body = text[4:].split("\n---\n", maxsplit=1)
        metadata = yaml.safe_load(frontmatter)
    except (ValueError, yaml.YAMLError) as exc:
        errors.append(f"{relative}: invalid YAML frontmatter ({exc})")
        return
    if not isinstance(metadata, dict):
        errors.append(f"{relative}: frontmatter must be a mapping")
        return
    if metadata.get("name") != path.parent.name:
        errors.append(f"{relative}: skill name must match directory name {path.parent.name!r}")
    if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
        errors.append(f"{relative}: skill description must be a non-empty string")


def main() -> int:
    errors: list[str] = []
    files = repository_files()

    for path in files:
        text = validate_text(path, errors)
        suffix = path.suffix.lower()
        if text is not None and suffix == ".json":
            validate_json(path, text, errors)
        elif text is not None and suffix == ".toml":
            validate_toml(path, text, errors)
        elif text is not None and suffix in {".yaml", ".yml"}:
            validate_yaml(path, text, errors)
        elif suffix == ".svg":
            validate_svg(path, errors)

        if text is not None and suffix == ".md":
            validate_markdown_links(path, text, errors)
        if text is not None and path.name == "SKILL.md":
            validate_skill(path, text, errors)

    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(files)} repository files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
