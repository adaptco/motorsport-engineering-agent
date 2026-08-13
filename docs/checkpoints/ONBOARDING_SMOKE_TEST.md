# Onboarding Smoke Test (v3.6.3)

- Date: 2026-04-09
- Environment: local clean `.venv-ci`
- Commands:
  - `uv sync --extra dev`
  - `uv run pytest tests/test_version_alignment.py -q`
- Measured elapsed time: `14 seconds`
- Result: PASS
- Assessment: New developer baseline setup/test smoke completed in < 2 hours.
