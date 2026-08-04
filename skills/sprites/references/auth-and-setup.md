# Auth and setup

Sprites from this plugin go through the **hosted MCP server** only:

```text
https://sprites.dev/mcp
```

Grok authenticates that server with **browser OAuth**. The Sprites CLI is not required for plugin use and must not be installed as a workaround.

## 60-second first run (user)

1. Install and enable (prefer GitHub install, not a local checkout, for daily use):
   ```bash
   grok plugin install superfly/sprites-grok-plugin --trust
   grok plugin enable sprites
   ```
2. Reload plugins (`/plugins` → `r`) or restart Grok.
3. In Grok, say: **List my sprites.**
   Or run **`/sprites-status`** for a guided check.
4. Complete the browser OAuth prompt:
   - Fly.io account with Sprites access
   - Correct organization
   - Review **token restrictions** on the consent screen (see below)
5. Empty list = success. You are ready.

Optional: run **`/sprites-smoke`** for list → create → exec → (optional) destroy.

Optional CLI checks if tools never appear:

```bash
grok plugin list
grok mcp doctor sprites
```

| Doctor result | Meaning |
|---------------|---------|
| Server started, then OAuth / authorization required | Install is fine — finish browser auth (or `/mcps` → sprites → authenticate) |
| Folder untrusted | Trust the project (local install path) or reinstall from GitHub / `~/.grok/plugins` |
| Tools missing / plugin disabled | `grok plugin enable sprites`, reload |

You do **not** need the Sprites CLI, `sprite login`, or `grok mcp add`.

## Consent screen: name prefix and caps

During OAuth the user configures the connector token:

| Setting | Default (typical) | User may |
|---------|-------------------|----------|
| Name prefix (restricted) | **`mcp-`** | Change to another **non-empty** prefix (restricted tokens require one) |
| Create cap | Limited count | Raise/lower within restricted mode |
| Access mode | Restricted connector | **Full access** — no prefix, unrestricted org sprites |

### Access tradeoff (disclose clearly)

| Consent choice | Names | Security |
|----------------|-------|----------|
| Default restricted prefix | e.g. `mcp-my-task` | Safer for agents; only sprites under that prefix |
| Custom restricted prefix | e.g. `agent-my-task` | Same, under the custom prefix |
| **Full access (no prefix)** | Bare names allowed (`odysseus`, …) | **Unrestricted access to all sprites in the org** |

Restricted tokens **cannot** “clear” the prefix while staying restricted — the OAuth implementation requires a non-empty prefix for restricted tokens. Bare names mean **Full access**.

**For users:** Prefer a restricted prefix for agent connectors. Choose **Full access** only when you intentionally need org-wide control. Remember what you set: default names look like `mcp-my-task`.

**For the agent:**

- Do **not** assume the live prefix is always `mcp-` (defaults change per token).
- Prefer **try the name as requested**, then learn from API errors.
- When **choosing** a name with no user name and no session knowledge, prefer the product default prefix **`mcp-`** (e.g. `mcp-grok-tests`). If create fails with a different required prefix, retry once with that prefix. If create succeeds with no prefix rule (full access), bare descriptive names are fine afterward.
- Session memory: after any successful create or prefix error, remember the effective rule for later creates.
- Do **not** tell the user to “just disable the prefix” without mentioning that **Full access** unlocks every sprite in the org.

## How the agent should diagnose

Classify the failure before suggesting anything. Give short recovery steps. **Stop** after explaining — do not invent a second stack.

### A. Tools missing (MCP not loaded)

**Signals:** No Sprites tools in the integration tool list / `search_tool` finds none. Plugin may still show as installed.

**User recovery (in order):**

1. `grok plugin enable sprites` (install with `--trust` if needed)
2. Prefer user-scope install (GitHub) over `grok plugin install .` from a random project cwd
3. If doctor says folder untrusted: trust the project, or reinstall from a user path
4. Reload plugins or restart Grok
5. `grok mcp doctor sprites` — see table above
6. `grok inspect` — confirm MCP server `sprites` is listed

