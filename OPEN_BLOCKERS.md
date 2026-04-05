# Open Blockers (April 5, 2026)

## P0/P1 Carryover

1. `on_event` startup hooks are deprecated in FastAPI.
- Impact: warning-only today, but needs lifespan migration before production freeze.
- Evidence: pytest warnings from `control_plane/app.py`.
- Next action: migrate startup checks to lifespan context manager.

2. Redis fallback policy is environment-driven and still permissive by default.
- Impact: local-safe default, but production must explicitly set `QUEUE_ALLOW_IN_MEMORY_FALLBACK=false` to fail closed.
- Next action: enforce strict production env profile in deployment manifests.

3. DB pooling currently supports graceful fallback when `psycopg_pool` is unavailable.
- Impact: service still runs, but pooling benefits depend on runtime package availability.
- Next action: ensure `psycopg_pool` is present in production image and CI dependency checks.

## P2/P3/P4 Remaining

4. End-to-end ingest workflow assertion is split across multiple tests, not one single scenario test.
- Impact: coverage is good but fragmented.
- Next action: add one e2e-style test that performs `normalize -> ingest APIs -> debrief`.

5. Runtime GUI is a minimal local scaffold; no authenticated operator workflow yet.
- Impact: suitable for local HITL validation only.
- Next action: define auth, retention, and UX acceptance criteria for production.

6. Dependency lock strategy is still not finalized.
- Impact: version drift risk across local/CI/runtime images.
- Next action: choose lock workflow (constraints file or lockfile) and enforce in CI.
