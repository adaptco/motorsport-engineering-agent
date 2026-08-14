# MEA V3.8 Task Ledger

| Work item | Status | Evidence | Release gate |
| --- | --- | --- | --- |
| Canonical release identity | Complete | `VERSION.json`, `pyproject.toml`, `release/RELEASE_MANIFEST.json` | All metadata agrees on kernel 3.8 and package 0.3.8. |
| Platform ownership consolidation | Complete | `PRD.md`, `SKILL.md`, `mcp.json`, `mcp_v1_runtime_bundle/tool-registry.json` | Runtime and tool authorities remain singular. |
| Governed skill contracts | Complete | `contracts/skills/skill_contract.schema.json`, `shared/skill_contracts.py`, `tests/test_skill_contracts.py` | Every skill has versioned metadata, a scope, valid authority paths, and a unique identity. |
| Runtime observability | Complete | `contracts/runtime/agent_runtime_contract_bundle.schema.json`, `tests/test_runtime_contract_bundle.py` | Event envelopes require run, agent, and lane identifiers. |
| Reliability policy and error budgets | Complete | `config/reliability/slo.yaml`, `shared/reliability.py`, `tests/test_reliability_policy.py` | Service objectives, budgets, and required labels validate. |
| Deployment and rollback readiness | Complete | `deploy/compose/docker-compose.v3.8.yml`, `deploy/verify-v3.8.sh`, `docs/ops/V3_8_PRODUCTION_READINESS.md` | Compose, container, health, incident, and rollback procedures are defined. |
| Release documentation cleanup | Complete | `PRD.md`, `PROGRESS.md`, `CHANGELOG.md`, `release/`, `deploy/` | Deprecated release-era documents and references are removed or normalized. |
| Local and CI verification | In progress | Current worktree validation output and pull-request checks | All applicable checks must pass before release promotion. |
