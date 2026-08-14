# Motorsport Engineering Agent V3.8 Product Requirements

## Release objective

MEA V3.8 is the repository’s single active release baseline. It consolidates package and deployment ownership, exposes governed skill capabilities, and establishes production-readiness gates without removing the critical public API surface.

## Architecture and ownership

The platform is organized into bounded ownership areas. The control plane owns ingress, validation, runtime state, and the aerodynamic simulation API. The orchestrator owns deterministic execution, handoffs, leases, receipts, and checkpoints. The MCP server owns controlled tool discovery and invocation. The worker owns asynchronous execution. The telemetry and aerodynamic lanes remain separate, with evidence links rather than shared mutable state.

| Area | Canonical authority | V3.8 responsibility |
| --- | --- | --- |
| Runtime agent metadata | `mcp.json` | Deterministic agent discovery. |
| Tool contracts | `mcp_v1_runtime_bundle/tool-registry.json` | Controlled orchestration tool discovery. |
| Runtime events | `contracts/runtime/agent_runtime_contract_bundle.schema.json` | Validated, receipted execution events. |
| Governed skills | `contracts/skills/skill_contract.schema.json` | Versioned capability metadata and policy scope. |
| Reliability policy | `config/reliability/slo.yaml` | SLOs, error budgets, observability dimensions, and rollback readiness. |
| Release metadata | `VERSION.json`, `pyproject.toml`, `release/RELEASE_MANIFEST.json` | Canonical version and package identity. |

## Functional requirements

### Platform consolidation

The control-plane, orchestrator, MCP, worker, telemetry, and aerodynamic boundaries are independently owned. Runtime-contract and tool-registry identities are not duplicated. The V3.8 compose topology and container base are the only active deployment cut.

### Governed capabilities

Every repository `SKILL.md` must contain a unique capability name, a descriptive purpose, a `contract_version`, a permitted `policy_scope`, and valid source-of-truth paths. `shared.skill_contracts.validate_skill_repository` enforces this contract in the regression suite.

### Runtime and observability

Every event validated by the runtime contract must include `run_id`, `agent_id`, and `lane`; tool requests must include an idempotency key. The execution loop preserves schema validation, policy and budget gates, state transitions, checkpoints, blocked/resume paths, and receipts.

### Production hardening

The reliability policy defines availability objectives and 30-day error budgets for the control plane, MCP server, and backend worker. The release gate requires valid observability context, a documented incident procedure, an executable rollback command, a reproducible container/compose cut, and regression coverage for fallback, checkpoint/resume, and event ordering.

### Compatibility commitments

The following public routes remain available throughout the V3.8 release line:

- `GET /healthz`
- `GET /healthz/dependencies`
- `GET /ingest/sources`
- `POST /ingest/normalize`
- `POST /runtime/logs/parse`
- `GET /runtime/sessions`
- `POST /agent/decision`
- `POST /verifier/execute`

## Completion criteria

| Criterion | Completion evidence |
| --- | --- |
| Consolidated ownership | Contract authorities and deployment topology are documented in this PRD and tested by the release suite. |
| Governed skills | `contracts/skills/skill_contract.schema.json`, `shared/skill_contracts.py`, and `tests/test_skill_contracts.py` pass. |
| Observability | Runtime events require run, agent, and lane identifiers; regression coverage rejects missing identifiers. |
| Reliability | `config/reliability/slo.yaml`, `shared/reliability.py`, and `tests/test_reliability_policy.py` pass. |
| Rollback readiness | `docs/ops/V3_8_PRODUCTION_READINESS.md` documents the drill and invokes `deploy/rollback.sh`. |
| Release alignment | Canonical release metadata, current docs, deployment files, and automation target V3.8 only. |

## Verification

```bash
uv sync --extra dev --locked
uv run --extra dev pytest -q -rs
uv run --extra dev pytest -q --cov=control_plane --cov=services.orchestrator --cov=shared
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
docker compose -f deploy/compose/docker-compose.v3.8.yml config
docker build -f deploy/containers/mea-v3.8/Dockerfile -t mea:v3.8 .
```

V3.8 is complete only when all applicable local and continuous-integration checks pass, every release surface identifies V3.8, and the release readiness evidence is attached to the pull request.
