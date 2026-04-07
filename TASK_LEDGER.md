# Task Ledger

| Task | Status | Owner | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Reconcile repo truth vs docs | Done | codex | `PROGRESS.md`, `CURRENT_STATE.md` | Replaced stale review-era progress with current grounded status. |
| Publish open blockers | Done | codex | `OPEN_BLOCKERS.md` | Blockers are explicit and action-oriented. |
| Establish execution ledger | Done | codex | `TASK_LEDGER.md` | Canonical tracking table established. |
| Forensic ledger persistence path and startup validation | Done | codex | `shared/runtime_paths.py`, `control_plane/app.py`, `tests/test_forensic_ledger_persistence.py` | Default path moved to workspace state dir; startup validates DB path. |
| Deployment documentation | Done | codex | `docs/deployment.md` | Includes bootstrap, health checks, and rollout flow. |
| Runtime runbook | Done | codex | `docs/runbook.md` | Includes failure handling and recovery procedures. |
| Environment reference | Done | codex | `docs/env.md`, `.env.example` | Env wiring documented with defaults and production notes. |
| DB connection pooling | Done | codex | `shared/db.py`, `GET /healthz/dependencies` | Pool settings + fallback + health stats endpoint. |
| Circuit breakers: GitHub API | Done | codex | `control_plane/github_app.py`, `shared/circuit_breaker.py` | Bounded retries and breaker open-state protection. |
| Circuit breakers: Redis queue path | Done | codex | `control_plane/queue.py`, `shared/circuit_breaker.py` | Explicit fail-closed mode via env toggle. |
| Circuit breakers: MCP call path | Done | codex | `control_plane/services/mcp_client.py`, `shared/circuit_breaker.py` | Guarded client utility added for tool-call transport. |
| Ingest module surface (V3.5) | Done | main | `ingest/logs/*` | Already present at current baseline. |
| Ingest API wiring | Done | main | `control_plane/routes/ingest.py`, `control_plane/app.py` | Already present at current baseline. |
| Runtime log endpoints | Done | main | `control_plane/routes/runtime_logs.py` | Already present at current baseline. |
| Minimal GUI for runtime review | Done | main | `frontend/hitl_runtime_logs.html` | Local operator scaffold present. |
| E2E normalize->ingest->debrief single-flow test | Open | codex | `OPEN_BLOCKERS.md` item 4 | Coverage exists but still fragmented across multiple tests. |
| Dependency lock strategy and CI enforcement | Open | codex | `OPEN_BLOCKERS.md` item 6 | Pending explicit lock policy. |
