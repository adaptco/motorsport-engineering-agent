# Ralph Loop Playbook

## Standard Invocation

1. Run reconciliation:
```python
from worker.background_workers import run_task_reconciliation_loop

state = run_task_reconciliation_loop(
    session_id="release-v3.8",
    workflow_id="v3.8-release-gate",
    task_files=[
        "PRD.md",
        "PROGRESS.md",
        "docs/ops/V3_8_PRODUCTION_READINESS.md",
    ],
    task_ledger_path="TASK_LEDGER.md",
    mcp_prd_path="PRD.md",
    completed_acceptance_criteria=[],
    max_iterations=10,
    sleep_seconds=0,
)
```

2. Consume output:
- `state["status"] == "complete"`: all tracked work is closed.
- `state["status"] == "running"`: more loop iterations can continue.
- `state["status"] == "blocked"`: max iterations reached; resolve pending items, then rerun.

## Operational Pattern

- Run reconciliation before changing status tables.
- Execute concrete fixes.
- Close only evidence-backed checklist lines via `close_checklist_items_with_evidence(...)`.
- Rerun reconciliation.
- Update `TASK_LEDGER.md` and `PROGRESS.md` only after evidence is present.
