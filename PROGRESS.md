# MEA V3.8 Release Tracker

**Status:** Active release baseline

## Release state

MEA V3.8 is the sole active release line. Its canonical package identity is kernel `3.8` and package `0.3.8`. Version authority resides in `VERSION.json`, `pyproject.toml`, and `release/RELEASE_MANIFEST.json`.

| Workstream | Status | Evidence |
| --- | --- | --- |
| Platform consolidation | Complete | Canonical ownership map in `PRD.md`; V3.8 compose and container artifacts in `deploy/`. |
| Governed skills | Complete | Skill schema, parser/validator, and regression suite. |
| Runtime observability | Complete | Runtime-event contract requires `run_id`, `agent_id`, and `lane`. |
| Reliability hardening | Complete | SLO/error-budget policy, rollback procedure, and regression suite. |
| Release alignment | In verification | Local and continuous-integration gates must pass on the release commit. |

## Required release evidence

The release cannot close until the following evidence is attached to the pull request.

1. The full test suite, lint, format, type, dependency, and diff checks are green.
2. The V3.8 compose configuration and V3.8 container build validate successfully.
3. All governed skill metadata validates with unique capability identities and existing authorities.
4. The reliability policy validates and a rollback drill remains executable through `deploy/rollback.sh`.
5. Continuous-integration results are terminal and successful; skipped deployment jobs are classified by their environment gates.

## Compatibility verification

V3.8 keeps the operational health, ingest, runtime-session, decision, and verifier routes listed in `PRD.md`. Compatibility is enforced through the repository’s regression suite; release cleanup does not remove active runtime contract or tool-registry authorities.
