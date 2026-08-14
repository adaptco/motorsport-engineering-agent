# Progress Tracking - Motorsport Engineering Agent

**Document Version:** 2.0 (Release Roadmap Baseline)
**Last Updated:** 2026-04-09
**Status:** ACTIVE EXECUTION (v3.8 production-readiness and release alignment in progress)
**Current Baseline:** `v3.8 / 0.3.8`
**Reference:** [PRD.md](./PRD.md), [docs/releases](./docs/releases)

---

## Executive Summary

This tracker is the canonical execution board for the additive migration path:

1. `v3.8` production-readiness, release metadata, and dependency alignment
2. `v3.8` runtime contracts, compose topology, and deployment verification
3. Preserve `v3.7` multi-agent orchestration and MCP gateway compatibility
4. Retain `v3.6` release records only as historical traceability

The release strategy is intentionally non-destructive. Legacy v3.5.2 operational surfaces remain compatibility-backed while newer slices are layered in behind versioned routes and additive migrations.

## Latest Execution Update (2026-04-09)

- Created branch `codex/v3.6.3-production-readiness` and added orchestration manager control-plane artifact (`skills/dmn-manager-orchestrator/SKILL.md`).
- Added phase checkpoint artifacts: `docs/checkpoints/PHASE_A.md`, `PHASE_B.md`, `PHASE_C.md`, `PHASE_D_TASK004.md`, `PHASE_D_TASK005.md`, `PHASE_E.md`, `PHASE_F.md`.
- Locked version surfaces to v3.6.3: `VERSION.json`, `pyproject.toml`, `README.md`, `CHANGELOG.md`, `.git-commit-sha`, and regenerated `uv.lock`.
- Closed Task-005 residual checklist items with evidence and onboarding timing artifact (`docs/checkpoints/ONBOARDING_SMOKE_TEST.md`).
- Closed Task-004 residual evidence items except the explicit commit gate (`Commit uv.lock to git` remains open until commit).
- Compacted namespace by collapsing `configs/` into `config/` and updating all references.
- Unified runtime contract pointers so `mcp.json` is authoritative and `mcp_v1_runtime_bundle/tool-registry.json` is single registry source for runtime docs/openapi/skills.
- Added PR lifecycle automation script `scripts/github_pr_lifecycle.sh` and embedded workflow in `skills/agent-ralph-wiggum/SKILL.md` plus `skills/github-pr-lifecycle/SKILL.md`.
- Closed the final Task-004 gate (`Commit uv.lock to git`) after commit-backed evidence and confirmed reconciliation reaches zero remaining actions.

- Added persistent reconciliation loop primitives in `worker/background_workers.py` for task findings, `TASK_LEDGER.md`, and MCP PRD acceptance criteria.
- Added/extended loop coverage in `tests/test_background_workers_state.py`.
- Created skill `skills/agent-ralph-wiggum/` to run checkpointed closeout loops.
- Resolved dependency lock workflow blocker by generating `uv.lock` and removing stale root `requirements.txt`.
- Added project lint/type configuration (`ruff`, `mypy`) in `pyproject.toml`.
- Added E2E ingest lifecycle integration coverage in `tests/integration/test_ingest_e2e_lifecycle.py`.
- Added runtime contract validation utility and tests (`shared/runtime_contracts.py`, `tests/test_runtime_contract_bundle.py`).
- Added MCP PRD evaluation artifact `mcp_v1_runtime_bundle/docs/prd-evaluation.json` for AC-08 closure tracking.
- Added missing contributor/API/ops docs (`CONTRIBUTING.md`, `docs/API.md`, `docs/ops/GENERAL_RUNBOOK.md`).
- Promoted Ralph loop from blocked reconciliation to active execution with prioritized closure actions persisted in `.mea_tmp/workflow_state/v3_6_closeout_ranked_actions.json`.
- Corrected Ralph closure process: reverted non-evidenced shortcut closures, enforced evidence-only checklist closure, and reduced validated remaining actions to `11`.
- Closed PR `#59` Gemini runtime review findings with concrete fixes in `control_plane/app.py` and `control_plane/services/aero_runner.py`, plus coverage updates in `tests/test_rate_limit_middleware.py` and `tests/test_aero_simulation_runner.py`.
- Re-ran full local suite after PR59 fixes: `83 passed, 1 skipped`.
- Re-ran Ralph reconciliation loop with current checklist/ledger/PRD state; persisted truthful blocked status with `19` remaining actions (no non-evidence closures).

---

## Four-Phase Timeline

| Phase | Release Theme | Outcome |
| --- | --- | --- |
| Phase 1 | v3.5.2 Stabilization | Stable, reproducible baseline with debt flush and compatibility lock |
| Phase 2 | v3.6 Runtime Contract Harness | Enforceable runtime contracts, event gates, resumable checkpoints, deployable container cut |
| Phase 3 | v3.7 Multi-Agent Orchestration | Orchestrator-owned handoffs, MCP v1 gateway, agent containers, HITL eval surfaces |
| Phase 4 | v3.8 Consolidation + Capability + Hardening | Platform consolidation, SKILL.md tool packaging, production SLO and reliability gates |

---

## Release-Phase Tracker

