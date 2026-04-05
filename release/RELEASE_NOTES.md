# MEA Root Kernel v3.5 / 0.3.5

This release adds a static-log ingestion harness to the governed control-plane kernel.

## Added
- `ingest/logs/` adapter registry and normalizer
- `tools/normalize_log.py` CLI
- control-plane ingest endpoints for local file normalization
- fixture-driven tests for CSV/VBOX normalization

## Intended use
Use v3.5 to validate native or vendor-export telemetry logs before wiring live sim adapters.
