# MEA Root Kernel v3.3.1

MEA Root Kernel v3.3.1 builds on the governed v3.2 core and integrates the runtime-correctness patch set required for temporally correct replay, policy determinism, and supervisor-loop readiness.

## What v3.3 adds
- PolicyEngine logical clock with deterministic queue behavior
- DATA vs WALL time-domain helpers
- strict JSONL validation for replay artifacts
- `POST /session/replay` backed by replay validation tasks
- `POST /agent/decision` supervisor loop hook with paired receipts
- evidence packet schema migration scaffold
- sentry-style metrics and model-weight manifests

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest -q
uvicorn control_plane.app:app --reload
```

## Release authority
Use `docs/versioning-spec.md` as the release authority for kernel and package revisions.

## Environment
- `GITHUB_WEBHOOK_SECRET` (**required for webhook processing**): shared secret used to verify `X-Hub-Signature-256` on `/github/webhook`. If this value is missing or blank, webhook requests are rejected with HTTP `503` fail-closed behavior.
- `GITHUB_WEBHOOK_REQUIRED` (optional, default `false`): when set to `true`/`1`/`yes`, control-plane startup fails unless `GITHUB_WEBHOOK_SECRET` is configured.
- `OPENAI_API_KEY` (required for supervisor/agent routes that call OpenAI-backed models).

