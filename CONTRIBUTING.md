# Contributing

## Development Setup

1. Use Python 3.11+.
2. Install dependencies with `uv`:
   - `uv sync --extra dev`
3. Copy `.env.example` to `.env` and set local values.

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

## PR Guidelines

1. Keep changes scoped to one task lane.
2. Add tests for behavior changes.
3. Update tracker docs (`TASK_LEDGER.md`, `PROGRESS.md`) when closing a tracked task.
4. Avoid reverting unrelated user changes in dirty worktrees.

## Branching

- Use `codex/*` branches for implementation slices.
- Prefer additive migrations and compatibility-safe changes.
