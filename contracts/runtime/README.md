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
