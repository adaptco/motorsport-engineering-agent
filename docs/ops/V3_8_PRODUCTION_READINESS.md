# MEA V3.8 Production Readiness

## Release authority

MEA V3.8 is the single active release baseline. Its authoritative package metadata is `VERSION.json`, `pyproject.toml`, and `release/RELEASE_MANIFEST.json`. Runtime event contracts are defined by `contracts/runtime/agent_runtime_contract_bundle.schema.json`; governed capability metadata is defined by `contracts/skills/skill_contract.schema.json`.

## Service-level objectives and error budgets

The executable policy in `config/reliability/slo.yaml` defines the V3.8 objectives. Every runtime measurement and receipt must carry the **run identifier**, **agent identifier**, and **lane** labels. The runtime-event schema enforces those dimensions on event envelopes.

| Service | Availability objective | 30-day error budget |
| --- | ---: | ---: |
| Control plane | 99.9% | 43.2 minutes |
| MCP server | 99.9% | 43.2 minutes |
| Backend worker | 99.5% | 216.0 minutes |

The release gate is failed when a service exceeds its error budget, a required observability label is absent, a governed skill fails validation, or rollback instructions cannot be executed from the current deployment tree.

## Reliability and regression gate

The mandatory V3.8 suite validates the following properties.

| Gate | Required evidence |
| --- | --- |
| Runtime contracts | Schema-valid events include `run_id`, `agent_id`, and `lane`; tool requests include idempotency keys. |
| Resilience | Circuit-breaker fallback, checkpoint/resume, and event-order tests pass. |
| Skill governance | Every `SKILL.md` has versioned metadata, a defined policy scope, valid source-of-truth paths, and a unique capability identity. |
| Deployment | `deploy/compose/docker-compose.v3.8.yml` parses, the V3.8 container builds, and `/healthz` succeeds for the deployed service roles. |
| Compatibility | Critical health, ingest, runtime-session, decision, and verifier routes remain covered by the regression suite. |

## Incident and rollback procedure

An operator must first record the affected `run_id`, `agent_id`, and lane, preserve the relevant logs and receipts, and stop promotion. If the condition cannot be mitigated within the applicable error budget, restore the last verified backup using the repository-owned rollback command.

```bash
./deploy/rollback.sh <backup_directory>
```

After rollback, confirm the control plane and MCP server respond on `/healthz`, run the V3.8 verification script, and attach the output to the incident record.

```bash
./deploy/verify-v3.8.sh
curl --fail http://localhost:8000/healthz
curl --fail http://localhost:7000/healthz
```

A rollback drill is complete only when the restored deployment exposes healthy endpoints, runtime contracts remain parseable, and the incident record includes the trigger, impact, rollback timestamp, validation output, and follow-up owner.
