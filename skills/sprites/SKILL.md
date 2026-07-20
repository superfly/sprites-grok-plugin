---
name: sprites
description: >
  Use Sprites for isolated remote compute from Grok Build: create sandboxes,
  run commands and tests, manage long-running services, checkpoint and restore
  filesystem state, and control outbound network policy. Invoke whenever the
  user mentions Sprites, sprite environments, remote sandboxes, cloud sandboxes,
  agent compute, running code remotely, or the Sprites MCP server — and when
  Grok needs durable isolated Linux compute that should not run on the local
  machine (untrusted generated code, heavy builds/tests, long-running servers,
  experiments that need snapshots). Also invoke for Sprites plugin setup, MCP
  auth, OAuth, name prefix errors, smoke tests, or troubleshooting missing
  Sprites tools. When writing files on a sprite, load references/files.md (no
  write_file MCP tool; use git clone or base64 + space-free python3 -c via exec).
---

# Sprites

Sprites are hardware-isolated, persistent Linux environments with their own filesystem, public URL surface, background services, checkpoints, and outbound network policy. This skill runs in **Grok Build on the local machine**, outside the sprite.

**Control plane:** the **Sprites MCP tools** from this plugin (`https://sprites.dev/mcp`). That is the only supported path for agent-driven Sprites work.

## When to use Sprites (compute routing)

Prefer Sprites over the local shell when:

- The user asks for a sandbox, remote environment, or isolated compute.
- You need to run untrusted or generated code safely.
- Builds, tests, or dependency installs would pollute or overload the local machine.
- Work needs a long-running process (web server, worker, database) with a reachable URL.
- You want reversible filesystem experiments via checkpoints.
- The task needs a clean Linux environment independent of the user's laptop.

Stay local when the task is purely about editing the current workspace, reading local files, or git operations the user expects on this machine.

## References

| Topic | Load when |
|-------|-----------|
| [auth-and-setup.md](references/auth-and-setup.md) | First run, tools missing, OAuth, prefix/policy errors, install/trust |
| [smoke-test.md](references/smoke-test.md) | Verify setup end-to-end; user wants a smoke test |
| [compute.md](references/compute.md) | Bootstrap remote compute, bring code in, tests, teardown |
| [files.md](references/files.md) | Writing/reading files on a sprite; `exec` quoting; base64 write pattern |
| [services.md](references/services.md) | Long-running processes, ports, logs |
| [safety.md](references/safety.md) | Destroy, restore, public exposure, network policy |

## Golden path

1. Call Sprites MCP tools directly for all sprite operations.
2. **Empty `list_sprites` is success** (org has no sprites yet, or none visible under the token policy). Offer to create one if useful.
3. If tools are missing or auth fails, **stop and diagnose** via [auth-and-setup.md](references/auth-and-setup.md). Do not continue with CLI/API workarounds.
4. OAuth: wait for the user to finish the browser flow, then retry **once**.
5. **Name prefixes** are set on the OAuth consent screen for **restricted** tokens (product **default is `mcp-`**; user may choose another non-empty prefix). **Full access (no prefix)** is a separate choice: bare names allowed, but **unrestricted access to all sprites in the org**. Discover the live rule from API errors and session creates — do not hardcode a single prefix as universal.
6. Keep replies concise: names, status, URLs, checkpoint ids — not MCP registration chatter.

## Stop conditions (fail closed)

If Sprites MCP tools are **not available** or **cannot authenticate**, stop workarounds. Explain the failure class and recovery from [auth-and-setup.md](references/auth-and-setup.md).

### Forbidden

- Install the Sprites CLI or run `sprite login` / `sprite org auth` as a substitute for Grok OAuth
- Raw HTTP to `api.sprites.dev` or inventing tokens
- Register a second MCP server when this plugin already provides `sprites`
- Pretend the local shell is inside a sprite

### Allowed when blocked

- Classify: tools missing vs auth incomplete vs policy/prefix
- Give short recovery steps; wait for the user
- On **prefix errors only**, auto-retry create with the required prefix (see below) — that is using MCP correctly, not a workaround stack

## Tool map

| Intent | Tool(s) |
|--------|---------|
| List sprites | `list_sprites` |
| Create | `create_sprite` |
| Destroy | `destroy_sprite` (only with explicit delete/destroy/remove intent) |
| One-off command | `exec` |
| Write/read files | **No dedicated tool** — use `exec` with patterns in [files.md](references/files.md) |
| Exec sessions | `exec_list`, `exec_kill` |
| Services | `service_list`, `service_get`, `service_create`, `service_start`, `service_stop`, `service_logs` |
| Checkpoints | `checkpoint_create`, `checkpoint_list`, `checkpoint_get`, `checkpoint_restore` |
| Network policy | `policy_network_get`, `policy_network_update` |

