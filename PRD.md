# Feature: Aerodynamic Simulation Lane + Durable Digital Twin

## Overview
Add a separate aerodynamic simulation lane that runs in its own service layer after the control-plane API boundary. This lane owns vehicle intake, CAD candidate selection, OpenFOAM case generation, solver execution hooks, and CL/CD branch evaluation. It is intentionally distinct from the racing telemetry loop, which continues to own on-track evidence, replay, and session analysis.

## Stack Placement
- UI: collect vehicle metadata, images, telemetry references, and design prompts.
- Control plane: validate requests and expose aero simulation APIs.
- Aero simulation service: manage durable simulation state, geometry branches, solver configuration, and branch evaluation.
- Telemetry loop: keep race-session ingest and replay separate from simulation state.
- OBS / ledger: record provenance, hashes, and branch history for every simulation update.

## Goals
1. Scaffold a dedicated aero simulation contract and API boundary.
2. Persist a durable state model that can be resumed independently from telemetry sessions.
3. Keep the aero loop isolated from the racing telemetry loop while still allowing telemetry references to be linked as inputs.
4. Provide a clean branch model for design prompts that can track predicted CL / CD changes.

## Non-Goals
- Running OpenFOAM inside the control-plane request path.
- Reusing race-session ledger records as the durable aero state.
- Folding simulation runs into the telemetry replay pipeline.
- Automatically approving geometry changes without review.

## Workstreams

### Workstream 1 — Service Contract and API Boundaries
**Add**
- `contracts/aero/README.md`
- `control_plane/routes/aero.py`
- `control_plane/services/aero_state_store.py`
- `services/aero-simulation/README.md`
- `services/aero-simulation/Dockerfile`

**Modify**
- `control_plane/app.py`
- `shared/models.py`
- `shared/runtime_paths.py`

**Acceptance Criteria**
- `POST /aero/runs` creates a new simulation run from a vehicle snapshot and source references.
- `GET /aero/runs` lists durable aero runs.
- `GET /aero/runs/{run_id}` returns the current durable simulation state.
- `POST /aero/runs/{run_id}/branches` appends a design branch proposal to the run.
- API models are separate from telemetry session models.

### Workstream 2 — Durable Aero State
**Add**
- `contracts/aero/aero_simulation_state.schema.json`

**Acceptance Criteria**
- The state schema stores simulation-only data: vehicle identity, geometry state, solver state, metrics, provenance, calibration, and branch history.
- The durable state includes `state_hash` and `prev_state_hash` so updates can be resumed and audited.
- Telemetry references may be linked into the aero state, but telemetry session state is not embedded as the source of truth.
- The state file can be validated independently of the racing telemetry loop.

### Workstream 3 — Simulation Loop Separation
**Add**
- `tests/test_aero_simulation_state.py`

**Acceptance Criteria**
- The aero simulation state can be created, fetched, and branch-updated without touching telemetry session storage.
- Schema validation rejects malformed state payloads.
- The control plane route layer and the aero state layer remain logically separate from the telemetry ingest/replay loop.

# Feature: MEA V3.6 Runtime Contract Harness + Deployment Container Cut

## Overview
Upgrade Motorsport Engineering Agent from the current V3.5 baseline to **MEA V3.6** by promoting runtime contracts into first-class event gates, aligning the control-plane / runtime / tool surfaces to the approved swimlane model, and shipping a reproducible containerized deployment cut.

The current repository baseline is still versioned as package `0.3.5` and kernel `3.5`, while the existing `PRD.md` is scoped to a codebase review rather than implementation delivery. V3.6 replaces that with an execution PRD focused on contract-driven runtime control, resumable checkpoints, explicit policy gates, and deployment artifacts.

## Current Repo Snapshot
- Repository: `adaptco/motorsport-engineering-agent`
- Baseline branch: `main`
- Baseline commit: `3a7d53a462d2ed446fd0171bcb67d07bad64a801`
- Current package version: `0.3.5`
- Current kernel version: `3.5`

## Problem Statement
The repository already contains A2A handoff contracts, ingestion surfaces, and trust-surface hardening, but it lacks a runtime-wide event contract harness for:
- `request.received`
- `run.created`
- `workflow.policy.screened`
- `plan.proposed`
- `plan.repaired`
- `plan.failed`
- `step.dispatched`
- `approval.resolved`
- `tool.requested`
- `tool.executed`
- `action.proposed`
- `action.repaired`
- `action.invalid`
- `state.transitioned`
- `checkpoint.persisted`
- `blocked`
- `resume.requested`
- `run.completed`
- `run.failed`
- `audit.bundle.written`

