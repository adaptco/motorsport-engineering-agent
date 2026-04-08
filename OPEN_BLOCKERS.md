# Open Blockers (April 7, 2026 - V3.5.1 Baseline)

## P0/P1 - V3.6 Update Readiness

1. **Deprecated FastAPI Startup Hooks (RESOLVED)**
- Resolution: Migrated `on_event` hooks to `lifespan` context manager in `control_plane/app.py`.

2. **Absence of Unified Linting/Formatting**
- Impact: Codebase consistency and technical debt risk.
- Location: Project-wide; `pyproject.toml`.
- Next action: Integrate `ruff` and `mypy` configurations.

3. **Inconsistent Docker Infrastructure**
- Impact: Environment drift; outdated Python runtimes.
- Location: `Dockerfile`, `control_plane/Dockerfile`, `mcp_server/Dockerfile`, `worker/Dockerfile`.
- Next action: Standardize all images to `python:3.12-slim`.

4. **Permissive Redis Fallback Policy**
- Impact: Security/Integrity risk in production.
- Location: `control_plane/queue.py`.
- Next action: Enforce strict `QUEUE_ALLOW_IN_MEMORY_FALLBACK=false` for production environments.

## P2/P3 - Quality & Coverage

5. **Fragmented E2E Ingest Workflow**
- Impact: High-level scenario validation is split across unit/integration tests.
- Next action: Create a single integration test for the full `normalize -> ingest -> debrief` lifecycle.

6. **Dependency Lock Strategy (RESOLVED)**
- Resolution: Added `uv.lock` and removed stale root `requirements.txt` to enforce `pyproject.toml` + `uv` as the canonical dependency workflow.
