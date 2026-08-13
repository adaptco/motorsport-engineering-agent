# Phase F Checkpoint - Runtime/Agent Contract Unification

- Date: 2026-04-09
- Scope: Align runtime discovery around one contract authority and one tool registry.

## Contract Unification Actions
- Added root runtime authority skill:
  - `SKILL.md` declares `mcp.json` + `mcp_v1_runtime_bundle/tool-registry.json` as authoritative.
- Updated runtime bundle publication docs:
  - `mcp_v1_runtime_bundle/Agents.md` now includes explicit runtime contract source pointer (`../mcp.json`).
  - `mcp_v1_runtime_bundle/SKILL.md` now lists `../mcp.json` as required and authoritative.
- Added explicit OpenAPI extensions:
  - `x-runtime-contract-source: ../mcp.json`
  - `x-tool-registry-source: ../mcp_v1_runtime_bundle/tool-registry.json`
- Updated A2A skill contracts to reference the same authority paths.

## Validation
- JSON/YAML contract parse checks passed for:
  - `mcp.json`
  - `mcp_v1_runtime_bundle/tool-registry.json`
  - `mcp_v1_runtime_bundle/openapi/orchestration-agent.openapi.yaml`

## Files Changed
- `SKILL.md`
- `mcp_v1_runtime_bundle/Agents.md`
- `mcp_v1_runtime_bundle/SKILL.md`
- `mcp_v1_runtime_bundle/openapi/orchestration-agent.openapi.yaml`
- `skills/a2a_handoff/SKILL.md`
- `skills/a2a-mcp-agent-env-map/SKILL.md`
- `docs/checkpoints/PHASE_F.md`

## Residual Risks
- Runtime consumers outside this repository must adopt the new pointer semantics if they were hardcoding legacy discovery paths.