V3.6 must make those contracts enforceable at runtime, not advisory documentation.

## Goals
1. Add a first-class JSON schema bundle for runtime events and state-transition gates.
2. Bind the orchestration loop to schema validation, policy screening, checkpoint persistence, and resumable execution.
3. Add a V3.6 container cut aligned to the deployment sequence:
   browser → gateway → control plane → worker pool → data plane
4. Replace the review-only PRD with a delivery PRD that enumerates concrete repo changes.
5. Version bump the repo from `0.3.5` / kernel `3.5` to `0.3.6` / kernel `3.6`.

## Non-Goals
- Rewriting all existing feature surfaces in one PR.
- Changing domain telemetry semantics.
- Replacing A2A contracts already verified in `PROGRESS.md`.
- Converting the whole stack to a single-process runtime.

## Success Criteria
- [ ] Runtime contract bundle added under `contracts/runtime/`
- [ ] Per-step runtime events validated through schema + policy + budget gates
- [ ] `tool.requested` requires `idempotency_key`
- [ ] `state.transitioned` emitted after each approved runtime step
- [ ] `checkpoint.persisted` emitted for each safe resume point
- [ ] Resume token contract added for blocked/retry branches
- [ ] MEA V3.6 compose file and container Dockerfile added
- [ ] Root Dockerfile deprecation decision recorded
- [ ] Tests added for event bundle validity and event order
- [ ] `PRD.md`, `VERSION.json`, and `pyproject.toml` updated to V3.6

## Architecture Alignment
The implementation must preserve the lane ownership model:

- **UI**: ingress, auth boundary, API/session control
- **ORCH**: workflow governor
- **GOV**: policy, safety, schema, secret scope
- **CTX**: memory, retrieval, checkpoints
- **LLM**: planning and bounded synthesis
- **RT**: deterministic execution loop
- **MCP**: controlled tool/action surface
- **EXT**: systems of record
- **HITL**: explicit approval lane
- **OBS**: receipts, logs, traceability

## Workstreams

### Workstream 1 — Runtime Contract Bundle
**Add**
- `contracts/runtime/agent_runtime_contract_bundle.schema.json`
- `contracts/runtime/README.md`

**Acceptance Criteria**
- Bundle validates all event families above.
- Shared envelope includes:
  - `event_type`
  - `schema_version`
  - `event_id`
  - `run_id`
  - `task_id`
  - `step_id`
  - `created_at`
  - `lane`
  - `fsm_state`
  - `prev_hash`
  - `state_hash`
  - `policy_version`
  - `payload`
- `plan.repaired` and `action.repaired` carry `repair_metadata`.
- `tool.requested` carries `idempotency_key`.

### Workstream 2 — Runtime Integration
**Modify**
- `control_plane/app.py`
- `control_plane/queue.py`
- `control_plane/services/mcp_client.py`
- `worker/backend_worker.py`
- `shared/db.py`

**Acceptance Criteria**
- Orchestrator emits `run.created`, `workflow.policy.screened`, `step.dispatched`, `run.completed`, `run.failed`.
- Runtime emits `state.transitioned`, `blocked`.
- Context/checkpoint surface emits `checkpoint.persisted`.
- MCP/tool surface emits `tool.requested`, `tool.executed`.
- Invalid plan/action branches emit `plan.failed` / `action.invalid`.
- Resume branch emits `resume.requested`.

### Workstream 3 — Containerization
**Add**
- `deploy/containers/mea-v3.6/Dockerfile`
- `deploy/compose/docker-compose.v3.6.yml`

**Modify**
- `docker-compose.yml`
- `control_plane/Dockerfile`
- `worker/Dockerfile`
- `mcp_server/Dockerfile`

**Delete or Deprecate**
- root `Dockerfile` after V3.6 service image adoption

**Acceptance Criteria**
- Compose topology maps cleanly to:
  - Browser / operator
  - Gateway
  - Control plane
  - Worker pool
  - Data plane
- Control plane, worker, and MCP services run from a common V3.6 base image or explicitly version-matched service images.
- Existing Postgres and Redis dependencies remain intact.

### Workstream 4 — Versioning + Documentation
**Modify**
- `PRD.md`
- `VERSION.json`
- `pyproject.toml`

**Add**
- `docs/REPO_SNAPSHOT_2026-04-07.md`

**Acceptance Criteria**
- `PRD.md` becomes this implementation document.
- `VERSION.json` updates kernel version to `3.6`.
- `pyproject.toml` updates package version to `0.3.6`.
- Snapshot doc records the exact baseline commit and current deployment shape.

