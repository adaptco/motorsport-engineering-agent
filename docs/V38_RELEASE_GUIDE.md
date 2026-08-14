# MEA V3.8 Release Guide

## Purpose

This guide describes the supported V3.8 release path. The release identity is kernel `3.8` and package `0.3.8`; `VERSION.json`, `pyproject.toml`, and `release/RELEASE_MANIFEST.json` must agree before promotion.

## Pre-release validation

Run the repository quality gates from the project root. The full suite validates compatibility routes, runtime contracts, governed skills, reliability policy, release alignment, and deployment artifacts.

```bash
uv sync --extra dev --locked
uv run --extra dev pytest -q -rs
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run --extra dev mypy .
docker compose -f deploy/compose/docker-compose.v3.8.yml config
```

The build is ready for review only when all applicable commands pass and `git diff --check` reports no whitespace errors.

## Deployment cut

The supported topology is defined by `deploy/compose/docker-compose.v3.8.yml`. The common control-plane image is built from `deploy/containers/mea-v3.8/Dockerfile`.

```bash
docker build -f deploy/containers/mea-v3.8/Dockerfile -t mea:v3.8 .
docker compose -f deploy/compose/docker-compose.v3.8.yml up -d
deploy/verify-v3.8.sh
```

Verify the control-plane and MCP services with `/healthz`. Every runtime event must include `run_id`, `agent_id`, and `lane` so incident receipts can be correlated.

## Production readiness

The executable policy is `config/reliability/slo.yaml`. It contains the V3.8 SLOs, 30-day error budgets, required observability labels, and rollback reference. Operators must follow `docs/ops/V3_8_PRODUCTION_READINESS.md` when a service approaches or exceeds its error budget.

## Rollback

Stop promotion, retain the incident receipts and correlated logs, then restore the last verified backup:

```bash
./deploy/rollback.sh <backup_directory>
```

After rollback, rerun `deploy/verify-v3.8.sh` and validate both `/healthz` endpoints before closing the incident.
