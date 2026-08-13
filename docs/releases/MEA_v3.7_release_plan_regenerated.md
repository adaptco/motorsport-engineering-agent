# MEA v3.7 & v3.8 Implementation Plan

## Objective

Deliver the multi-agent runtime slice (v3.7) and platform consolidation & production hardening (v3.8) as additive releases on top of the stabilized v3.6 baseline. Maintain full backwards compatibility with existing control-plane, ingest, and forensic ledger surfaces while introducing the new orchestration, MCP gateway, agent containers, evaluation surfaces, and hardening features.

## Release Context

- **Current baseline**: v3.6 / 0.3.6 (control-plane & runtime harness).
- **v3.7 goals**: orchestrator service, MCP gateway v1, workflow state plane, contract extraction, HITL evaluation surface, agent containers, backwards compatibility.
- **v3.8 goals**: platform consolidation, kernelization & gating across all services, resumable state, migrations, test coverage, runbook & external host contract, ADRs & gotchas, production readiness checklist.

## Workstream A — Contract Extraction & Versioning (v3.7)

- Create JSON schemas for:
    - `contracts/orchestration/run_envelope.schema.json`
    - `contracts/orchestration/agent_spec.schema.json`
    - `contracts/orchestration/handoff_event.schema.json`
    - `contracts/orchestration/checkpoint_receipt.schema.json`
    - `contracts/evals/eval_run.schema.json`
    - `contracts/evals/hitl_verdict.schema.json`
    - `contracts/telemetry/telemetry_frame.schema.json`
    - `contracts/telemetry/evidence_packet.schema.json`
    - `contracts/policy/tool_permit.schema.json`

- Refactor `shared/models.py` into dedicated modules:
    - `packages/sdk-models/contracts/orchestration.py`
    - `packages/sdk-models/contracts/telemetry.py`
    - `packages/sdk-models/contracts/evals.py`
    - `packages/sdk-models/contracts/mcp.py`

- Add JSON schema bundle generation in CI.
- Ensure version fields exist for all runtime contracts.
- Re-export old imports for backwards compatibility.

## Workstream B — Orchestrator Runtime (v3.7)

- Add new service `services/orchestrator`.
- Implement run creation endpoint and queue integration.
- Implement agent selection & dispatch logic.
- Persist run and handoff state to the durable database.
- Handle event gating and state checkpoints.
- Integrate orchestrator with existing MCP server & new gateway.
- Provide receipts for each stage of the run lifecycle.

## Workstream C — MCP Gateway v1 (v3.7)

- Create `apps/mcp-gateway` (or promote `mcp_server` as gateway).
- Expose `/mcp/v1/<provider>/<operation>` endpoints.
- Bridge provider calls to tool servers and third-party providers.
- Preserve legacy `/a2a/invoke` endpoints as compatibility aliases.
- Implement concurrency controls, auth, and error handling.
- Publish OpenAPI spec for tool providers.

## Workstream D — Agent Containers (v3.7)

- Introduce specialized agent services:
    - `services/agent-supervisor`
    - `services/agent-telemetry-analyst`
    - `services/agent-replay-analyst`
- Remove CI-specific worker semantics from generic worker.
- Ensure all agent traffic is routed via the orchestrator.
- Add queue lanes for runs, handoffs, and evaluation tasks.
- Provide container images and deployment specs for each agent.

## Workstream E — HITL Evaluation Surface (v3.7)

- Add `services/eval-engine` to manage human-in-the-loop evaluations.
- Implement endpoints for submitting evaluation runs and verdicts.
- Store evaluation evidence and scores in the database.
- Integrate eval results into orchestrator handoff decisions.
- Build an operator console in the `frontend` app for review.

## Workstream F — Deployment & Versioning (v3.7)

- Update Docker Compose, Kubernetes, and Helm charts to include new services.
- Define environment variables and secrets for orchestrator, gateway, agents, and eval-engine.
- Maintain existing v3.6 services for compatibility.
- Bump version to 3.7 in `VERSION.json`, `pyproject.toml`, and docs.
- Update `README.md` and release notes.

## Workstream G — Platform Consolidation & Hardening (v3.8)

- **Kernelization & gating**: implement a unified kernel model with five validation gates (ingest, orchestrator, tool, evaluation, commit) across all services.
- **Resumable state**: design run state schemas and persistence strategies for resumable workflows; add checkpoint/resume logic to orchestrator and agents.
- **Database migrations**: use Alembic to create migration scripts for new tables (runs, handoffs, checkpoints, evals, verdicts, receipts); integrate migrations into CI/CD.
- **Test matrix & coverage**: expand integration tests to cover multi-agent flows, error scenarios, resumptions, and performance; enforce coverage thresholds.
- **Runbook & external host contract**: document the architecture, endpoints, event sequences, failure modes, and scaling strategies; define a contract for external tool hosts and providers.
- **ADRs & gotchas**: record architectural decisions and known issues for transparency.
- **Production readiness checklist**: verify health checks, scaling policies, logging, monitoring, security hardening, and data retention; ensure all services meet readiness criteria.
- **Packaging consolidation**: update deployment manifests to remove deprecated services from v3.5.x; consolidate container images and environment configuration for a streamlined production release.

## Task List Summary

| Sprint | Key Deliverables | Status |
| --- | --- | --- |
| **v3.7 — Contracts & Orchestrator** | Define and publish JSON schemas; refactor `shared/models.py`; add orchestrator service; implement run/handoff state; generate schema bundle. | _Pending_ |
| **v3.7 — MCP Gateway & Agents** | Deliver MCP gateway v1; implement provider bridging; introduce agent-supervisor, agent-telemetry-analyst, agent-replay-analyst services; route traffic via orchestrator. | _Pending_ |
| **v3.7 — HITL & Deploy** | Build eval-engine & operator console; integrate HITL scoring; update deployment files; bump version & docs. | _Pending_ |
| **v3.8 — Kernelization & Gating** | Implement unified kernel model and validation gates across all services; design resumable state schemas; add checkpoint logic. | _Pending_ |
| **v3.8 — Hardening & Docs** | Create Alembic migrations; expand test suite; write runbook & host contract; publish ADRs & readiness checklist; consolidate deployment. | _Pending_ |

---

This document supersedes the previous `v3.7_IMPLEMENTATION_PLAN.md` and sets the roadmap for completing v3.7 and v3.8 releases on top of the v3.6 baseline while preserving compatibility.
