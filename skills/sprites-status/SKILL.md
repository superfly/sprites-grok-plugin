---
name: sprites-status
description: >
  Check whether the Sprites plugin MCP is loaded and authenticated. Use when
  the user runs /sprites-status, asks if Sprites is working, or wants a setup
  status check without creating resources.
---

# /sprites-status

Verify Sprites readiness for this Grok session. **MCP only** — do not install the CLI or call the REST API.

## Steps

1. **Discover tools** via the integration tool search for Sprites (`list_sprites`, etc.).
2. If **no Sprites tools**:
   - Report: MCP not loaded.
   - Recovery (short): enable plugin with `--trust`, trust project if local install, reload, `grok mcp doctor sprites`.
   - Stop. Load [../sprites/references/auth-and-setup.md](../sprites/references/auth-and-setup.md) class A if needed.
3. If tools exist, call **`list_sprites`**.
4. Interpret:
   - **Auth error / OAuth required** → class B: complete browser OAuth or `/mcps` → sprites → authenticate; empty list not reached yet.
   - **Empty list** → authenticated; no sprites visible (success).
   - **Non-empty list** → summarize count; name, status, URL for each (cap detail if many).
5. Mention name prefix only if known from prior session context or names on the list; otherwise note that the prefix is set on the OAuth consent screen (default often `mcp-`).

## Output

```text
Sprites status
- MCP tools: available | missing
- Auth: OK | needs OAuth | unknown
- Sprites: N (or empty)
- Next: <one line>
```

Do **not** create or destroy sprites in this command.
