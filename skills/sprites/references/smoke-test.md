# Smoke test (end-to-end confidence)

Use after OAuth works (or when the user runs `/sprites-smoke` / asks to verify Sprites). Proves list, create, exec, and optionally destroy via **MCP only**.

## Preconditions

- Sprites MCP tools available. If not → [auth-and-setup.md](auth-and-setup.md) class A/B; stop.
- Do not install the CLI or call the REST API.

## Steps

1. **`list_sprites`**
   - Success: list or empty array.
   - Note any shared name prefix on existing sprites (hint only).

2. **`create_sprite`** with a short-lived name:
   - Prefer `mcp-smoke-<shortid>` when the session has no known prefix (product default is `mcp-`).
   - If create fails with “must start with `X`”, retry once as `Xsmoke-<shortid>` (or `X` + slug).
   - If the user already has a known prefix from this session, use it.
   - Report actual name, status, URL. **Cold is OK.**

3. **`exec`** on that sprite, e.g.:
   - `uname -a` or `echo smoke-ok`
   - Summarize exit status and one line of output.

4. **Cleanup (default: ask)**
   - Unless the user already said to destroy when done, **ask** before `destroy_sprite`.
   - If they want it kept, say how to reuse the name later.
   - If they confirm destroy, call `destroy_sprite` and confirm it is gone (optional re-list).

## Report format

```text
Sprites smoke test
- list: OK (N sprites) | empty (OK)
- create: <name> — <status> — <url>
- exec: exit <code> — <brief output>
- destroy: skipped (kept) | destroyed | not requested
- prefix learned: mcp- | <other> | full-access (none)
```

## Failures

| Step | Action |
|------|--------|
| list auth error | Class B — user completes OAuth; do not continue create |
| create prefix error | One retry with required prefix; then report |
| create cap | Explain cap; do not loop creates |
| exec fail | Report output; leave sprite for user unless they want destroy |

Keep the whole smoke test to a few tool calls. No package installs, no services, no network policy changes.
