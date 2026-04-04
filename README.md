# MEA Root Kernel v3.4.0

MEA Root Kernel v3.4.0 aligns runtime health and package reporting with `VERSION.json` as the single authoritative release source.

## What v3.4 adds
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
