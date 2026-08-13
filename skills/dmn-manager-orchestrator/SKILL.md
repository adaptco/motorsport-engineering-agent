---
name: dmn-manager-orchestrator
description: Govern Motorsport Engineering Agent production-readiness execution using DMN gate policy, evidence-first Ralph reconciliation loops, and phase checkpoints. Use for multi-phase repo closure, task-ledger completion, and safe delegation control.
---

# DMN Manager Orchestrator

## Purpose
Coordinate phased repository closure and release hardening with explicit gates and checkpoint artifacts.

## Required Inputs
- `PRD.md`
- `PROGRESS.md`
- `TASK_LEDGER.md`
- `TASK-004_DEPENDENCY_MANAGEMENT_FINDINGS.md`
- `TASK-005_DOCUMENTATION_AUDIT_FINDINGS.md`
- `TASK-006_DATABASE_STATE_MANAGEMENT_FINDINGS.md`
- `TASK-007_OPERATIONAL_HARDENING_FINDINGS.md`
- `.github/dmn-manager-decisions.md`

## Worker Roles
- **Manager:** dmn-manager-orchestrator (gate owner)
- **Closure Worker:** `agent-ralph-wiggum` (reconcile -> persist -> re-check loops)
- **Infra Worker:** workflows/deploy/runtime hardening
- **Docs Worker:** PRD/progress/task ledger and docs alignment
- **Runtime Worker:** contract/schema/tool-registry and agent loop consistency

## Governance Rules
1. Treat `.github/dmn-manager-decisions.md` as top-level gate policy.
2. Do not close any task item without concrete file evidence.
3. Enforce phase checkpoints under `docs/checkpoints/PHASE_*.md`.
4. Prefer additive compatibility shims before destructive removals.
5. Allow destructive cleanup only after the phase gate explicitly approves it.
6. Always record residual risk and next gate in each checkpoint.

## Closure Loop
1. Reconcile open checklist items from task findings and `TASK_LEDGER.md`.
2. Implement fixes and generate evidence paths.
3. Update task finding checkboxes only where evidence exists.
4. Persist checkpoint with tests and unresolved blockers.
5. Re-run reconciliation until open count is zero or externally blocked.

## Phase Gate Exit Conditions
- **A:** Branch + orchestration artifacts created.
- **B:** Baseline drift report produced and accepted.
- **C:** Strict v3.6.3 semver/dependency/workflow baseline locked.
- **D:** TASK-004..007 evidence-closed or explicitly externally blocked.
- **E:** Namespace/duplicate compaction complete with runtime-safe references.
- **F:** `mcp.json` authoritative mapping aligned across runtime bundle artifacts.
- **G:** Full validation matrix passing; docs/ledger/progress synchronized.
- **H:** PR automation, review resolution, merge readiness report complete.
