---
name: mea-runtime-contract-authority
description: Enforce a single-source runtime contract for orchestration and tool discovery so every consumer resolves tools from mcp.json plus mcp_v1_runtime_bundle/tool-registry.json without repository-wide scanning.
contract_version: "1.0"
policy_scope: read
source_of_truth:
  - mcp.json
  - mcp_v1_runtime_bundle/tool-registry.json
---

# MEA Runtime Contract Authority

## Objective
Keep runtime discovery deterministic and fail-closed across orchestration, A2A handoff, and MCP tools.

## Authoritative contract sources
1. `mcp.json` is the single source for runtime agent contract metadata.
2. `mcp_v1_runtime_bundle/tool-registry.json` is the single source for orchestrator tool contracts.
3. `mcp_v1_runtime_bundle/openapi/orchestration-agent.openapi.yaml` must reference the same contract authority.
4. `mcp_v1_runtime_bundle/Agents.md` must publish discovery pointers, not alternate definitions.

## Required invariants
1. Do not duplicate agent identity/contract data in multiple files without an explicit pointer to `mcp.json`.
2. Do not introduce additional tool registry files for MCP v1 runtime.
3. Keep A2A handoff docs/skills aligned to the same runtime and tool contract paths.
4. If contract files move, update all pointers in the same change set.

## Minimal verification
1. Validate JSON/YAML parse for `mcp.json`, `tool-registry.json`, and OpenAPI contract.
2. Verify references in `SKILL.md`, `Agents.md`, and A2A skill docs point to current paths.
3. Run focused tests for any path-sensitive contracts.
