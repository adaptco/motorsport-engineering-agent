# MEA V3.8 Versioning Specification

## Canonical identity

MEA V3.8 is the sole supported release line. The human-facing kernel version is `3.8`; the package version is `0.3.8`. The following files must agree before release promotion:

- `VERSION.json`
- `pyproject.toml`
- `release/RELEASE_MANIFEST.json`
- the first V3.8 heading in `CHANGELOG.md`

A release is valid only when it maps to one Git commit, all metadata surfaces agree, the deployment artifacts identify V3.8, and the applicable continuous-integration checks pass on that commit.

## Compatibility policy

V3.8 changes are additive with respect to the supported health, ingest, runtime-session, decision, and verifier routes listed in `PRD.md`. Runtime and tool discovery authorities must remain singular. Schema or endpoint changes that invalidate existing receipts, replay behavior, or public clients require a new release decision before implementation.

## Release verification

The release gate checks package metadata, runtime contract validity, governed-skill contracts, reliability policy, deployment topology, regression behavior, formatting, static analysis, dependency integrity, and Git diff hygiene. Release promotion requires a documented rollback procedure and terminal successful check results.
