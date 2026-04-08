# Deployment Guide

## Scope

This guide covers deployment of the MEA control plane, MCP server, and worker with persistent session-ledger state and guarded external dependency behavior.

## Prerequisites

- Python 3.11+
- PostgreSQL reachable by `DATABASE_URL`
- Redis reachable by `REDIS_URL`
- GitHub App credentials:
  - `GITHUB_APP_ID`
  - `GITHUB_APP_INSTALLATION_ID`
  - `GITHUB_APP_PRIVATE_KEY`
  - `GITHUB_WEBHOOK_SECRET`
- Optional LLM/MCP credentials:
  - `MCP_SHARED_BEARER_TOKEN`
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENROUTER_API_KEY`

## Environment Bootstrap

1. Copy `.env.example` to `.env`.
2. Set production-grade values for all required env vars.
3. Ensure `SESSION_LEDGER_DB_PATH` points to durable storage.
4. Set `QUEUE_ALLOW_IN_MEMORY_FALLBACK=false` in production.
5. If pooling is desired, ensure `psycopg_pool` is installed and `DB_POOL_ENABLED=true`.

## Service Startup

1. Start Postgres and Redis.
2. Run DB migrations from `db/migrations/`.
3. Start control plane:
   - `uvicorn control_plane.app:app --host 0.0.0.0 --port 8000`
4. Start MCP server:
   - `uvicorn mcp_server.app:app --host 0.0.0.0 --port 7000`
5. Start worker:
   - `python -m worker.backend_worker`

## Health and Readiness

- Control plane:
  - `GET /healthz`
  - `GET /healthz/dependencies`
- MCP server:
  - `GET /healthz`
  - `GET /providers`

Readiness checks should fail rollout if:

- DB pool health is not healthy when pooling is expected.
- Session ledger path is invalid/unwritable.
- Redis is unavailable and in-memory fallback is disabled.

## Webhook Setup

1. Configure GitHub webhook to `POST /github/webhook`.
2. Use `application/json`.
3. Set webhook secret to match `GITHUB_WEBHOOK_SECRET`.
4. Validate with an actual webhook delivery and verify persistence in `webhook_events`.

## Rollback Strategy

1. Roll back app images/binaries to prior known-good version.
2. Keep persistent ledger DB file in place (do not delete).
3. Re-run health checks:
   - `/healthz`
   - `/healthz/dependencies`
4. Confirm queue drains normally and worker can fetch GitHub installation token.

## Scaling Guidance

- Horizontal scale control plane behind gateway/load balancer.
- Scale worker replicas based on queue depth and DB pool limits.
- Tune `DB_POOL_MAX_SIZE` and Redis capacity together to avoid head-of-line blocking.

## SSL/TLS

- Terminate TLS at ingress/gateway (recommended).
- Enforce HTTPS between browser and gateway for production.

## Monitoring

- Track `/healthz` and `/healthz/dependencies`.
- Collect service logs centrally.
- Track queue depth, job throughput, and error-rate alerts.
