# Dependency Workflow

## Source of Truth

- `pyproject.toml` is the canonical dependency declaration.
- `uv.lock` is the reproducible lock artifact.
- Legacy root `requirements.txt` is intentionally removed.

## Install

Preferred:

```bash
uv sync --extra dev
```

Alternative editable install:

```bash
pip install -e .[dev]
```

## Update Dependencies

1. Update version constraints in `pyproject.toml`.
2. Regenerate lock file:
   - `uv lock`
3. Run quality gates:
   - `uv run pytest -q`
   - `uv run ruff check .`
   - `uv run mypy control_plane worker shared`

## Security and CVE Scanning

- CI runs `pip-audit` using the locked environment.
- Address findings by updating constraints + `uv lock`.

## Version Constraint Strategy

- Use lower-bound constraints (`>=`) in `pyproject.toml`.
- Use `uv.lock` to pin exact transitive versions for reproducibility.

## Python Version Matrix

- CI validates with Python 3.11 and 3.13.
