# Agents.md

## A2A Registry
This file is the human-readable registry for agent-to-agent discovery.
Runtime contract authority:
- `../mcp.json` (agent/runtime source of truth)
- `tool-registry.json` (single MCP v1 tool registry)
- `openapi/orchestration-agent.openapi.yaml` (transport contract)

### Agent: MCP V1 Orchestration Agent
- **agent_id**: `mcp-v1-orchestrator-single`
- **name**: `MCP V1 Orchestration Agent`
- **protocol**: `A2A v1`
- **role**: `orchestrator`
- **mode**: `single-agent`
- **runtime**: `typescript-langgraph`
- **entrypoint**: `src/runtime/mcp-v1-runtime.ts`
- **api_contract**: `openapi/orchestration-agent.openapi.yaml`
- **skill_document**: `SKILL.md`
- **agent_document**: `Agent.md`
- **tool_registry**: `tool-registry.json`
- **runtime_contract_source**: `../mcp.json`

### Responsibilities
- own release phase state
- coordinate resumable generation flow
- enforce checkpoint boundaries
- evaluate release against `PRD.md`
- publish evidence and registry outputs

### A2A routing contract
Inputs accepted:
- release generation requests
- resume requests with `thread_id`
- PRD evaluation requests
- registry inspection requests

Outputs emitted:
- state updates
- checkpoints
- evaluation reports
- registry metadata

### Interop notes
This registry is designed for future A2A expansion. In V1, only the orchestrator agent is active.
Consumers should resolve agent/runtime metadata from `../mcp.json` and only use this file as a human-readable index.
