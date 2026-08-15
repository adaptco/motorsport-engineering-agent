# Contributing

## Development Setup

1. Use Python 3.11+.
2. Install dependencies with `uv`:
   - `uv sync --extra dev`
3. Install the repository hooks:
   - `uv run pre-commit install`
4. Copy `.env.example` to `.env` and set local values.

## Local Run

1. Start dependencies (Postgres, Redis).
2. Start services:
   - `uv run uvicorn control_plane.app:app --reload`
   - `uv run uvicorn mcp_server.app:app --port 7000 --reload`
   - `uv run python -m worker.backend_worker`

## Quality Gates

Run these before opening a PR:

- `uv run pytest -q`
- `uv run ruff check .`
- `uv run mypy control_plane worker shared`
- `uv run pre-commit run --all-files`

The V3.8 runtime-reference hook rejects deprecated MEA V3.x product references and unpinned `latest` MEA image tags. Use explicit V3.8 values: kernel `3.8`, package `0.3.8`, and component image tags ending in `:3.8`.

## PR Guidelines

1. Keep changes scoped to one task lane.
2. Add tests for behavior changes.
3. Update tracker docs (`TASK_LEDGER.md`, `PROGRESS.md`) when closing a tracked task.
4. Avoid reverting unrelated user changes in dirty worktrees.

## Branching

- Use `codex/*` branches for implementation slices.
- Prefer additive migrations and compatibility-safe changes.