| Phase | Objective | Status | Gate | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| v3.5.2 | Lock baseline and eliminate known pre-v3.6 blockers | Historical | Baseline lock checklist complete | codex | [V3.5.2 stabilization record](./docs/releases/v3.5.2_STABILIZATION.md) |
| v3.6 | Runtime contract harness + containerization + compatibility gates | Superseded by V3.8 | Contract/event-order concepts retained in V3.8 | codex | [V3.6 runtime-contract record](./docs/releases/v3.6_RUNTIME_CONTRACT_PLAN.md) |
| v3.7 | Multi-agent runtime slices via six PRs (contracts -> deploy) | Planned | Orchestrator + MCP v1 + HITL exit criteria met | codex | [V3.7 implementation plan](./docs/releases/v3.7_IMPLEMENTATION_PLAN.md) |
| v3.8 | Platform consolidation, governed skills, and production hardening | Active | Release metadata, dependency, deployment, and compatibility checks pass | Agent | [V3.8 consolidation and hardening](./docs/releases/v3.8_PLATFORM_CONSOLIDATION_AND_HARDENING.md) |

---

## PRD Alignment Matrix (Task/Workstream -> Release + Slice)

| PRD Item | Target Release | PR Slice | Notes |
| --- | --- | --- | --- |
| v3.5.2 debt flush and baseline lock | v3.5.2 | Slice 0 | Stabilization before major structural work |
| Runtime contract bundle + validation harness | v3.6 | Slice 1 | Contracts-first additive cut |
| Runtime integration events/checkpoints | v3.6 | Slice 2 | Event order and resumability semantics |
| Containerization and compose cut | v3.6 | Slice 3 | Service image alignment and deployment reproducibility |
| Contract extraction from shared models | v3.7 | Slice 1 | Compatibility re-exports required |
| Orchestrator runtime service | v3.7 | Slice 2 | Run-first model with additive migrations |
| MCP gateway `/mcp/v1/*` | v3.7 | Slice 3 | Legacy aliases preserved |
| Agent containers and dispatch lanes | v3.7 | Slice 4 | Orchestrator owns all handoffs |
| HITL eval engine and verdict flow | v3.7 | Slice 5 | Evidence-backed approvals and rejects |
| Deploy/docs/version cut | v3.7 | Slice 6 | Release and runbook completion |
| Platform consolidation and capability packaging | v3.8 | Slice A | Structural simplification and contracts |
| Skill tooling expansion (`SKILL.md`) | v3.8 | Slice B | Capability growth through toolized skills |
| Production hardening and SLO readiness | v3.8 | Slice C | Mandatory release gate before close |

---

## Blocker Register by Release

### v3.5.2 Blockers

| ID | Blocker | Priority | Hard Gate | Unblock Action |
| --- | --- | --- | --- | --- |
| B352-01 | Lint/type safety baseline incomplete | P1 | Ruff + mypy policy committed | Add lint/type config and CI enforcement |
| B352-02 | E2E ingest scenario fragmentation | P2 | Consolidated integration path | Merge normalize->ingest->debrief coverage |
| B352-03 | Runtime/deploy doc drift risk | P1 | Baseline docs aligned to v3.5.2 | Sync PRD/progress/release docs |

### v3.6 Blockers

| ID | Blocker | Priority | Hard Gate | Unblock Action |
| --- | --- | --- | --- | --- |
| B36-01 | Runtime event contracts not enforced | P0 | Contract and event-order tests green | Add schema bundle + gate integration |
| B36-02 | Resume branch semantics not explicit | P0 | Checkpoint/resume contract validation | Add resumability tests and receipts |
| B36-03 | Container cut not reproducible | P1 | Compose and build config validate in CI | Ship deploy/compose + container docs |

### v3.7 Blockers

| ID | Blocker | Priority | Hard Gate | Unblock Action |
| --- | --- | --- | --- | --- |
| B37-01 | `shared/models.py` merge churn | P0 | Domain split with compatibility imports | Extract contracts into packages |
| B37-02 | CI-centric worker semantics | P0 | Orchestrator lanes isolated from CI jobs | Keep legacy worker; add orchestrator path |
| B37-03 | MCP scaffold behavior | P0 | `/mcp/v1/*` transport-backed | Implement gateway v1 and aliases |

### v3.8 Blockers

| ID | Blocker | Priority | Hard Gate | Unblock Action |
| --- | --- | --- | --- | --- |
| B38-01 | Platform sprawl across apps/services | P0 | Consolidated runtime boundaries approved | Merge service ownership and package contracts |
| B38-02 | Capability expansion without governance | P0 | Skill/tool contracts + policy checks | Add SKILL.md packaging and policy harness |
| B38-03 | Hardening debt after capability growth | P0 | SLO, rollback, incident gates pass | Run production readiness and chaos drills |

---

## Compatibility Commitments by Release

- `v3.5.2`: no breaking API changes; baseline lock only.
- `v3.6`: event and checkpoint contracts added with compatibility-safe integration.
- `v3.7`: `/mcp/v1/*` added while legacy routes remain available.
- `v3.8`: capability expansion through skills without breaking critical legacy endpoints.

Critical endpoints preserved during migration:

- `GET /healthz`
- `GET /healthz/dependencies`
- `GET /ingest/sources`
- `POST /ingest/normalize`
- `POST /runtime/logs/parse`
- `GET /runtime/sessions`
- `POST /agent/decision`
- `POST /verifier/execute`

---

## Verification and Planning Integrity Checks

1. Internal link and reference validation across `PROGRESS.md`, `PRD.md`, and `docs/releases/*`.
2. Version consistency checks for baseline and target releases.
3. Release gate checks: each phase must include entry criteria, exit criteria, and blockers.
4. Crosswalk checks: each active PRD workstream maps to one primary release phase and PR slice.

Runtime confidence suites retained in planning:

- baseline: `tests/test_backend_worker.py`, `tests/test_ci_workflow.py`, `tests/test_security_validation.py`
- v3.6 target: runtime contract + event-order suites
- v3.7 target: orchestrator lifecycle, handoff/checkpoint, MCP v1 compatibility, HITL verdict flow
- v3.8 target: platform integration, skill tooling contracts, reliability and regression gates
