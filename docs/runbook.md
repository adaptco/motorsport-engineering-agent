# Operations Runbook

## 1. Control Plane Not Starting

Checks:

1. Verify env vars are loaded (`DATABASE_URL`, `SESSION_LEDGER_DB_PATH`, `GITHUB_WEBHOOK_SECRET`).
2. Confirm ledger path is writable.
3. Run:
   - `python -c "from control_plane.app import validate_session_ledger_startup_config; print('ok')"`
4. Start app and inspect logs for startup validation exceptions.

## 2. GitHub Token Issuance Failing

Symptoms:

- Worker fails at token issuance.
- Errors include circuit-open or GitHub API failures.

Actions:

1. Validate GitHub app env credentials.
2. Confirm system clock skew is reasonable (JWT iat/exp).
3. Retry after circuit breaker recovery window if open.
4. Inspect:
   - `control_plane/github_app.py`
   - breaker settings in `.env`.

## 3. Queue Stalls or Job Enqueue Errors

Symptoms:

- Jobs not dequeued.
- Runtime errors mention Redis unavailable.

Actions:

1. Check Redis reachability with `redis-cli ping`.
2. Verify `REDIS_URL` and queue env settings.
3. Confirm whether `QUEUE_ALLOW_IN_MEMORY_FALLBACK` is intentionally disabled.
4. If strict mode is enabled and Redis is down, restore Redis before retrying.

## 4. Session Ledger Integrity Issues

Actions:

1. Verify configured ledger DB path from `/healthz/dependencies`.
2. Run chain verification:
   - `python -c "from shared.forensic_ledger import verify_chain; print(verify_chain('PATH','SESSION'))"`
3. If chain fails, isolate affected session and preserve DB artifact for forensic review.

## 5. Ingest Normalization Failures

Actions:

1. Check adapter availability:
   - `GET /ingest/sources`
2. Retry with explicit `vendor_hint`.
3. Confirm output directory is writable.
4. Use fixture-based tests as known-good references:
   - `tests/fixtures/sample_export.csv`
   - `tests/fixtures/sample.vbo`

## 6. MCP Tool Call Failures

Actions:

1. Verify MCP base URL and bearer token.
2. Check MCP server health (`/healthz` and `/providers`).
3. Review `control_plane/services/mcp_client.py` retries and circuit breaker settings.

## 7. Standard Recovery Procedure

1. Stabilize external dependencies (Postgres, Redis, GitHub API reachability).
2. Restart control plane, MCP server, worker in that order.
3. Re-run health checks and one synthetic job.
4. Record incident + remediation in `docs/ops/`.
