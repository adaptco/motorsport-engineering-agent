# Agents.md

## A2A Registry
This file is the human-readable registry for agent-to-agent discovery.

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
