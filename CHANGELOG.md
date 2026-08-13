## v3.8 / 0.3.8
1. Version Manifest & Release Metadata Synchronization
Unified Kernel & Package Semver: Updated and synchronized the kernel version (3.8) and package version (0.3.8) across VERSION.json, pyproject.toml, README.md, and CHANGELOG.md.

Release Gate Validation: Enforced automated version alignment CI checks (tests/test_version_alignment.py) to validate that all package metadata, top-level headings, and manifest files strictly match prior to deployment.

2. Multi-Modal CFD & Simulation Expansion
CFD Multimodal Agent Package: Introduced the new A2A_MCP/packages/cfd-multimodal-agent workspace scaffold, including FastAPI microservice routes and Pydantic data models for handling multimodal aerodynamics and CFD pipeline execution.

Aerodynamics Simulator Enhancements: Integrated updated telemetry and aero-simulation state models to process aerodynamics data alongside core engine runtime state.

3. CI/CD Hardening & Code Quality
Ruff Formatting & Import Sorting: Enforced standard PEP 8 import sorting (I001) and lint rules across all new subpackages and test suites (tests/test_aero_simulation_state.py, tests/test_mcp_tools_guardrail.py, tests/test_time_domains.py).

Dependency & Security Maintenance: Upgraded core dependencies (including pytest coverage tools via pytest-cov >= 7.1.0) and updated environment locks to address security audit advisories across runtime packages (click, pyjwt, starlette, urllib3).

## v3.6.3 / 0.3.6.3

- consolidated production-readiness hardening and release metadata alignment for v3.6.3
- resolved merge conflicts and reconciled `PROGRESS.md` for the current baseline
- migrated `control_plane/app.py` from deprecated `on_event` hooks to `lifespan` context manager
- implemented production-hardening: circuit breakers for GitHub/MCP and persistent forensic ledger paths
- updated version alignment across `VERSION.json`, `pyproject.toml`, and `README.md`
- established V3.6 preparation roadmap in `TASK_LEDGER.md`

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
