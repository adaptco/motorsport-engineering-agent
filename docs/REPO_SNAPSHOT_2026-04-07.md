# MEA repository snapshot — 2026-04-07

## Source baseline
- Repository: `adaptco/motorsport-engineering-agent`
- Branch: `main`
- HEAD commit: `3a7d53a462d2ed446fd0171bcb67d07bad64a801`
- Commit title: `Fix .gitignore root anchor for nested clone path (#46)`

## Current shipped version
- `pyproject.toml`: package version `0.3.5`
- `VERSION.json`: kernel version `3.5`, package version `0.3.5`

## Current container shape
- Root `Dockerfile` is a generic single-container template still pointing at `mcp_tools.__init__:app`
- `docker-compose.yml` orchestrates `postgres`, `redis`, `control_plane`, `worker`, and `mcp_server`
- Service-local Dockerfiles exist for:
  - `control_plane/Dockerfile`
  - `worker/Dockerfile`
  - `mcp_server/Dockerfile`

## Verified complete from repo progress record
- A2A handoff skill + state persistence contracts
- V3.5 ingestion + runtime review surface
- Trust-surface and production-hardening updates
- Validation snapshot recorded as `python -m pytest -q => 46 passed` on 2026-04-05

## Gap against MEA V3.6 target
1. No first-class runtime event-gate schema bundle for plan/action/checkpoint/resume lifecycle.
2. No explicit V3.6 deployment container cut that unifies current service image assumptions.
3. Current `PRD.md` is still a codebase review document, not an implementation PRD for V3.6 runtime-contract integration.
4. Root `Dockerfile` is stale relative to the microservice deployment model.

## Proposed repo changes

### Add
- `contracts/runtime/agent_runtime_contract_bundle.schema.json`
- `contracts/runtime/README.md`
- `deploy/containers/mea-v3.6/Dockerfile`
- `deploy/compose/docker-compose.v3.6.yml`
- `docs/REPO_SNAPSHOT_2026-04-07.md`
- `tests/test_runtime_contract_bundle.py`
- `tests/test_runtime_event_order.py`

### Modify
- `PRD.md`
- `VERSION.json`
- `pyproject.toml`
- `control_plane/app.py`
- `control_plane/queue.py`
- `control_plane/services/mcp_client.py`
- `worker/backend_worker.py`
- `shared/db.py`
- `docker-compose.yml`
- `control_plane/Dockerfile`
- `worker/Dockerfile`
- `mcp_server/Dockerfile`

### Delete or deprecate
- `Dockerfile` (delete or mark legacy after V3.6 compose cut is adopted)
