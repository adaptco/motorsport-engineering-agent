# Refactor Plan

## Phase 1
- preserve current control plane
- move shared pydantic models into `contracts/` and `packages/sdk-models`
- isolate MCP into dedicated gateway contract
- replace local workflow-state files with durable state service

## Phase 2
- introduce orchestrator service
- introduce agent registry + role config
- split agent roles into separate containers
- move telemetry normalization into standalone service

## Phase 3
- add eval engine + HITL verdict workflow
- append-only receipt ledger
- promotion gates for recommendations/debriefs
- replay / audit CLI and dashboards
