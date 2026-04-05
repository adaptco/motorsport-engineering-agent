# PR-Ready Diff Plan (April 5, 2026)

This file groups the implemented and queued work into mergeable PR slices.

## PR-001: Reconcile Truth Surface and Tracking

### Scope

- Replace stale progress narrative with current verified state.
- Add canonical status artifacts.

### Files

- `PROGRESS.md`
- `CURRENT_STATE.md`
- `OPEN_BLOCKERS.md`
- `TASK_LEDGER.md`

### Suggested title

- `docs: reconcile current state and establish execution ledger`

## PR-002: Forensic Ledger Durability and Startup Validation

### Scope

- Eliminate `/tmp`-style default path drift.
- Validate ledger path/writeability at startup.
- Add persistence regression tests.

### Files

- `shared/runtime_paths.py`
- `control_plane/app.py`
- `control_plane/repository.py`
- `control_plane/routes/agent.py`
- `tests/test_forensic_ledger_persistence.py`

### Suggested title

- `control-plane: enforce persistent session ledger path and startup validation`

## PR-003: DB Pooling and Dependency Health Visibility

### Scope

- Add psycopg pool support with safe fallback.
- Expose pool/dependency health for operators.

### Files

- `shared/db.py`
- `control_plane/app.py`
- `.env.example`
- `docs/env.md`

### Suggested title

- `db: add pooled connection runtime and dependency health reporting`

## PR-004: Circuit Breakers and Bounded Retries

### Scope

- Add reusable circuit breaker.
- Guard GitHub API, Redis queue path, and MCP client calls.

### Files

- `shared/circuit_breaker.py`
- `control_plane/github_app.py`
- `control_plane/queue.py`
- `control_plane/services/mcp_client.py`
- `tests/test_circuit_breaker.py`
- `.env.example`

### Suggested title

- `resilience: add fail-closed circuit breakers and bounded retries`

## PR-005: Deployment and Operations Documentation

### Scope

- Add deployment, runbook, and env docs aligned with production blockers.

### Files

- `docs/deployment.md`
- `docs/runbook.md`
- `docs/env.md`
- `docs/ops/pr_ready_diffs.md`

### Suggested title

- `docs: add deployment, env, and runbook guidance for v3.5 operations`
