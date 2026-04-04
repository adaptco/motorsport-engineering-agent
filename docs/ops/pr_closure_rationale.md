# Rationale: PR Closures vs. Inline Fixes (Fail-Closed Governance)

## Overview

Recent open PRs were closed rather than fixed as a direct application of the
**Fail-Closed** governance policy defined in
`docs/ops/github_pr_runbook.md` and `docs/ops/pr_remote_audit.md`.

## Reasons for Closure

1. **Preflight Failure**: The `scripts/pr_preflight.sh` utility is a hard gate.
   In environments where the GitHub CLI (`gh`) is missing or the canonical
   `origin` remote is not deterministically configured, the gate fails.
2. **Traceability Integrity**: Per `docs/ops/pr_remote_audit.md`, every
   operation must have a queryable "instruction -> execution -> receipt" chain.
   Attempts to "fix" branches in a state where the remote environment is not
   fully verified would violate traceability requirements.
3. **Linear History Enforcement**: Many automated `codex/` branches diverged
   from `main` or had conflicting histories. Closing and pruning these branches
   allows for a clean baseline so subsequent changes build on verified, linear
   history.
4. **Agent Authority**: Without a production-ready GitHub App identity (with
   signed commits and proper OIDC-backed authority), the agent lacks governance
   credits to safely mutate existing PRs that may contain human-authored or
   high-integrity code.

## Path Forward

- **Pruning**: Remove stale `codex/` and `fix/` branches to reduce cognitive
  load and prevent accidental merges of unverified code.
- **CI Hardening**: Implement SAST and better audit logging to make
  fail-closed decisions more transparent.
- **GitHub App Maturity**: Move from a basic script/token model to a
  structured GitHub App with restricted permissions and verifiable identities.
