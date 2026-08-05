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

    def test_root_and_packaged_mcp_configs_agree_on_connection(self) -> None:
        """The two configs must stay in sync on how to reach the server.

        They deliberately differ on attribution headers only — see the
        attribution tests below.
        """
        root = dict(self.root_mcp["mcpServers"]["sprites"])
        packaged = dict(self.packaged_mcp["mcpServers"]["sprites"])
        packaged.pop("headers", None)
        self.assertEqual(root, packaged)

    def test_root_config_sends_no_attribution(self) -> None:
        """The root .mcp.json is the generic project-scoped config that Grok,
        Claude Code, and Cursor all read. Attribution headers here would label
        any client used in a checkout of this repo as Grok.
        """
        self.assertNotIn("headers", self.root_mcp["mcpServers"]["sprites"])

    def test_packaged_config_sends_attribution(self) -> None:
        """Fly-Client-Interactive is the instrumentation sentinel: without a
        parseable boolean, client-signals discards Fly-Client-Agent too and the
        request classifies as uninstrumented. "grok" is the canonical tag from
        client-signals spec/markers.json; any other spelling normalizes to
        "other". See the Client attribution section in the README.
        """
        self.assertEqual(
            self.packaged_mcp["mcpServers"]["sprites"]["headers"],
            {"Fly-Client-Interactive": "false", "Fly-Client-Agent": "grok"},
        )

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
