# Sprites for Grok Build

Use [**Sprites**](https://sprites.dev) from [Grok Build](https://x.ai/cli): isolated, checkpointable Linux environments for agent compute (builds, tests, sandboxes, long-running services).

This repo **is** the plugin. It wires Grok to the hosted MCP server at `https://sprites.dev/mcp` (OAuth) and ships skills for safe workflows. **No Sprites CLI required.**

The plugin marks its hosted MCP requests as Grok-driven using coarse,
privacy-safe [`client-signals`](https://github.com/superfly/client-signals)
headers. Nothing user-, machine-, or repo-specific is sent. The attribution is
advisory analytics only — client signals are self-reported, so they are never
used for authentication, authorization, per-request gating, or enforcement.

## Quick start

```bash
grok plugin install superfly/sprites-grok-plugin --trust
grok plugin enable sprites
```

Reload plugins (`/plugins` → `r`) or restart Grok, then:

| Step | What to do |
|------|------------|
| 1 | Say **List my sprites.** (or run **`/sprites-status`**) |
| 2 | Complete **browser OAuth** (Fly.io → organization) |
| 3 | On the consent screen, review token settings — name prefix **defaults to `mcp-`** (restricted). **Full access** allows bare names but grants unrestricted access to every sprite in the org |
| 4 | Empty list = **success** — you are authenticated |

Optional full check: **`/sprites-smoke`** (list → create → exec → ask before destroy).

Try next:

> Create a sprite for a quick experiment and run `uname -a` in it.

If create fails with a prefix rule, Grok should retry with `{prefix}your-name` and tell you the real name (e.g. `mcp-experiment` when using the default).

### Optional health checks

```bash
grok plugin list
grok mcp doctor sprites
```

| Result | Meaning |
|--------|---------|
| Started, then OAuth / authorization required | Install OK — finish browser auth (`/mcps` → sprites → authenticate) |
| Folder untrusted | Trust the project, or install from GitHub instead of a local path |
| Plugin disabled / no tools | Enable plugin, reload |

## Slash commands

| Command | Purpose |
|---------|---------|
| `/sprites-status` | Is MCP loaded and authenticated? Lists sprites; does not create/destroy |
| `/sprites-smoke` | End-to-end: list → create → exec → optional destroy |

## What you can do

- List, create, and destroy sprites (destroy only when you ask)
- Run commands and tests inside a sprite
- Manage services (dev servers, workers), checkpoints, network policy
- Keep risky work off your laptop

## Install notes

**Recommended:** GitHub install (above). Fewer folder-trust issues than a local path.

**Local development** of this plugin:

```bash
grok plugin install . --trust
grok plugin enable sprites
```

Local installs may require **trusting the project folder** before MCP starts. If tools never appear, check `grok inspect` for `Project trusted`, or symlink/install via `~/.grok/plugins`.

Always use `--trust` on install so the plugin’s MCP can run.

The canonical marketplace listing is maintained in
[`xai-org/plugin-marketplace`](https://github.com/xai-org/plugin-marketplace).
This repository intentionally contains only the plugin itself. Direct GitHub
installation remains available for development and testing.

## Authentication (one screen)

| Piece | Role |
|-------|------|
| Plugin | Points Grok at `https://sprites.dev/mcp` |
| Browser OAuth | Your Fly.io user + org; Grok stores connector tokens |
| Name prefix | Set on consent for **restricted** tokens; **default `mcp-`**. A non-empty prefix is required for restricted access |
| Create cap | Restricted tokens may limit how many sprites this connector can create |
| Full access | Unrestricted token — bare names allowed; **can use every sprite in the org** |

You do **not** need `sprite login` or a manual `grok mcp add` for normal use.

### Name prefix and access

Restricted MCP tokens **must** have a non-empty name prefix. Bare names are not a separate “clear the prefix” toggle — they come with **Full access**.

| Consent choice | Example names | Access |
|----------------|---------------|--------|
| Default restricted prefix | `mcp-my-task`, `mcp-api-debug` | Only sprites under that prefix (safer for agents) |
| Custom restricted prefix (e.g. `agent-`) | `agent-my-task` | Only sprites under that prefix |
| **Full access (no prefix)** | `my-task`, `odysseus` | Bare names allowed; **unrestricted access to all sprites in the org** |

Prefer a restricted prefix for day-to-day agent use. Choose **Full access** only when you intentionally need org-wide sprite control.

To change prefix or access level later: re-authenticate the Sprites MCP connector (`/mcps` → sprites) and adjust the consent screen.

## Example prompts

- "List my sprites."
- "Create a sprite and run the test suite for this repo there."
- "On my experiment sprite, create a checkpoint, then install dependencies and re-run the failing test."
- "Start the web service in my sprite and give me the URL."
- "Destroy the sprite we created for this experiment."
- "/sprites-status"
- "/sprites-smoke"

## How it works

Grok stays on your machine. Sprites MCP is the control plane for remote environments:

- Local workspace ≠ sprite filesystem
- Remote commands → `exec` / services tools
- **No dedicated file upload/write tool** — agents use `exec` (prefer `git clone` or base64 + space-free `python3 -c`; see skill `files.md`)
- Long-running processes → services (not a forever exec)
- Snapshots → checkpoints
- Egress → network policy

If MCP is missing or unauthenticated, Grok should **explain recovery** (skill `auth-and-setup`) rather than installing the CLI.

## Client attribution

`.grok-plugin/mcp.json` sets two static headers on every request to
`https://sprites.dev/mcp`:

| Header | Value | Why |
|---|---|---|
| `Fly-Client-Agent` | `grok` | The canonical agent tag from [`spec/markers.json`](https://github.com/superfly/client-signals/blob/main/spec/markers.json). Any other spelling classifies as `other`. |
| `Fly-Client-Interactive` | `false` | Required. See below. |

**Don't remove `Fly-Client-Interactive`, and don't "correct" it to `true`.**
Both are easy mistakes to make, and both are silent:

- It is the *instrumentation sentinel*. Per
  [`spec/request-metrics.md`](https://github.com/superfly/client-signals/blob/main/spec/request-metrics.md),
  a request missing this header — or carrying an unparseable value — classifies
  as `{"operator": "uninstrumented", "agent": "none"}`, and `Fly-Client-Agent`
  is discarded along with it. Dropping this header zeroes out all attribution.
- `false` is correct despite Grok Build being human-driven. `Interactive` means
  "stdout looks attached to a terminal," not "a human is present." These
  requests originate from Grok's MCP client, where no terminal is attached. A
  static manifest cannot observe per-session terminal state, so it sends a
  constant rather than a measurement. The value is also inert for reporting:
  operator precedence is `ci > agent > interactive`, so a present
  `Fly-Client-Agent` yields `operator="agent"` either way.

`Fly-Client-Parent` and `Fly-Client-CI` are deliberately omitted — the spec
states that `Parent` must not affect classification, and false-valued `CI` is
omitted rather than sent.

The headers live **only** in `.grok-plugin/mcp.json`, the manifest
`plugin.json` ships. The root `.mcp.json` is the generic project-scoped config
that Grok, Claude Code, and Cursor all read, so it deliberately carries no
attribution — otherwise any non-Grok client used in a checkout of this repo
would report itself as Grok.

To confirm attribution is arriving, check `fly_client_signals_requests_total`
server-side: `operator="agent", agent="grok"` means the headers landed;
`operator="uninstrumented", agent="none"` means the client stripped them.

## Safety

- Treat sprite URLs as potentially public.
- Do not expose secrets, env dumps, or arbitrary files over HTTP.
- Destroy is permanent (state, services, checkpoints, URL).

## Troubleshooting

### Tools missing

| Check | Action |
|-------|--------|
| Not installed / not enabled | `grok plugin install … --trust` and `grok plugin enable sprites` |
| Local path + untrusted project | Trust project, or reinstall from GitHub |
| Stale session | Reload plugins or restart Grok |
| Doctor | `grok mcp doctor sprites` |

### Auth incomplete

| Check | Action |
|-------|--------|
| Never finished OAuth | Complete browser flow, or `/mcps` → sprites → authenticate |
| Wrong org | Re-auth and pick the org that owns your sprites |
| Doctor: authorization required after start | Normal until OAuth completes |

### Prefix or policy

| Check | Action |
|-------|--------|
| `name must start with '…'` | Use that prefix (agent should auto-retry once), or re-auth and pick a different restricted prefix |
| Create cap | Destroy unused sprites or re-auth with a higher cap |
| Need bare names / org-wide access | Re-auth and choose **Full access** (unrestricted — every sprite in the org) |
| Sprite not in list | Other org, or outside this token’s prefix visibility |

### Runtime (MCP already works)

| Symptom | Try |
|---------|-----|
| Network errors inside sprite | Inspect network policy before changing it |
| Service URL not reachable | Services, logs, HTTP port |
| Cold sprite | Normal; first command wakes it |

### Do not

- Install the Sprites CLI only because MCP failed
- Add a duplicate MCP with `npx mcp-remote` while this plugin is installed
- Paste API tokens into the shell to bypass OAuth

## Repository layout

```
.grok-plugin/plugin.json       Manifest (v0.2.0)
.grok-plugin/mcp.json          Hosted MCP URL + client attribution (shipped)
.mcp.json                      Project-scoped config for working in this repo;
                               no attribution headers — see Client attribution
skills/sprites/                Main skill + references
skills/sprites-status/         /sprites-status
skills/sprites-smoke/          /sprites-smoke
assets/sprites-logo.svg
README.md
LICENSE
```

## Related

- https://sprites.dev
- https://docs.sprites.dev
- https://docs.sprites.dev/integrations/remote-mcp/
- MCP registry: [`dev.sprites/mcp`](https://registry.modelcontextprotocol.io/v0/servers?search=dev.sprites/mcp) · [superfly/sprites-mcp](https://github.com/superfly/sprites-mcp)

## License

[MIT](./LICENSE) © Fly.io, Inc.
