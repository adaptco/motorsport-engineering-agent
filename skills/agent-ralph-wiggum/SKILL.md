---
name: agent-ralph-wiggum
description: Persist and reconcile evidence-backed task closure loops while checkpointing workflow progress until all tracked actions are complete.
contract_version: "1.0"
policy_scope: write
source_of_truth:
  - PRD.md
  - TASK_LEDGER.md
---

# Agent Ralph Wiggum

## Overview

Run deterministic "reconcile -> persist -> re-check" loops for release closure work.
Track open checklist items and PRD acceptance criteria as durable workflow state so loops can safely resume after interruption.

## Workflow

1. Gather the V3.8 task sources:
- `PRD.md`
- `PROGRESS.md`
- `TASK_LEDGER.md`
- `docs/ops/V3_8_PRODUCTION_READINESS.md`

2. Build reconciliation state using:
- `reconcile_remaining_actions(...)` to produce actionable open items
- `run_task_reconciliation_loop(...)` to persist loop progress until completion or max-iteration block

3. Persist every iteration:
- Keep `session_id` and `workflow_id` stable
- Store pending actions in workflow state
- Use metadata fields (`loop_iteration`, `acceptance_criteria_remaining`) to make block reason explicit

4. Update execution docs after each loop:
- Update `TASK_LEDGER.md` status rows
- Update `PROGRESS.md` phase/board status
- Keep unresolved items explicit in `pending_actions` rather than dropping them from the loop

5. After any PR is created:
- Normalize PR lifecycle labels/comments using `scripts/github_pr_lifecycle.sh normalize <pr_number> v3.8`.
- Run review follow-up automation using `scripts/github_pr_api.sh post-yeet-followup <pr_number> [test_command]`.
- Keep closure actions open until review conversations are resolved and validation passes.

## Guardrails

- Never mark an item complete without concrete file-level evidence.
- Never bulk-close checklist items by policy, summary, or "closure note" text.
- Close checklist items only through `close_checklist_items_with_evidence(...)`.
- Every closure must cite one or more real paths that exist in the workspace.
- If an item cannot be evidenced in this turn, keep it open and carry it forward in `pending_actions`.
- Keep loop iterations bounded and persist blocked state when max iterations are exhausted.
- Treat PRD acceptance criteria (`AC-*`) as first-class gate checks, not optional notes.

## Evidence-First Closure Process

1. Reconcile open work with `reconcile_remaining_actions(...)`.
2. Implement artifact/code changes.
3. Close only evidence-backed checklist items using:
   - `close_checklist_items_with_evidence(checklist_path=..., closures=[...])`
4. Re-run reconciliation.
5. Repeat until remaining count is zero or work is genuinely blocked by external dependency.

## Reference

See [references/loop-playbook.md](references/loop-playbook.md) for canonical invocation patterns.
