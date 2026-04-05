## v3.5 / 0.3.5

- added `ingest/logs` static-log ingestion module with adapter registry
- added adapters for MoTeC `.ld`, iRacing `.ibt`, AiM `.xrk/.xrz`, VBOX `.vbo`, Pi MAT, and vendor CSV/TXT exports
- added canonical normalizer emitting `normalized_channels.csv`, `channel_manifest.csv`, and `session_manifest.json`
- added control-plane ingest endpoints and CLI harness for local module I/O testing
- added fixture-driven tests for normalization and API routing

# Changelog

## v3.4 / 0.3.4
- reissued the unified runtime-correctness kernel as the coherent V3.4 release
- aligned kernel release naming to the repo versioning specification: kernel V3.4 paired with package 0.3.4
- preserved the validated v3.3 runtime patch set without changing package semver
- sealed a single-source release bundle for Git import, validation, and promotion


## v3.3.0 / 0.3.3
- integrated runtime-correctness patch set into the v3.2 kernel
- added `PolicyEngine` logical clock and deterministic queue semantics
- added time-domain separation helpers (`DATA` vs `WALL`)
- added JSONL validation layer with monotonic timestamp and required-field checks
- extended replay service to use strict validation tasks
- added `POST /agent/decision` supervisor loop hook with paired forensic receipts
- added `evidence_packets` DB migration scaffold
- updated model weights and performance task manifests for sentry validation

## v3.2 / 0.3.2
- unified divergent v3.1 artifacts into a monorepo-safe release
