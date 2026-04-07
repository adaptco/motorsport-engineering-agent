# MEA Root Kernel v3.5

MEA Root Kernel v3.5 adds a static-log ingestion harness for native motorsport data files and exported telemetry files, integrated into the existing control-plane scaffold.

It introduces a first testable path for file I/O normalization before live sim adapter work.

## What v3.5 adds
- `ingest/logs/` native-log ingestion skeleton
- off-the-shelf adapters for MoTeC `.ld`, iRacing `.ibt`, AiM `.xrk/.xrz`, VBOX `.vbo`
- vendor-export adapters for Pi MAT, Haltech CSV/TXT, and AEM CSV/TXT
- canonical channel mapper and normalizer that emit normalized CSV artifacts
- `tools/normalize_log.py` CLI for local testing
- control-plane endpoints: `GET /ingest/sources`, `POST /ingest/normalize`
- fixture-driven tests for CSV/VBOX normalization and ingest API

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

## System architecture
Use `docs/system_architecture.md` as the canonical runtime architecture baseline for v3.5.
