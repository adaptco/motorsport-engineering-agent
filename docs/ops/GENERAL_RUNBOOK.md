# General Operations Runbook

Primary runbook content is maintained in [../runbook.md](../runbook.md).

## Quick Links

- Service lifecycle and recovery: [../runbook.md](../runbook.md)
- Deployment procedures: [../deployment.md](../deployment.md)
- API troubleshooting endpoints: [../API.md](../API.md)
- Backup and restore: [BACKUP_RESTORE.md](BACKUP_RESTORE.md)

## Standard Incident Flow

1. Check `/healthz` and `/healthz/dependencies`.
2. Validate external dependencies (Postgres, Redis, GitHub API).
3. Restart services in order: control plane -> MCP server -> worker.
4. Verify queue drains and runtime sessions remain readable.
