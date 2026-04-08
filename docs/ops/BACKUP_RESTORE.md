# Backup and Restore

## PostgreSQL Backup

```bash
pg_dump "$DATABASE_URL" > backup.sql
```

## Point-In-Time Recovery (PITR)

1. Enable WAL archiving in PostgreSQL.
2. Restore latest base backup.
3. Replay WAL up to target timestamp.

## Retention

- Keep daily backups for at least 30 days.
- Replicate backup artifacts to off-site/object storage.

## Ledger Backup

- Persist forensic ledger under durable path (`SESSION_LEDGER_DB_PATH`).
- Snapshot ledger file daily and retain with DB backups.

## Restore Drill

Run quarterly:

1. Restore DB in isolated environment.
2. Restore ledger snapshot.
3. Execute health checks and one synthetic job.
