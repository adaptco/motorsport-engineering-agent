# PRD - MEA Release Delivery Framework (v3.5.2 -> v3.8)

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
