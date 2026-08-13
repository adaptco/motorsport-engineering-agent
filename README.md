# MEA Root Kernel v3.8

MEA Multi-Agent Runtime Template

## Quick Start

1. Install dependencies with a reproducible lockfile workflow:
   - `uv sync --extra dev`
   - alternative: `pip install -e .[dev]`
2. Copy `.env.example` to `.env` and set local credentials.
3. Start control plane:
   - `uv run uvicorn control_plane.app:app --reload`
4. Start MCP server:
   - `uv run uvicorn mcp_server.app:app --port 7000 --reload`
5. Start worker:
   - `uv run python -m worker.backend_worker`

## Operational Docs

- Deployment: `docs/deployment.md`
- API guide: `docs/API.md`
- General runbook: `docs/runbook.md`
- Contributing: `CONTRIBUTING.md`
- Dependencies: `DEPENDENCIES.md`
- License notices: `LICENSES/THIRD_PARTY_NOTICES.md`

This template refactors a monolithic MEA-style control plane into a production multi-container runtime:

- `apps/control-plane`: north-south API, session lifecycle, job submission
- `apps/mcp-gateway`: tool mediation, provider routing, A2A/MCP boundary
- `apps/hitl-console`: operator review for telemetry replay, evals, and receipts
- `services/orchestrator`: task routing, agent loop, checkpoints, handoffs
- `services/agent-runtime-*`: specialized agent containers
- `services/telemetry-ingest`: normalize vendor/native logs into canonical frames
- `services/memory`: state store + vector retrieval abstraction
- `services/eval-engine`: automated evals + HITL verdict capture
- `services/ledger`: append-only receipts, replay, audit
- `platform/*`: queue, db, cache, observability, policy bundles

## Current -> Target map

| Current path | Target service | Why |
|---|---|---|
| `control_plane/*` | `apps/control-plane`, `services/orchestrator` | split ingress from orchestration |
| `mcp_server/*` | `apps/mcp-gateway` | make MCP/tool routing a dedicated network boundary |
| `worker/backend_worker.py` | `services/orchestrator` + `services/agent-runtime-*` | separate generic orchestration from specialized agent execution |
| `ingest/*` | `services/telemetry-ingest` | isolate telemetry normalization + sampling |
| `frontend/hitl_runtime_logs.html` | `apps/hitl-console` | promote GUI into full HITL review surface |
| `worker/background_workers.py` | `services/orchestrator/state` | move workflow checkpoints/handoffs into governed runtime state |
| `shared/models.py` | `contracts/*` + `packages/sdk-models` | make contracts reusable across services |

## Minimum production containers

1. control-plane
2. mcp-gateway
3. orchestrator
4. telemetry-ingest
5. memory
6. eval-engine
7. ledger
8. agent-supervisor
9. agent-telemetry-analyst
10. agent-replay-analyst
11. hitl-console
12. postgres / redis / object-store / tracing backend

## Agent loop in this template

receive task -> load checkpoint -> retrieve memory -> plan -> invoke model -> call tools through MCP -> evaluate -> persist receipt -> handoff or return result

## Primitive index

See `PRIMITIVES.md`.

## MCP Contract Stub

- `mcp.json` declares the planner, researcher, coder, reviewer, and tester contract with capabilities, scopes, resource URIs, and lease envelopes.
- `mcp_api.py` exposes `/mcp/info`, `/mcp/agents`, and `/mcp/invoke` as a contract-first FastAPI stub.
- The production MCP server remains `mcp_server/app.py`; this stub is a lightweight companion for declarative orchestration experiments.