Sprite-scoped tools need a `sprite` argument (usually the name). If unspecified, `list_sprites` and pick the obvious match; ask only when ambiguous.

**Filesystem:** Prefer `git clone` for real trees. For generated content, use the **base64 + space-free `python3 -c`** pattern in [files.md](references/files.md). Avoid heredocs and nested quotes through `exec` — they usually break.

## Naming and OAuth token prefix

The name prefix is a **per-connector OAuth setting**, not a fixed product rule for Grok.

Restricted tokens **require a non-empty prefix**. “No prefix” is not a restricted-token option — it is **Full access**, which can operate on every sprite in the organization.

| Consent choice | Create behavior |
|----------------|-----------------|
| Default restricted prefix | Usually **`mcp-`** — names like `mcp-my-task`; limited to that prefix |
| Custom restricted prefix | Whatever the user set (e.g. `grok-`, `agent-`); limited to that prefix |
| **Full access (no prefix)** | Bare names allowed; **unrestricted access to all sprites in the org** |

**Agent rules:**

1. **Session memory:** After a prefix error or successful create, remember the effective prefix (or “full access / none”).
2. **Agent-chosen names** (user did not specify): if unknown, prefer **`mcp-` + short slug** (matches the common restricted default). If the API requires another prefix, retry once. If the token is full access (no prefix rule), bare descriptive names are fine.
3. **User-chosen bare names** (e.g. “create odysseus”): try exact name first; on prefix error, **retry once** with `{prefix}{name}`; report the actual name and that it comes from their OAuth connector settings.
4. Never invent a second auth path to avoid the prefix. To get bare names / org-wide access, the user re-auths and chooses **Full access** on consent — warn that this is unrestricted org access, not merely “no naming rule.”

Details: [auth-and-setup.md](references/auth-and-setup.md).

## Common flows

### List sprites

1. `list_sprites`.
2. Empty → say none found for this org/token (success). Offer create if they wanted an environment.
3. Auth/tools failure → stop conditions.
4. Otherwise summarize name, status, URL — not raw JSON unless asked.
5. Note **cold** is normal until the first command wakes the sprite.

### Create a sprite for compute

1. MCP available (stop conditions if not).
2. `create_sprite` with a policy-compliant name (prefix rules above).
3. Report name, status, URL. Cold status is OK.
4. [compute.md](references/compute.md) for bootstrap if the user wants work done inside it.
5. Offer a baseline checkpoint after setup when useful.

### Smoke test

When the user wants to verify setup, follow [smoke-test.md](references/smoke-test.md): list → create → exec → ask before destroy.

### Run a command

1. Target sprite (list if needed).
2. `exec` with command (`dir` / `env` as needed).
3. Summarize exit status and important output.

### Write files on a sprite

There is no MCP `write_file`. Load [files.md](references/files.md) and:

1. Prefer `git clone` when a repo exists.
2. Otherwise encode content as base64 on the host, then `exec` a **space-free** `python3 -c …write_bytes(…b64decode(…))` on the sprite.
3. Verify with `cat` / `wc -c` before starting services.
4. Do **not** use heredocs or heavily quoted multi-line shell through `exec`.

### Long-running work

Use **services**, not a forever `exec`. See [services.md](references/services.md).

### Risky changes

`checkpoint_create` first. See [safety.md](references/safety.md).

## Grok vs sprite context

| Context | What it is |
|---------|------------|
| Grok local workspace | Repo and shell for this conversation |
| Sprites MCP | API to operate sprites |
| Sprite filesystem | Remote only via sprite-scoped tools |

Local terminal tools do not run inside the sprite.

## Safety

Treat sprite HTTP as potentially internet-accessible.

Never expose secrets, env dumps, arbitrary files, or unfiltered internals via HTTP.

**Destroy is irreversible.** Only with explicit delete/destroy/remove intent or clear approval.

Checkpoint before risky package installs, migrations, or broad refactors.

Network: `policy_network_get` before changes; update only when needed and explainable.

## Response format

**Operations:** what you did → result (ids, status, URL) → next step or done.

**Setup blocked:** failure class → recovery steps → you will retry after they finish (no CLI install).

**Prefix rewrite:** requested name → actual name → OAuth connector prefix setting (default is often `mcp-`).

Keep output concise.
