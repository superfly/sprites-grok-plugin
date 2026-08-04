from __future__ import annotations

import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class GrokPluginRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_json(ROOT / ".grok-plugin/plugin.json")
        self.packaged_mcp = load_json(ROOT / self.manifest["mcpServers"])
        self.root_mcp = load_json(ROOT / ".mcp.json")

    def test_manifest_references_existing_content(self) -> None:
        self.assertTrue((ROOT / self.manifest["mcpServers"]).is_file())
        expected_skills = {"sprites", "sprites-smoke", "sprites-status"}
        actual_skills = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(actual_skills, expected_skills)

    def test_manifest_repository_matches_this_repository(self) -> None:
        self.assertEqual(
            self.manifest["repository"],
            "https://github.com/superfly/sprites-grok-plugin",
        )

    def test_root_and_packaged_mcp_configs_match(self) -> None:
        self.assertEqual(self.root_mcp, self.packaged_mcp)

    def test_mcp_server_uses_https(self) -> None:
        server = self.packaged_mcp["mcpServers"]["sprites"]
        parsed = urlparse(server["url"])
        self.assertEqual(server["type"], "http")
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "sprites.dev")
        self.assertEqual(parsed.path, "/mcp")
        self.assertGreaterEqual(server["tool_timeout_sec"], 60)


if __name__ == "__main__":
    unittest.main()
