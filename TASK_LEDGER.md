# Task Ledger (V3.8 Production Readiness)

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
| Rate limiting on high-cost POST routes | 🟢 Done | codex | `control_plane/app.py`, `tests/test_rate_limit_middleware.py`, `.env.example` | Added middleware guardrails for `/repos/fix-ci` and `/runtime/logs/parse`. |
| PR59 Gemini review closure (runtime hardening) | 🟢 Done | codex | `control_plane/app.py`, `control_plane/services/aero_runner.py`, `tests/test_rate_limit_middleware.py`, `tests/test_aero_simulation_runner.py` | Addressed timeout NameError risk, plain-text metrics, proxy-aware IP extraction (opt-in), and rate-limit bucket cleanup with passing tests. |
| Ingest module surface (V3.5) | 🟢 Done | main | `ingest/logs/*` | Already present at current baseline. |
| Ingest API wiring | 🟢 Done | main | `control_plane/routes/ingest.py`, `control_plane/app.py` | Already present at current baseline. |
| Runtime log endpoints | 🟢 Done | main | `control_plane/routes/runtime_logs.py` | Already present at current baseline. |
| Minimal GUI for runtime review | 🟢 Done | main | `frontend/hitl_runtime_logs.html` | Local operator scaffold present. |
| A2A handoff skill & persistence | 🟢 Done | codex | `skills/a2a_handoff/SKILL.md`, `contracts/a2a/` | Workflow state and handoff event schemas established. |
| Agent Ralph Wiggum loop skill | 🟢 Done | codex | `skills/agent-ralph-wiggum/SKILL.md`, `worker/background_workers.py`, `tests/test_background_workers_state.py` | Reconciliation loop now persists pending task/PRD gates across iterations. |
| Task-004 closure loop (dependency evidence refresh) | 🟢 Done | codex | `docs/checkpoints/PHASE_D_TASK004.md`, `docs/checkpoints/PHASE_H.md`, `uv.lock`, `TASK-004_DEPENDENCY_MANAGEMENT_FINDINGS.md` | All Task-004 checklist items closed with evidence-backed updates after commit-backed uv.lock gate closure. |
| Task-005 closure loop (documentation residuals) | 🟢 Done | codex | `docs/checkpoints/PHASE_D_TASK005.md`, `docs/checkpoints/ONBOARDING_SMOKE_TEST.md`, `TASK-005_DOCUMENTATION_AUDIT_FINDINGS.md` | Residual checklist fully closed with evidence-backed updates. |
| Phase E monorepo compaction | 🟢 Done | codex | `docs/checkpoints/PHASE_E.md`, `config/model_weights.yaml`, `tests/test_model_weights.py` | Collapsed `configs/` into `config/` and updated runtime/doc references. |
| Phase F runtime contract authority unification | 🟢 Done | codex | `docs/checkpoints/PHASE_F.md`, `SKILL.md`, `mcp_v1_runtime_bundle/Agents.md`, `mcp.json` | Runtime contract and tool discovery now pointer-aligned to single authority paths. |
| PR lifecycle automation normalization | 🟢 Done | codex | `scripts/github_pr_lifecycle.sh`, `skills/github-pr-lifecycle/SKILL.md`, `skills/agent-ralph-wiggum/SKILL.md` | Standardized label/comment process and embedded it into skill workflow. |

## V3.8 Release Alignment Roadmap

| Task | Status | Owner | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Migrate FastAPI hooks to Lifespan | 🟢 Done | codex | `control_plane/app.py` | Migrated `on_event` to `lifespan` context manager. |
| Version alignment across docs | 🟢 Done | codex | `README.md`, `VERSION.json` | Reconciled README and package version for v3.5.1. |
| Project-wide Linting Config | 🟢 Done | codex | `pyproject.toml` | Added Ruff + mypy config blocks and dev dependencies. |
| Dockerfile Standardization | 🟢 Done | codex | `Dockerfile` | Unified runtime base image standardized to `python:3.12-slim`. |
| Enforce strict Redis fallback | 🟢 Done | codex | `.env.example`, `control_plane/queue.py` | Production env defaults to `QUEUE_ALLOW_IN_MEMORY_FALLBACK=false`; queue logic honors strict fail-closed mode. |
| E2E Ingest integration suite | 🟢 Done | codex | `tests/integration/test_ingest_runtime_debrief_e2e.py` | Added normalize -> runtime parse -> debrief lifecycle integration test. |
| Dependency lock strategy | 🟢 Done | codex | `pyproject.toml`, `uv.lock`, `TASK-004_DEPENDENCY_MANAGEMENT_FINDINGS.md` | Stale `requirements.txt` removed; lockfile workflow now grounded on `uv lock` + `uv sync`. |
| Documentation closure package (deployment/API/contrib/runbook) | 🟢 Done | codex | `docs/deployment.md`, `docs/API.md`, `CONTRIBUTING.md`, `docs/ops/GENERAL_RUNBOOK.md` | Production-facing doc blockers closed with concrete guides. |
