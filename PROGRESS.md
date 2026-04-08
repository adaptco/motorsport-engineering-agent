# Progress Tracking - Motorsport Engineering Agent

**Document Version:** 2.0 (Release Roadmap Baseline)
**Last Updated:** 2026-04-08
**Status:** ACTIVE ROADMAP (v3.5.2 -> v3.8)
**Current Baseline:** `v3.5.2 / 0.3.5.2`
**Reference:** [PRD.md](./PRD.md), [docs/releases](./docs/releases)

---

## Executive Summary

This tracker is the canonical execution board for the additive migration path:

1. `v3.5.2` stabilization and baseline lock
2. `v3.6` runtime contract harness and container cut
3. `v3.7` multi-agent orchestration and MCP gateway v1
4. `v3.8` platform consolidation + skill tooling + production hardening

The release strategy is intentionally non-destructive. Legacy v3.5.2 operational surfaces remain compatibility-backed while newer slices are layered in behind versioned routes and additive migrations.

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
| v3.5.2 | Lock baseline and eliminate known pre-v3.6 blockers | In Progress | Baseline lock checklist complete | codex | [docs/releases/v3.5.2_STABILIZATION.md](./docs/releases/v3.5.2_STABILIZATION.md) |
| v3.6 | Runtime contract harness + containerization + compatibility gates | Planned | Contract/event-order tests green | codex | [docs/releases/v3.6_RUNTIME_CONTRACT_PLAN.md](./docs/releases/v3.6_RUNTIME_CONTRACT_PLAN.md) |
| v3.7 | Multi-agent runtime slices via six PRs (contracts -> deploy) | Planned | Orchestrator + MCP v1 + HITL exit criteria met | codex | [docs/releases/v3.7_IMPLEMENTATION_PLAN.md](./docs/releases/v3.7_IMPLEMENTATION_PLAN.md) |
| v3.8 | Consolidate platform, add capability via skills, harden to production SLOs | Planned | Reliability and rollback readiness gates pass | codex | [docs/releases/v3.8_PLATFORM_CONSOLIDATION_AND_HARDENING.md](./docs/releases/v3.8_PLATFORM_CONSOLIDATION_AND_HARDENING.md) |

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