### Workstream 5 — Verification
**Add**
- `tests/test_runtime_contract_bundle.py`
- `tests/test_runtime_event_order.py`

**Acceptance Criteria**
- Schema bundle validates representative samples for:
  - valid plan path
  - repaired plan path
  - invalid action path
  - blocked/retry path
  - completed run path
- Event order test enforces:
  `request.received → run.created → workflow.policy.screened → plan.* → step.dispatched → tool.* / approval.resolved → action.* → state.transitioned → checkpoint.persisted → run.completed|run.failed`

## File Plan

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

### Delete / Deprecate
- `Dockerfile` (legacy single-container entrypoint; delete or explicitly mark legacy)

## Verification Commands
```bash
python -m pytest -q
python -m pytest tests/test_runtime_contract_bundle.py -q
python -m pytest tests/test_runtime_event_order.py -q
docker compose -f deploy/compose/docker-compose.v3.6.yml config
docker build -f deploy/containers/mea-v3.6/Dockerfile -t mea:v3.6 .
```

## Exit Condition
V3.6 is complete when the runtime contracts are enforceable, the per-step execution loop is resumable and receipted, the container cut is reproducible, and the repo version and PRD reflect the new delivery baseline.


# Feature: Comprehensive Codebase Review for Motorsport Engineering Agent

## Overview
Conduct a thorough review of the motorsports-engineering-agent (MEA) codebase to understand its architecture, components, purpose, and functionality. The review will analyze how the system integrates AI decision-making with motorsport telemetry data, particularly from iRacing simulator, and document findings for better understanding and potential improvements.

## Success Criteria
- [ ] All review tasks completed
- [ ] Architecture diagram created
- [ ] Component roles documented
- [ ] Data flow mapped
- [ ] Key features identified
- [ ] Technology stack documented
- [ ] Findings summarized in review report

## Tasks

### Task-001: Analyze Project Structure and Configuration

**Priority**: High
**Estimated Iterations**: 1-2

**Acceptance Criteria**:

- [ ] Project dependencies and versions documented (from pyproject.toml)
- [ ] Docker configuration reviewed (Dockerfile, compose files)
- [ ] Database schema understood (migrations/)
- [ ] Configuration files analyzed (configs/, VERSION.json)
- [ ] Build and deployment scripts reviewed (Makefile, scripts/)

**Verification**:

```bash
# Check if project builds successfully
make build
# Verify Docker images can be built
docker build -t mea-test .
```

### Task-002: Review Control Plane Architecture

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] Main FastAPI application structure documented (control_plane/app.py)
- [ ] API routes analyzed (agent, replay, session, verifier, github)
- [ ] Job management system understood (queue.py, repository.py)
- [ ] Webhook integrations reviewed (github_app.py, webhooks.py)
- [ ] Health check endpoints verified

**Verification**:

```bash
# Test control plane health endpoint
curl http://localhost:8000/healthz
# Verify API routes are accessible
python -c "from control_plane.app import app; print('Routes loaded successfully')"
```

### Task-003: Examine MCP Server Implementation

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] MCP server purpose and role documented
- [ ] Supported LLM providers identified (OpenAI, Anthropic, Google, OpenRouter)
- [ ] Tool implementations reviewed (mea_ci_guardrail)
- [ ] Authentication mechanisms understood
- [ ] A2A invoke functionality analyzed

**Verification**:

```bash
# Check MCP server health
curl http://localhost:8001/healthz
# Verify providers endpoint
curl http://localhost:8001/providers
```

### Task-004: Analyze Worker Backend Processing

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] Worker loop logic documented (backend_worker.py)
- [ ] Job processing pipeline understood
- [ ] GitHub integration reviewed (github_app_client.py)
- [ ] Patch validation mechanisms analyzed
- [ ] Error handling and logging reviewed

**Verification**:

```bash
# Test worker can import without errors
python -c "from worker.backend_worker import worker_loop; print('Worker imports successfully')"
# Verify GitHub client functionality (requires token)
python -c "from worker.github_app_client import get_installation_token; print('GitHub client available')"
```

### Task-005: Review Telemetry Ingestion System

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] iRacing integration documented (iracing_stream.py)
- [ ] Telemetry data models understood (shared/models.py)
- [ ] Data streaming mechanisms analyzed
- [ ] Channel mapping and sampling reviewed
- [ ] Error handling for simulator unavailability

**Verification**:

```bash
# Test telemetry models can be imported
python -c "from shared.models import TelemetryFrame, ReplayMetrics; print('Models import successfully')"
# Verify iRacing stream adapter (without live simulator)
python -c "from ingest.iracing_stream import load_pyirsdk; print('iRacing adapter available')"
```