**Agent must not:** install the Sprites CLI, curl `api.sprites.dev`, register another MCP server, or run `npx mcp-remote`.

### B. Auth failed / not completed (MCP loaded, OAuth missing)

**Signals:** Tools exist; calls fail with unauthorized, 401, OAuth required, or login prompts. Doctor may say *server started* then *authorization required* — that is **progress**, not a broken install.

**User recovery:**

1. Complete the browser OAuth flow Grok shows
2. Or `/mcps` → **sprites** → authenticate (`i` where offered)
3. Pick the correct organization; note prefix/cap settings on consent
4. Retry the original request once

**Agent must not:** run `sprite login`, paste tokens into the shell, or open a second OAuth path from the terminal.

### C. Token / policy restricted (authenticated, action denied)

**Signals:** Create/mutate fails with a clear prefix or cap message, e.g. `sprite name must start with 'mcp-'` (or another prefix the user configured).

**Agent behavior (preferred — smooth for new users):**

1. Read the **required prefix from the error** (do not hardcode).
2. For a user-requested bare name (e.g. `odysseus`), **retry once** with `{prefix}{name}` when that mapping is unambiguous.
3. Report the **actual name created**, and that it matches the connector’s OAuth prefix setting.
4. Remember the prefix for later creates in this session.
5. If the user insisted on the exact bare name only, explain they can re-auth and choose **Full access** on the consent screen (unrestricted org access — not a restricted empty prefix) — do not loop.

**User recovery if caps or broader access are needed:**

1. Stay under the create cap, or destroy unused sprites
2. Re-authenticate and adjust cap, or choose **Full access** if they intentionally need unrestricted org-wide sprite access

**Agent must not:** invent tokens or ask the user to paste API keys into the shell.

### D. Wrong org or sprite not found

**Signals:** `list_sprites` works but the expected sprite is missing.

**User recovery:**

1. Confirm OAuth org
2. Prefix policy may hide out-of-prefix sprites — list and use exact names
3. Use names returned by `list_sprites`, never guess

### E. Empty list (not a failure)

`list_sprites` returning zero sprites is a **successful** auth path. Offer to create one if the user wanted an environment.

## Name prefix playbook (agent)

1. **Session memory:** After any prefix error or successful create, keep the effective prefix (or “full access / none”) for the session.
2. **Agent-chosen names (no user name):** If prefix unknown, use default-style names under **`mcp-`**. If the API requires a different prefix, retry once. If unrestricted (**Full access**, no prefix), descriptive bare names are OK.
3. **User-chosen bare names:** Try as requested; on prefix error, retry with `{prefix}{name}` and explain. Do not suggest “disable prefix” without stating that **Full access** is unrestricted org-wide access.
4. **Hints from list:** Shared prefixes on existing sprites are clues only — trust explicit API errors over guesses.

## Forbidden agent workarounds

| Forbidden | Why |
|-----------|-----|
| Install the Sprites CLI | Plugin path is MCP |
| `sprite login` / `sprite org auth` as OAuth substitute | Different credential surface |
| Raw `curl` to `api.sprites.dev` | Bypasses MCP; secret risk |
| Second MCP via `grok mcp add` / `npx mcp-remote` | Hides load/trust issues |
| Inventing tokens / env vars | Not the plugin auth model |

## Optional: user already uses the Sprites CLI

Independent of this plugin. Agent still uses MCP for Grok-driven work. Never install or re-auth the CLI just to finish a plugin task.

## Success criteria

1. Plugin `sprites` enabled
2. MCP `sprites` can start (doctor: not folder-blocked)
3. At least one Sprites tool call works after OAuth (empty list is OK)
4. Creates respect the connector’s OAuth name-prefix setting when one is set
