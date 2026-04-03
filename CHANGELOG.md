# Changelog

## v3.3.1 / 0.3.4
- normalized the v3.3 runtime-correctness release into a single bundle
- aligned embedded version metadata across VERSION.json, pyproject.toml, README, and release artifacts
- preserved the v3.3 patch set without changing runtime contracts
- verified the packaged tree against the test suite before sealing the release

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
