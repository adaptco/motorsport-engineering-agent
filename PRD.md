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

## Current Baseline

- Repository: `adaptco/motorsport-engineering-agent`
- Baseline release: `v3.5.2`
- Kernel/package baseline: `3.5.2 / 0.3.5.2`
- Strategy: additive migration with compatibility windows; no destructive rewrite path

---

## Feature Intent A: Aerodynamic Simulation Lane + Durable Digital Twin

### Overview

Add a dedicated aerodynamic simulation lane after the control-plane boundary. This lane owns vehicle intake, design branching, and solver orchestration while remaining separate from telemetry truth surfaces.

### Goals

1. Add a dedicated aero simulation contract and API boundary.
2. Persist durable simulation state independently of telemetry sessions.
3. Link telemetry references as inputs without collapsing ownership boundaries.
4. Track CL/CD branch hypotheses with audited state transitions.

### Non-Goals

- Running OpenFOAM in control-plane request paths.
- Reusing race-session ledger records as authoritative aero state.
- Folding simulation runs directly into telemetry replay.

### Primary Workstreams

- Service contract and API boundaries
- Durable aero state schema
- Simulation loop separation and validation

---

## Feature Intent B: v3.6 Runtime Contract Harness + Container Cut

### Overview

Promote runtime contracts into enforceable event gates and ship a reproducible deployment cut aligned with deterministic lane ownership.

### Goals

1. Add first-class runtime schema bundle under `contracts/runtime/`.
2. Bind orchestration/runtime/tool surfaces to schema + policy + budget gates.
3. Ship reproducible container/compose cut.
4. Keep migration compatibility-safe against v3.5.2 operational surfaces.

### Non-Goals

- Single-PR rewrite of all feature surfaces.
- Replacing existing telemetry domain semantics.
- Breaking critical legacy endpoints during migration.

### Primary Workstreams

- Runtime contract bundle
- Runtime integration and event-order guarantees
- Containerization and deployment topology
- Versioning/documentation alignment
- Verification suites for contract validity and event order

---

## Feature Intent C: v3.7 Multi-Agent Runtime Slice

### Overview

Deliver the first production-grade multi-agent orchestration slice on top of the stabilized v3.5.2 baseline, preserving legacy compatibility routes while introducing orchestrator-owned handoffs and MCP v1 gateway surfaces.

### Goals

1. Deterministic orchestrator as sole owner of agent-to-agent routing.
2. MCP upgrade to transport-backed `/mcp/v1/*` with aliases.
3. Durable workflow + handoff + checkpoint state plane.
4. Contract extraction from overloaded shared model surfaces.
5. HITL eval/verdict surface tied to evidence packets.

### Non-Goals

- Replacing CI-fix worker loop in this release.
- Forcing all telemetry logic into cloud-only topology.
- Making LLM output authoritative over deterministic telemetry truth.

### Primary Workstreams

- Contract extraction and versioning
- Orchestrator runtime service
- MCP gateway v1
- Agent containers
- HITL eval surface
- Deploy/version packaging

---

## Release Sequencing (Authoritative Crosswalk)

### Dependency Order (PR Slice Sequence)

1. contracts
2. orchestrator
3. MCP gateway
4. agents
5. eval/HITL
6. deploy/versioning

This order is mandatory for v3.7 and informs v3.6/v3.8 planning dependencies.

### Release-by-Release Execution

| Release | Primary Objective | PR Slice Mapping | Compatibility Requirement |
| --- | --- | --- | --- |
| v3.5.2 | Stabilize and lock baseline | Slice 0 (stabilization) | No breaking API changes |
| v3.6 | Runtime contract harness + container cut | Slices 1-3 (contracts, runtime integration, containerization) | Preserve critical legacy endpoints |
| v3.7 | Multi-agent orchestrator and MCP v1 | Slices 1-6 listed above | Keep aliases for legacy MCP routes |
| v3.8 | Consolidation + capability + hardening | Slices A-C (consolidate, skills/tooling, hardening gate) | Preserve compatibility windows while tightening reliability |

