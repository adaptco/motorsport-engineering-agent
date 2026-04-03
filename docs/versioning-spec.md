# Kernel Versioning and Revision Specification

## Problem this spec fixes

Two different artifacts were released as **v3.1 / 0.3.1** while containing different files and APIs. That means the version number did not uniquely identify the codebase.

From this point on, a version label must map to **one** canonical Git tree and **one** release manifest.

## Version surfaces

There are two version surfaces:

1. **Kernel release version**: `VMAJOR.MINOR`
   - human-facing release line, e.g. `V3.2`
2. **Package version**: `MAJOR.MINOR.PATCH`
   - Python package / container build semver, e.g. `0.3.2`

The package version must be embedded in `pyproject.toml` and `VERSION.json`.

## Release authority

A release is valid only if all are true:

- one Git commit SHA is designated as the source of truth
- `VERSION.json` and `pyproject.toml` agree
- release archive names match the embedded version
- a changelog entry exists
- CI passes on that exact commit

## Minor vs major changes

### Minor change: `V3.x -> V3.y`
Use a **minor** kernel bump when all are true:

- additive features only
- no breaking REST path removals
- no incompatible schema rewrites on canonical tables
- no required environment variable removals
- old clients can still replay and verify prior ledgers
- migration path is forward-compatible

Examples:

- add `/session/{id}/replay-ledger`
- add a new allowed verifier job
- add MCP provider metadata endpoints
- add GitHub Actions jobs without changing API contracts

### Major change: `V3.x -> V4.0`
Use a **major** kernel bump when any are true:

- canonical receipt schema changes incompatibly
- replay semantics or state hash surfaces change incompatibly
- existing REST contracts break or are removed
- job-space contract changes in a way that invalidates prior policies
- old ledgers cannot be replayed without transformation
- package topology changes enough to require a migration guide

Examples:

- replacing `state_hash` calculation inputs
- renaming or deleting verifier endpoints used by current clients
- changing policy decision receipts so older chains are invalid
- switching the control ledger from append-only semantics to mutable snapshots

## Patch changes: `0.3.1 -> 0.3.2`
Patch bumps are for:

- bug fixes
- doc corrections
- test additions
- non-breaking build or packaging fixes
- release unification where runtime API remains additive

## Monorepo merge rule

A branch merges cleanly into the monorepo only if:

- file tree diff is conflict-free or resolved
- package version is unique
- container tags are unique
- migrations are ordered and unique
- GitHub workflow names are stable
- replay tests pass against previous stable fixtures

If two divergent trees share the same version label, **the next release must bump**. That is why the unified artifact is **V3.2 / 0.3.2**.
