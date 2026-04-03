# MEA Root Kernel v3.2

MEA Root Kernel v3.2 unifies the two divergent v3.1 artifacts into one monorepo-safe release.

## Why v3.2 exists

The prior `0.3.1` release label was applied to two incompatible trees:

- **`Root-Kernel-V3.1.zip`** contained a SQLite forensic ledger and a named-job verifier.
- **`Root-Kernel-V3.1-source.zip` / `Root-Kernel-V3.1-source.patch`** contained Postgres-backed session receipt replay and worktree bootstrap files.

Both carried the same package version even though their file trees and runtime surfaces differed. That creates merge ambiguity and invalidates provenance.

## What v3.2 unifies

- deterministic SQLite forensic ledger with append-only receipts
- session evidence ingestion with per-session replay verification
- job-space verifier with allowlists, timeouts, and receipt pairing
- GitHub App scaffold for workflow correlation
- MCP scaffold with provider registry and required API key discovery
- CI workflow that runs tests and builds all service images

## Services

- `control_plane/` — FastAPI control plane and replay/verifier APIs
- `mcp_server/` — MCP-compatible REST scaffold for A2A tool invocation
- `worker/` — background worker scaffold
- `shared/` — models, DB helpers, canonical hashing, forensic ledger
- `tests/` — unit and API tests for ledger, verifier, replay, and MCP scaffolding

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest -q
uvicorn control_plane.app:app --reload
```

## Release rule

Use `docs/versioning-spec.md` as the release authority for kernel and package revisions.
