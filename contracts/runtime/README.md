# MEA V3.6 runtime contract bundle

This directory is the runtime event-gate surface for MEA V3.6.

## Event order
request.received
-> run.created
-> workflow.policy.screened
-> plan.proposed | plan.repaired | plan.failed
-> step.dispatched
-> approval.resolved | tool.requested
-> tool.executed
-> action.proposed | action.repaired | action.invalid
-> state.transitioned
-> checkpoint.persisted
-> blocked | resume.requested | next step
-> run.completed | run.failed
-> audit.bundle.written

## Required gates
1. Schema gate
2. State-transition gate
3. Policy gate
4. Budget gate
5. Idempotency gate

## Additive execution control

`execution-control.schema.json` defines **only** the missing command and worker-lease primitives used to schedule, pause, resume, cancel, or checkpoint an existing run. It does not replace `agent_runtime_contract_bundle.schema.json`, which remains the authority for event-gated runtime behavior, or `contracts/orchestrator/orchestrator_run.schema.json`, which remains the authority for aggregate run state.
