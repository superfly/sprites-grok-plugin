# Sprites safety

## Confirm before these actions

- Destroying a sprite (`destroy_sprite`) — irreversible.
- Restoring a checkpoint (`checkpoint_restore`) — discards filesystem state after that checkpoint.
- Deleting checkpoints (when available).
- Widening outbound network policy (`policy_network_update`).
- Making a service public or exposing a new HTTP surface that may be internet-reachable.
- Broad destructive filesystem commands inside a sprite (`rm -rf` of large trees, disk wipes).

## Checkpoint guidance

Create a checkpoint before:

- Package upgrades or lockfile churn
- Database migrations
- Bulk file moves, deletes, or generated rewrites
- Service command changes
- Network policy changes
- Experiments with untrusted or agent-generated code

Use comments that include the reason, for example `before-node-upgrade` or `before-db-migration`.

## Recovery

Before restoring, explain that restore rewinds filesystem state and discards work after the checkpoint. Prefer listing newer checkpoints or relevant paths first when the user may still need them.

## Secrets and exposure

- Prefer environment variables injected into `exec` / services over writing secrets into the repo tree.
- Do not create debug endpoints that dump env, tokens, or arbitrary files.
- Treat sprite URLs as potentially public; authenticate or restrict by default when the product supports it.
- Restricted OAuth tokens (non-empty name prefix + create caps) are safer for agent connectors — stay within the prefix unless the user intentionally chooses **Full access** (no prefix, unrestricted access to all sprites in the org).
