# Task Ledger (V3.5.1 Patched Baseline)

| Task | Status | Owner | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Reconcile repo truth vs docs | 🟢 Done | codex | `PROGRESS.md`, `CURRENT_STATE.md` | Replaced stale review-era progress with current grounded status. |
| Publish open blockers | 🟢 Done | codex | `OPEN_BLOCKERS.md` | Blockers are explicit and action-oriented. |
| Establish execution ledger | 🟢 Done | codex | `TASK_LEDGER.md` | Canonical tracking table established. |
| Forensic ledger persistence path and startup validation | 🟢 Done | codex | `shared/runtime_paths.py`, `control_plane/app.py` | Default path moved to workspace state dir; startup validates DB path. |
| Deployment documentation | 🟢 Done | codex | `docs/deployment.md` | Includes bootstrap, health checks, and rollout flow. |
| Runtime runbook | 🟢 Done | codex | `docs/runbook.md` | Includes failure handling and recovery procedures. |
| Environment reference | 🟢 Done | codex | `docs/env.md`, `.env.example` | Env wiring documented with defaults and production notes. |
| DB connection pooling | 🟢 Done | codex | `shared/db.py`, `GET /healthz/dependencies` | Pool settings + fallback + health stats endpoint. |
| Circuit breakers: GitHub API | 🟢 Done | codex | `control_plane/github_app.py`, `shared/circuit_breaker.py` | Bounded retries and breaker open-state protection. |
| Circuit breakers: Redis queue path | 🟢 Done | codex | `control_plane/queue.py`, `shared/circuit_breaker.py` | Explicit fail-closed mode via env toggle. |
| Circuit breakers: MCP call path | 🟢 Done | codex | `control_plane/services/mcp_client.py`, `shared/circuit_breaker.py` | Guarded client utility added for tool-call transport. |
| Ingest module surface (V3.5) | 🟢 Done | main | `ingest/logs/*` | Already present at current baseline. |
| Ingest API wiring | 🟢 Done | main | `control_plane/routes/ingest.py`, `control_plane/app.py` | Already present at current baseline. |
| Runtime log endpoints | 🟢 Done | main | `control_plane/routes/runtime_logs.py` | Already present at current baseline. |
| Minimal GUI for runtime review | 🟢 Done | main | `frontend/hitl_runtime_logs.html` | Local operator scaffold present. |
| A2A handoff skill & persistence | 🟢 Done | codex | `skills/a2a_handoff/SKILL.md`, `contracts/a2a/` | Workflow state and handoff event schemas established. |
| Agent Ralph Wiggum loop skill | 🟢 Done | codex | `skills/agent-ralph-wiggum/SKILL.md`, `worker/background_workers.py`, `tests/test_background_workers_state.py` | Reconciliation loop now persists pending task/PRD gates across iterations. |

## V3.6 Preparation Roadmap

| Task | Status | Owner | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Migrate FastAPI hooks to Lifespan | 🟢 Done | codex | `control_plane/app.py` | Migrated `on_event` to `lifespan` context manager. |
| Version alignment across docs | 🟢 Done | codex | `README.md`, `VERSION.json` | Reconciled README and package version for v3.5.1. |
| Project-wide Linting Config | ⚪ Open | — | `pyproject.toml` | P1: Add `ruff` and `mypy` configurations for technical debt reduction. |
| Dockerfile Standardization | ⚪ Open | — | `Dockerfile`, `control_plane/Dockerfile` | P1: Standardize all images to `python:3.12-slim`. |
| Enforce strict Redis fallback | ⚪ Open | — | `control_plane/queue.py` | P1: Set `QUEUE_ALLOW_IN_MEMORY_FALLBACK=false` for production environments. |
| E2E Ingest integration suite | ⚪ Open | — | `tests/integration/` | P2: Consolidate fragmented tests into single end-to-end scenario. |
| Dependency lock strategy | 🟢 Done | codex | `pyproject.toml`, `uv.lock`, `TASK-004_DEPENDENCY_MANAGEMENT_FINDINGS.md` | Stale `requirements.txt` removed; lockfile workflow now grounded on `uv lock` + `uv sync`. |
