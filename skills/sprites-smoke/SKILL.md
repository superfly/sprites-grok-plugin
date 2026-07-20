---
name: sprites-smoke
description: >
  End-to-end Sprites smoke test via MCP: list, create, exec, optional destroy.
  Use when the user runs /sprites-smoke or asks to verify Sprites works after
  install or OAuth.
---

# /sprites-smoke

Run the full confidence check. Follow **[../sprites/references/smoke-test.md](../sprites/references/smoke-test.md)** exactly.

## Summary

1. Ensure Sprites MCP tools are available (if not, same recovery as `/sprites-status`; stop).
2. `list_sprites` — empty is OK.
3. `create_sprite` — prefer `mcp-smoke-<shortid>` if prefix unknown; on prefix error retry once with the required prefix.
4. `exec` a trivial command (`uname -a` or `echo smoke-ok`).
5. **Ask** before `destroy_sprite` unless the user already said to tear down when done.
6. Print the smoke-test report block from smoke-test.md (list / create / exec / destroy / prefix learned).

No CLI install, no raw API, no second MCP registration.
