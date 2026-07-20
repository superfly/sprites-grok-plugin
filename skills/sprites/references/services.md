# Sprites services

Use Sprites services for long-running processes such as web servers, workers, daemons, and preview apps. Prefer services over a forever-blocking `exec`.

## Service workflow

1. Inspect existing services (`service_list`) before adding a new one.
2. Prefer stable names based on role: `web`, `worker`, `preview`, `db`.
3. Create or update with `service_create` — set command, args, needs, and `http_port` intentionally.
4. Start with `service_start` (optional duration when you want a timed run).
5. Confirm with `service_get` and `service_logs`.
6. If a URL is needed, report the sprite URL and port, and whether access is expected to be authenticated or public.

## Debugging

- Read logs before changing code or restarting.
- Restart only the affected service (`service_stop` → `service_start`, or recreate if the definition changed).
- Include service name, port, URL/auth mode, and a short log summary in the final response.

## Safety

- Do not expose admin, env-dump, or unauthenticated file browsers.
- Confirm with the user before switching a service to a more public exposure model.
- Stop services you no longer need to avoid surprise public surfaces.
