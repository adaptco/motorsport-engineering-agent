---
name: motorsport-a2a-handoff
version: 1
source_of_truth:
  - PRD.md
  - PROGRESS.md
purpose: >-
  Normalize asynchronous multi-agent handoffs for the Motorsport Engineering Agent
  by persisting workflow position and resumable session context outside conversation history.
---

# Motorsport A2A Handoff Skill

## Intent
Use this skill when an agent must continue work started by a prior agent session without relying
on conversational context.

## Inputs
- `session_id` (string): Stable session/workstream identifier.
- `workflow_id` (string): Logical workflow name (`release-gate`, `mea-kernel-ci`, etc.).
- `run_id` (string, optional): CI run or orchestration run id.
- `trace_id` (string, optional): Trace correlation id.
- `current_position` (string): Current step/checkpoint in workflow.
- `status` (enum): `pending|running|blocked|completed|failed`.
- `summary` (string, optional): Human-readable snapshot.
- `pending_actions` (array<string>, optional): Explicit next actions.
- `artifacts` (array<object>, optional): Files/URLs used for continuation.

## Required Behavior
1. Persist `workflow_state.current_position` after each completed step.
2. Record `updated_at` and increment `version` on every write.
3. Load latest state on startup before planning next action.
4. Fail closed if persisted state is malformed (validate against schema).

## Contracts
- Workflow state schema: `contracts/a2a/workflow_state.schema.json`
- Handoff event schema: `contracts/a2a/handoff_event.schema.json`
- Worker persistence runtime: `worker/background_workers.py`
- Compatibility shim path: `workers/background_workers.py`

## Environment Contract
- `A2A_WORKFLOW_STATE_DIR` default `.mea_tmp/workflow_state`
- `A2A_WORKFLOW_STATE_SCHEMA` default `contracts/a2a/workflow_state.schema.json`
- `A2A_WORKFLOW_STATE_MAX_HISTORY` default `50`

## Resume Algorithm
1. Read latest state by `session_id` + `workflow_id`.
2. Validate JSON shape against contract.
3. Build minimal resume context from persisted summary + pending actions + last artifacts.
4. Continue from `current_position`.
5. Persist updated position/results.
