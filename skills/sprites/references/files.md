# Writing and reading files on a sprite

There is **no** `write_file` / `read_file` / upload tool in the Sprites MCP. All filesystem work goes through **`exec`**. That works, but the shape of `exec` is easy to get wrong — use the patterns below.

## How `exec` behaves (why writes fail)

| Fact | Implication |
|------|-------------|
| `cmd` is a **single string** | You pass one string, not a real argv array from MCP JSON |
| The server treats it like **command + args** (space-split) | Nested quotes, spaces inside `python -c '…'`, and shell metacharacters often break |
| Heredocs (`cat <<EOF`) usually fail | Redirection and multi-line shell syntax get mangled |
| `stdin: true` exists | **No content body** is exposed in the MCP schema — do **not** rely on stdin for file content |
| Simple commands work well | `mkdir -p /path`, `cat /path`, `ls`, `uname -a`, `curl …` |

**Rule of thumb:** Prefer commands whose payload has **no spaces** in the fragile part, or avoid putting payload in the shell string at all (`git clone`).

## Preferred ways to get content onto a sprite

Pick the first option that fits:

| Priority | Method | When |
|----------|--------|------|
| 1 | **`git clone`** (or fetch) | Real projects, multi-file trees, user named a repo |
| 2 | **Base64 + space-free `python3 -c`** | Generated HTML/config/scripts, multi-line or special chars |
| 3 | **Tiny space-free write** | One-liners / tiny files with no spaces if possible |
| 4 | Ask the user | Private code, large trees, or secrets you should not invent |

Do **not** invent tokens or paste secrets into world-readable files.

## Reliable write pattern (base64)

Works for multi-line text, HTML, JSON, scripts — anything you can base64.

### Steps

1. Locally (Grok host shell), base64-encode the file contents.
2. On the sprite via `exec`, decode with a **space-free** Python one-liner.
3. Verify with `cat`, `wc -c`, or a checksum.

### Local encode (Grok machine)

```bash
python3 -c 'import base64, pathlib; print(base64.b64encode(pathlib.Path("index.html").read_bytes()).decode())'
# or from a string:
python3 -c 'import base64; print(base64.b64encode(b"<h1>hi</h1>").decode())'
```

### Sprite write via MCP `exec`

Use **no spaces** after `-c`. `python3 -c print(1+1)` works; `python3 -c "print(1 + 1)"` often does not.

```text
cmd: python3 -c __import__('pathlib').Path('/home/sprite/app/index.html').write_bytes(__import__('base64').b64decode('BASE64_HERE'))
```

Optional parent dir first (simple command — fine):

```text
cmd: mkdir -p /home/sprite/app
```

### Verify

```text
cmd: wc -c /home/sprite/app/index.html
cmd: cat /home/sprite/app/index.html
```

## Patterns that usually fail (avoid)

| Pattern | Why |
|---------|-----|
| `cat > file <<'EOF' … EOF` | Heredoc / multi-line shell breaks under `exec` |
| `python3 -c "… long code with spaces …"` | Spaces split the `-c` argument |
| Nested single/double quotes in one `cmd` | Quote stripping → `unexpected EOF` / syntax errors |
| `echo 'long html…' > file` with complex quoting | Same quoting / split issues |
| Relying on `stdin: true` for body content | MCP schema has no stdin payload field |
| Writing secrets into HTTP-served dirs | Safety — see [safety.md](safety.md) |

## Small edits after a file exists

For tiny, careful patches once a file is on disk:

- Prefer rewriting the whole file with the base64 pattern (most reliable).
- Or use short space-free transforms only if you are sure of the encoding.

Avoid open-ended `sed`/`awk` one-liners with complex regex through `exec` unless the command stays simple.

## Reading files

Reads are easy — use plain commands:

```text
cmd: cat /home/sprite/app/index.html
cmd: head -n 50 /home/sprite/app/main.py
cmd: ls -la /home/sprite/app
```

Large dumps: prefer `head` / `tail` / `wc` first so tool output stays usable.

## Multi-file apps

1. Prefer **`git clone`** of a branch or gist.
2. Or write a **tarball/zip as base64** (same Python decode), then `tar -xzf` / `unzip` with simple args.
3. Or write a few key files with the base64 pattern; do not loop dozens of fragile shell writes if clone is possible.

Example unpack after a base64 blob is written to `/tmp/tree.tar.gz`:

```text
cmd: tar -xzf /tmp/tree.tar.gz -C /home/sprite/app
```

## Checklist before you claim “deployed”

1. `mkdir -p` parent paths.
2. Write with base64 pattern (or clone).
3. `cat` or `wc -c` to confirm.
4. Start service / run command.
5. Health-check (`curl` on the sprite, or `service_get` / `service_logs`).

## Related

- Bootstrap and teardown: [compute.md](compute.md)
- Long-running servers: [services.md](services.md)
- Public exposure and secrets: [safety.md](safety.md)
