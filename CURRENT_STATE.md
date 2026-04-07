# Current State (April 5, 2026)

## Repository Baseline

- `origin/main` currently includes `c3b04ae`:
  - "Add A2A handoff skill, workflow-state contracts, and background state persistence"
- Local `mea_root_kernel.egg-info/*` drift is intentionally excluded from commit scope.

## Completed Capability Surface

### A2A handoff persistence

- Added skill, contracts, and background state worker:
  - `skills/a2a_handoff/SKILL.md`
  - `contracts/a2a/workflow_state.schema.json`
  - `contracts/a2a/handoff_event.schema.json`
  - `worker/background_workers.py`
- Ignore policy covers persisted state artifacts only:
  - `.gitignore` includes `.mea_tmp/workflow_state/` and `runtime_logs/workflow_state/`.

### V3.5 ingest and HITL review loop

- Ingest module scaffold and adapters present:
  - `ingest/logs/registry.py`, `normalizer.py`, `canonical.py`, `util.py`, `types.py`
  - adapters: `motec_ld.py`, `iracing_ibt.py`, `aim_xrk.py`, `vbox_vbo.py`, `pi_mat.py`, `csv_export.py`
- API endpoints present:
  - `GET /ingest/sources`
  - `POST /ingest/normalize`
  - `POST /runtime/logs/parse`
  - `GET /runtime/sessions`
  - `GET /runtime/sessions/{session_id}`
  - `GET /runtime/sessions/{session_id}/debrief`
- Minimal GUI scaffold present:
  - `frontend/hitl_runtime_logs.html`

### Hardening applied in this branch

- Forensic ledger path now defaults to persistent workspace state path when env not set:
  - `shared/runtime_paths.py`
  - consumed by `control_plane/repository.py` and `control_plane/routes/agent.py`
- Startup validation added for session ledger persistence:
  - `control_plane/app.py` (`validate_session_ledger_startup_config`)
- DB pooling layer and health visibility added:
  - `shared/db.py`
  - `GET /healthz/dependencies` in `control_plane/app.py`
- Circuit breakers added and wired:
  - `shared/circuit_breaker.py`
  - GitHub API path: `control_plane/github_app.py`
  - Redis queue path: `control_plane/queue.py`
  - MCP client guard utility: `control_plane/services/mcp_client.py`

## Validation Evidence

- Full test suite:
  - `python -m pytest -q` => `46 passed`
- Added tests:
  - `tests/test_forensic_ledger_persistence.py`
  - `tests/test_circuit_breaker.py`

## Truth Reconciliation Notes

- README exists (`README.md`) and is version-aligned.
- Ingest and runtime surfaces are implemented in repository (not just planned).
- Status should be tracked in `TASK_LEDGER.md` instead of ad-hoc narrative files.
