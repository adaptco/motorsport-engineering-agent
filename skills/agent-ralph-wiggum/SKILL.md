---
name: agent-ralph-wiggum
description: Persist and reconcile long-running task closure loops for this repository. Use when Codex needs to repeatedly assess markdown task findings, `TASK_LEDGER.md`, and MCP PRD acceptance criteria while checkpointing workflow progress in `worker/background_workers.py` until all tracked actions are complete.
---

# Agent Ralph Wiggum

## Overview

Run deterministic "reconcile -> persist -> re-check" loops for release closure work.
Track open checklist items and PRD acceptance criteria as durable workflow state so loops can safely resume after interruption.

## Workflow

1. Gather task sources:
- Findings docs such as `TASK-004_DEPENDENCY_MANAGEMENT_FINDINGS.md`
- `TASK_LEDGER.md`
- MCP PRD such as `mcp_v1_runtime_bundle/PRD.md`

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

## Guardrails

- Never mark an item complete without concrete file-level evidence.
- Keep loop iterations bounded and persist blocked state when max iterations are exhausted.
- Treat PRD acceptance criteria (`AC-*`) as first-class gate checks, not optional notes.

## Reference

See [references/loop-playbook.md](references/loop-playbook.md) for canonical invocation patterns.
