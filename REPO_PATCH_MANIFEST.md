# MEA V3.6 Patch Manifest

This manifest describes the changes required to upgrade the `adaptco/motorsport‑engineering‑agent` repository from version `v3.5.2` to `v3.6`. The provided files in this patch implement the runtime contract harness, container cut, and initial tests.

## Added Files

| Path | Purpose |
| --- | --- |
| `contracts/runtime/agent_runtime_contract_bundle.schema.json` | First‑class JSON schema bundle defining all runtime events and gating contracts. |
| `deploy/containers/mea-v3.6/Dockerfile` | Base image for V3.6 control plane, worker, and MCP services, embedding the runtime contract bundle. |
| `deploy/compose/docker-compose.v3.6.yml` | Compose topology for the V3.6 deployment cut, mapping gateway → control plane → worker pool. |
| `docs/REPO_SNAPSHOT_2026-04-07.md` | Snapshot of the repository state prior to applying V3.6 changes. |
| `tests/test_runtime_contract_bundle.py` | Basic test verifying that the contract bundle can be loaded. |
| `tests/test_runtime_event_order.py` | Basic test ensuring required runtime events are defined in the bundle. |

## Modified Files (not included in this patch but must be updated by maintainers)

| Path | Description of Change |
| --- | --- |
| `PRD.md` | Replace review‑only content with the V3.6 implementation plan, goals, file plan, and success criteria. |
| `VERSION.json` | Update `kernel_version` to `3.6` and `package_version` to `0.3.6`. |
| `pyproject.toml` | Update package version to `0.3.6`. |
| `control_plane/app.py` | Emit runtime events: `run.created`, `workflow.policy.screened`, `step.dispatched`, `run.completed`, `run.failed`. |
| `control_plane/queue.py` | Integrate schema validation, budget gates, and resumable checkpoints. |
| `control_plane/services/mcp_client.py` | Propagate `idempotency_key` on tool requests and emit `tool.requested`, `tool.executed`. |
| `worker/backend_worker.py` | Emit `state.transitioned`, handle `blocked`/`resume.requested` flows. |
| `shared/db.py` | Add checkpoint persistence and resume token support. |
| `docker-compose.yml` | Deprecate the root single‑container service; reference the V3.6 compose file or ensure legacy containers remain until fully migrated. |
| `control_plane/Dockerfile`, `worker/Dockerfile`, `mcp_server/Dockerfile` | Build from the new V3.6 base image or incorporate the runtime bundle. |

## Deleted / Deprecated

| Path | Reason |
| --- | --- |
| `Dockerfile` (root) | Legacy single‑container entrypoint; superseded by service images in V3.6. |

## Notes for Maintainers

1. **Version Bump:** After merging this patch, bump `VERSION.json` and `pyproject.toml` to reflect the new V3.6 versions.
2. **Schema Validation:** The runtime must validate each event against the corresponding schema in the bundle. Integration points should call a common validator before emitting receipts or state transitions.
3. **Idempotency Keys:** All tool calls that produce side effects must include an `idempotency_key` in `tool.requested`. The runtime should use this key to ensure safe retries.
4. **State Transition and Checkpoint Events:** Emit `state.transitioned` after each successful runtime step and `checkpoint.persisted` whenever a safe resume point is committed.
5. **Resume and Blocked Flows:** Implement logic to emit `blocked` events with retry semantics when deadlines, rate limits, token budgets, or tool errors are encountered. Use `resume.requested` events to resume execution once conditions allow.
6. **Tests:** Extend the provided tests to cover representative event flows (valid plan, repaired plan, invalid action, blocked path, completed run). Ensure tests run under `pytest`.
7. **Documentation:** Update `PRD.md` to reflect the full implementation details, goals, and acceptance criteria for V3.6. Include architecture diagrams and event sequences as necessary.

This manifest is intended to guide maintainers in applying the patch cleanly and avoiding merge conflicts. It does not modify existing files directly; those changes should be applied manually or using Git operations outside of this read‑only environment.