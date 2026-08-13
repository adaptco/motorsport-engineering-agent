# SKILL.md

## Skill Name
`mcp-v1-single-agent-release`

## Purpose
This skill drives a checkpointed, resumable generation workflow for a single-agent MCP V1 runtime.

## Operating model
Use a graph-based runtime with explicit phase transitions:
1. `freeze_plan`
2. `generate_schemas`
3. `generate_openapi`
4. `generate_runtime_module`
5. `generate_registry_and_docs`
6. `evaluate_release`

Each phase:
- consumes bounded context
- writes machine-readable outputs
- runs local validation
- writes a checkpoint
- emits a compact summary for downstream context

## Required files
- `../mcp.json`
- `generation-manifest.json`
- `schemas/generation-state.schema.json`
- `src/runtime/mcp-v1-runtime.ts`
- `openapi/orchestration-agent.openapi.yaml`
- `Agent.md`
- `Agents.md`
- `tool-registry.json`
- `PRD.md`

## Hot / warm / cold context
- **hot**: current phase targets, local dependencies, validator errors
- **warm**: manifest, reference map, compressed phase summaries
- **cold**: completed file bodies, prior receipts, archived diagnostics

## Checkpoint rules
Checkpoint after every successful phase. A checkpoint record must include:
- `checkpoint_id`
- `thread_id`
- `phase`
- `completed_files`
- `manifest_digest`
- `context_summary`
- `token_usage`
- `next_phase`

## Quality gates
### Schemas
- valid JSON
- unique `$id`
- stable refs

### OpenAPI
- valid OpenAPI 3.1
- unique `operationId`
- response models align to generation state and manifest contracts

### TypeScript
- parseable module
- node contract and state contract align
- no placeholder production TODOs

### Release evaluation
- planned file count == generated file count
- PRD acceptance criteria marked pass / fail with evidence

## Tool usage policy
Only use tools declared in `tool-registry.json`.
Treat `../mcp.json` as the authoritative runtime contract for agent identity and wiring.
In production mode:
- side-effectful tools require permits
- non-deterministic operations must be wrapped in tasks
- replay must reuse checkpointed outputs instead of reissuing side effects

## A2A publication
Publish the final orchestration agent entry to:
- `Agents.md`
- `registry/agents.registry.json`
