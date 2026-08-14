# Changelog

## V3.8 / 0.3.8

MEA V3.8 consolidates the repository into a single supported release baseline.

- Formalized ownership boundaries for the control plane, orchestrator, MCP runtime, worker, telemetry, and aerodynamic simulation lanes.
- Added governed skill metadata contracts, repository validation, policy scopes, and source-of-truth checks.
- Added V3.8 reliability policy validation with service-level objectives, error budgets, incident guidance, and rollback readiness.
- Required `run_id`, `agent_id`, and `lane` in runtime event envelopes and retained idempotency enforcement for tool requests.
- Normalized release metadata, active deployment guidance, health checks, and automation to V3.8.
- Removed deprecated release plans, snapshots, patch notes, and implementation references from the working repository.
