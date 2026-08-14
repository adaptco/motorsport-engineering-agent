---
name: dmn-manager-orchestrator
description: Govern production-readiness execution using DMN gate policy, evidence-first reconciliation loops, and phase checkpoints.
contract_version: "1.0"
policy_scope: execute
source_of_truth:
  - PRD.md
  - PROGRESS.md
  - TASK_LEDGER.md
---

# DMN Manager Orchestrator

## Purpose
Coordinate phased repository closure and release hardening with explicit gates and checkpoint artifacts.

## Required Inputs
- `PRD.md`
- `PROGRESS.md`
- `TASK_LEDGER.md`
- `VERSION.json`
- `release/RELEASE_MANIFEST.json`
- `config/reliability/slo.yaml`
- `docs/ops/V3_8_PRODUCTION_READINESS.md`

## Worker Roles
- **Manager:** dmn-manager-orchestrator (gate owner)
- **Closure Worker:** `agent-ralph-wiggum` (reconcile -> persist -> re-check loops)
- **Infra Worker:** workflows/deploy/runtime hardening
- **Docs Worker:** PRD/progress/task ledger and docs alignment
- **Runtime Worker:** contract/schema/tool-registry and agent loop consistency

## Governance Rules
1. Treat the V3.8 PRD, release manifest, and reliability policy as top-level gate authority.
2. Do not close any task item without concrete file evidence.
3. Record verification results and residual risk in `PROGRESS.md` and `TASK_LEDGER.md`.
4. Preserve active compatibility routes and contract authorities during cleanup.
5. Allow destructive cleanup only after the release gate explicitly approves it.
6. Require a passing rollback and incident-readiness review before release close.

## Closure Loop
1. Reconcile open V3.8 items from `PRD.md`, `PROGRESS.md`, and `TASK_LEDGER.md`.
2. Implement fixes and generate evidence paths.
3. Update the V3.8 ledger only where evidence exists.
4. Persist validation results and unresolved blockers in the release tracker.
5. Re-run reconciliation until open count is zero or externally blocked.

## V3.8 Release Gate Exit Conditions
- **A:** Canonical package, release manifest, and deployment topology agree on V3.8.
- **B:** Runtime-contract and tool-registry authorities remain singular and path-valid.
- **C:** Governed skills validate with versioned metadata, policy scopes, and source paths.
- **D:** Runtime events enforce run, agent, and lane observability dimensions.
- **E:** Reliability policy, incident procedure, and rollback command validate.
- **F:** Full validation matrix passes and release docs contain no deprecated release references.
- **G:** Pull-request checks and review are complete before squash-merge readiness is reported.
