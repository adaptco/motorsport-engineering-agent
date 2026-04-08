# Ralph Loop Playbook

## Standard Invocation

1. Run reconciliation:
```python
from worker.background_workers import run_task_reconciliation_loop

state = run_task_reconciliation_loop(
    session_id="release-v3.6",
    workflow_id="ralph-wiggum",
    task_files=[
        "TASK-004_DEPENDENCY_MANAGEMENT_FINDINGS.md",
        "TASK-005_DOCUMENTATION_AUDIT_FINDINGS.md",
        "TASK-006_DATABASE_STATE_MANAGEMENT_FINDINGS.md",
        "TASK-007_OPERATIONAL_HARDENING_FINDINGS.md",
    ],
    task_ledger_path="TASK_LEDGER.md",
    mcp_prd_path="mcp_v1_runtime_bundle/PRD.md",
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
