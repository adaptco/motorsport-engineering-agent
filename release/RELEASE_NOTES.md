# MEA V3.8 Release Notes

MEA V3.8 is the single supported release baseline for the Motorsport Engineering Agent. It consolidates platform ownership, governs reusable capabilities through versioned `SKILL.md` metadata, and makes production readiness measurable through a repository-owned reliability policy.

The release requires runtime events to carry `run_id`, `agent_id`, and `lane` observability dimensions. Governed skills are parsed and validated against `contracts/skills/skill_contract.schema.json`. The reliability policy defines availability objectives, error budgets, incident response, and rollback readiness for the control plane, MCP server, and backend worker.

Operators should use `deploy/compose/docker-compose.v3.8.yml`, `deploy/containers/mea-v3.8/Dockerfile`, and `deploy/verify-v3.8.sh`. The detailed operating procedure is available in `docs/ops/V3_8_PRODUCTION_READINESS.md`.