### Task-006: Examine AI Agent and Reasoning Components

**Priority**: High
**Estimated Iterations**: 3-4

**Acceptance Criteria**:

- [ ] Agent decision API reviewed (routes/agent.py)
- [ ] Reasoning engine analyzed (mea/reasoning/)
- [ ] Policy engine functionality understood
- [ ] Time domain handling reviewed
- [ ] Supervisor loop documented

**Verification**:

```bash
# Test agent routes import
python -c "from control_plane.routes.agent import router; print('Agent routes available')"
# Verify reasoning components
python -c "from mea.reasoning.policy_engine import PolicyEngine; print('Policy engine available')"
```

### Task-007: Analyze Data Persistence and Storage

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] Database models reviewed (shared/models.py)
- [ ] Migration scripts analyzed (db/migrations/)
- [ ] Forensic ledger functionality understood
- [ ] Session receipts and evidence packets reviewed
- [ ] Data validation mechanisms examined

**Verification**:

```bash
# Test database connection (requires running DB)
python -c "from shared.db import get_db; print('DB module available')"
# Verify forensic ledger
python -c "from shared.forensic_ledger import ForensicLedger; print('Ledger available')"
```

### Task-008: Review Testing and Quality Assurance

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] Test structure analyzed (tests/ directory)
- [ ] Unit and integration tests reviewed
- [ ] Test coverage assessed
- [ ] CI/CD guardrails examined (mea_ci_guardrail.py)
- [ ] Validation utilities understood (jsonl_validator.py)

**Verification**:

```bash
# Run test suite
pytest --collect-only
# Check test coverage
pytest --cov=shared --cov-report=term-missing
```

### Task-009: Document Data Flow and Architecture

**Priority**: High
**Estimated Iterations**: 3-4

**Acceptance Criteria**:

- [ ] End-to-end data flow mapped (telemetry → processing → decisions)
- [ ] Component interaction diagram created
- [ ] API communication patterns documented
- [ ] Job lifecycle traced
- [ ] External integrations mapped (GitHub, iRacing, LLM providers)

**Verification**:

```bash
# Verify all components can be imported together
python -c "
from control_plane.app import app
from mcp_server.app import app as mcp_app
from worker.backend_worker import worker_loop
from ingest.iracing_stream import stream_iracing_frames
print('All main components import successfully')
"
```

### Task-010: Identify Key Features and Capabilities

**Priority**: Medium
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] Core features documented (CI fixing, replay analysis, session management)
- [ ] AI decision-making capabilities listed
- [ ] Telemetry processing features identified
- [ ] GitHub integration features reviewed
- [ ] Performance metrics and monitoring understood

**Verification**:

```bash
# Review metrics configuration
cat metrics/performance_tasks.yaml
# Check release manifest
cat release/RELEASE_MANIFEST.json
```

### Task-011: Assess Technology Stack and Dependencies

**Priority**: Low
**Estimated Iterations**: 1-2

**Acceptance Criteria**:

- [ ] Python version and key libraries documented
- [ ] Infrastructure dependencies identified (Redis, PostgreSQL)
- [ ] External API integrations listed
- [ ] Development tools and frameworks reviewed

**Verification**:

```bash
# Check Python version compatibility
python --version
# Verify key dependencies
python -c "import fastapi, uvicorn, pydantic, psycopg, redis; print('Core dependencies available')"
```

### Task-012: Create Comprehensive Review Report

**Priority**: High
**Estimated Iterations**: 2-3

**Acceptance Criteria**:

- [ ] Executive summary of system purpose
- [ ] Architecture overview with diagrams
- [ ] Component descriptions and responsibilities
- [ ] Key workflows documented
- [ ] Technology assessment
- [ ] Recommendations for improvements
- [ ] Security considerations noted

**Verification**:

```bash
# Create review report file
echo "# MEA Codebase Review Report" > REVIEW_REPORT.md
echo "Report created successfully"
```

## Technical Constraints

- Language: Python 3.11+
- Framework: FastAPI for web services
- Database: PostgreSQL with psycopg
- Cache: Redis
- External APIs: GitHub API, iRacing SDK, LLM providers
- Testing: pytest with coverage
- Containerization: Docker

## Architecture Notes

- Microservices architecture with separate control plane, MCP server, and worker
- Event-driven job processing with queue system
- AI agent integration for decision making in motorsport context
- Forensic ledger for audit trails and evidence collection
- GitHub App integration for CI/CD automation

## Out of Scope

- Detailed performance benchmarking
- Security vulnerability assessment
- Production deployment configuration
- User interface components (if any)
- Third-party LLM provider implementations
