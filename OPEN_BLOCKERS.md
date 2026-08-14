# Open Blockers (April 7, 2026 - V3.5.1 Baseline)

## P0/P1 - V3.8 Release Alignment Readiness

1. **Deprecated FastAPI Startup Hooks (RESOLVED)**
- Resolution: Migrated `on_event` hooks to `lifespan` context manager in `control_plane/app.py`.

2. **Unified Linting/Formatting (RESOLVED)**
- Resolution: Added repository-level `ruff` and `mypy` configuration blocks and dev dependencies in `pyproject.toml`.

3. **Inconsistent Docker Infrastructure**
- Impact: Environment drift; outdated Python runtimes.
- Location: `Dockerfile`, `control_plane/Dockerfile`, `mcp_server/Dockerfile`, `worker/Dockerfile`.
- Next action: Standardize all images to `python:3.12-slim`.

4. **Redis Fallback Policy (RESOLVED)**
- Resolution: Production (`APP_ENV=production`) now defaults queue fallback to fail-closed in `control_plane/queue.py`; `.env.example` preserves strict production default.

## P2/P3 - Quality & Coverage

5. **E2E Ingest Workflow (RESOLVED)**
- Resolution: Added `tests/integration/test_ingest_e2e_lifecycle.py` for normalize -> runtime parse -> debrief lifecycle coverage.

6. **Dependency Lock Strategy (RESOLVED)**
- Resolution: Added `uv.lock` and removed stale root `requirements.txt` to enforce `pyproject.toml` + `uv` as the canonical dependency workflow.