### Workstream/Task to Release Mapping

| Item | Target Release | Primary Slice | Notes |
| --- | --- | --- | --- |
| Baseline debt flush and doc/version lock | v3.5.2 | Slice 0 | Required before major structural rollout |
| Runtime event schemas and gate contracts | v3.6 | Slice 1 | Contract-first integration |
| Runtime event integration/checkpoint resume | v3.6 | Slice 2 | Deterministic event ordering |
| Container cut and compose alignment | v3.6 | Slice 3 | Reproducible deployment |
| Shared model split into contract packages | v3.7 | Slice 1 | Compatibility re-exports required |
| Orchestrator run lifecycle + handoffs | v3.7 | Slice 2 | Run-first additive DB model |
| MCP `/mcp/v1/*` gateway and aliases | v3.7 | Slice 3 | Backward-compatible routing |
| Agent services + dispatch lanes | v3.7 | Slice 4 | Orchestrator-owned coordination |
| HITL eval and verdict routes/console | v3.7 | Slice 5 | Evidence-backed operator decisions |
| Deploy manifests + release docs/version | v3.7 | Slice 6 | Final release closure |
| Platform consolidation and boundary simplification | v3.8 | Slice A | Reduce ownership ambiguity |
| Capability expansion via `SKILL.md` tooling | v3.8 | Slice B | Governed tool packaging |
| Production hardening/SLO/rollback gates | v3.8 | Slice C | Mandatory before v3.8 close |

---

## Public API, Interface, and Type Commitments by Release

### v3.5.2
- No breaking route or schema changes.
- Baseline stabilization only.

### v3.6
- Introduce runtime contract/event interfaces and resumable checkpoint contracts.
- Enforce deterministic event-order semantics.

### v3.7
- Add versioned MCP routes:
  - `POST /mcp/v1/tools/call`
  - `POST /mcp/v1/providers/invoke`
  - `POST /mcp/v1/a2a/invoke`
  - `GET /mcp/v1/tools`
  - `GET /mcp/v1/providers`
  - `GET /mcp/v1/healthz`
- Preserve compatibility aliases for legacy MCP surfaces.

### v3.8
- Expand capabilities via toolized skills (`SKILL.md` patterns) with contract governance.
- Maintain compatibility guarantees while tightening production reliability requirements.

Critical endpoints preserved across migration windows:

- `GET /healthz`
- `GET /healthz/dependencies`
- `GET /ingest/sources`
- `POST /ingest/normalize`
- `POST /runtime/logs/parse`
- `GET /runtime/sessions`
- `POST /agent/decision`
- `POST /verifier/execute`

---

## Verification and Exit Conditions

### Planning Integrity Checks

1. Internal links valid across `PROGRESS.md`, `PRD.md`, and `docs/releases/*`.
2. Version references consistent with `v3.5.2` baseline and planned progression.
3. Every release phase includes entry criteria, exit criteria, blockers, and PR slices.

### Runtime Confidence References

- Baseline suites retained:
  - `tests/test_backend_worker.py`
  - `tests/test_ci_workflow.py`
  - `tests/test_security_validation.py`
- v3.6 target suites:
  - runtime contract validity
  - runtime event order
- v3.7 target suites:
  - orchestrator run lifecycle
  - handoff/checkpoint persistence
  - MCP v1 compatibility
  - HITL verdict flow
- v3.8 target suites:
  - platform integration
  - skill tooling contract validation
  - reliability/regression and rollback drills

### Exit Condition for This PRD

This PRD is complete when release sequencing, crosswalk mappings, compatibility commitments, and verification gates are decision-complete for `v3.5.2 -> v3.8`.

---

## Historical Context (Deprecated Review-Era Tasks)

The legacy review task list (`Task-001` through `Task-012`) is retained as historical analysis context only. It is not the active release execution framework.

Active execution sources are:

- `PROGRESS.md` (release tracker)
- `docs/releases/*` (phase plans and audits)
- this PRD release sequencing chapter
