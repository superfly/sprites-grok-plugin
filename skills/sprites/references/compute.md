# Remote compute with Sprites

Use this when Grok needs isolated Linux compute for agent tasks: builds, tests, generated code, previews, or long-running services.

**Prerequisite:** Sprites MCP tools must already be available and authenticated. If they are not, stop and follow [auth-and-setup.md](auth-and-setup.md). Do not install the Sprites CLI or call the REST API from the shell to continue this playbook.

## Decision

| Situation | Prefer |
|-----------|--------|
| Edit current repo, local git, quick file reads | Local Grok tools |
| Untrusted / generated code execution | Sprite |
| Heavy `npm install` / compile / integration tests | Sprite |
| Dev server or worker that should stay up | Sprite service |
| Need snapshot/restore of whole environment | Sprite checkpoint |
| User said "sandbox", "remote", or "on a sprite" | Sprite |

## Bootstrap a task environment

1. **Select or create** a sprite (`list_sprites` → reuse if clearly matching; otherwise `create_sprite` with a task-scoped name. Prefer `mcp-…` when the session has no known prefix — that is the usual restricted OAuth default; learn any custom prefix or full-access rule from API errors — see [auth-and-setup.md](auth-and-setup.md)).
2. **Baseline tools** with short `exec` probes (`node -v`, `python3 --version`, `git --version`, package managers). Install only what the task needs.
3. **Checkpoint** a clean baseline (`checkpoint_create`, comment like `baseline-after-tooling`) before large installs or untrusted runs.
4. **Bring code in** (pick one — details in [files.md](files.md)):
   - `git clone` of a remote repo the user named (preferred when public or credentials exist in the sprite).
   - Generate small files via `exec` using the **base64 + space-free `python3 -c`** pattern (not heredocs — they usually break under MCP `exec`).
   - Ask the user how to get private code in if clone is not possible (token, upload, or they sync another way). Do not invent secrets.
5. **Run the work** with `exec` for one-shots; use services for processes that must stay up.
6. **Verify** with tests, health checks, or `service_logs`.
7. **Report** sprite name, commands run, exit status, URLs, and checkpoint ids. Offer cleanup only if the user wants it.

## Running tests and builds

- Prefer non-interactive flags (`CI=true`, `--yes`, etc.) so `exec` does not hang on prompts.
- Cap long jobs with awareness of MCP tool timeouts (plugin default is generous; still prefer detachable service patterns for multi-hour work).
- On failure: capture the last relevant log lines, fix inside the sprite, re-run. Use a checkpoint before speculative fixes when the tree is valuable.

## Long-running processes

Do not leave an interactive or forever-blocking `exec` as the primary pattern for servers.

1. `service_create` with a stable name (`web`, `api`, `worker`).
2. Set `http_port` when the process serves HTTP.
3. `service_start`, then `service_logs` / `service_get` to confirm.
4. Share the sprite URL and port guidance with the user. Assume exposure may be public — never put secrets in HTTP responses.

Details: [services.md](services.md).

## Parallelism and isolation

- One sprite per risky experiment or agent subtask when isolation matters.
- Reuse a sprite when the user is iterating on the same environment and wants persistence.
- Fork-style workflows: checkpoint before a branch of work; restore if it goes wrong (restore discards later filesystem state — confirm first).

## Teardown

- Stop services you started if they are no longer needed (`service_stop`).
- Destroy the sprite only with explicit user request or clear approval after summarizing what will be lost.
- Leaving idle sprites is fine (Sprites can idle cheaply) unless the user wants a clean org.

## Writing files (short)

No MCP file tool. **Do:** `git clone`, or base64-decode via space-free `python3 -c` on the sprite. **Don't:** heredocs, nested quotes, or `stdin: true` without a content body. Full guide: [files.md](files.md).

## Anti-patterns

- Treating local `run_terminal_command` as if it runs inside the sprite.
- Registering a second MCP server with `npx mcp-remote` when the plugin already provides Sprites.
- Putting API keys into sprite HTTP endpoints or world-readable files without the user asking.
- Destroying or restoring without confirming impact.
- Writing sprite files with heredocs / complex quoted shell through `exec` (use [files.md](files.md)).
