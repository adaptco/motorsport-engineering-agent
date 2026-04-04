# PR Remote Audit Log

## Context
- Operator workspace path (host example): `/workspace/motorsport-engineering-agent`
- Container runtime workdir (Dockerfiles): `/app`
- Audit timestamp (UTC): 2026-04-04
- Objective: establish canonical remote metadata and verify PR discovery prerequisites.

## Current Verified State (fail-closed)
1. No canonical `origin` remote is currently configured.
2. Remote connectivity/auth verification cannot pass until a canonical remote URL is provided and configured.
3. PR discovery cannot run in this environment because no provider remote is configured and GitHub CLI (`gh`) is not installed.

## Evidence
### Remote inventory
```bash
git remote -v
```
Output: *(no remotes returned)*

### Connectivity/auth check
```bash
git ls-remote --heads origin
```
Output:
```text
fatal: 'origin' does not appear to be a git repository
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```
Exit code: `128`

### PR discovery tooling availability
```bash
gh pr list --state open
```
Output:
```text
/bin/bash: line 1: gh: command not found
```

## Required deterministic inputs to unblock
- Canonical repository URL (exact): e.g. `https://github.com/<org>/<repo>.git` or `git@github.com:<org>/<repo>.git`.
- Access method: HTTPS + PAT / GitHub App token, or SSH key-based auth.
- Provider for PR discovery: GitHub/GitLab/Bitbucket (to select command/API path).
- If using API fallback: provider token with read access to pull requests.
- Baseline commit SHA agreed by maintainers for first `main` branch publication.
- Repository admin authority (or automation identity) allowed to configure branch protection rules.

## Reproducible execution sequence after URL is supplied
### Option A: GitHub CLI path (if `gh` is installed)
```bash
git remote add origin <repo-url>
git ls-remote --heads origin
git remote get-url origin
gh pr list --state open
```

### Option B: GitHub API fallback (no `gh` dependency)
```bash
git remote add origin <repo-url>
git ls-remote --heads origin
git remote get-url origin
export GITHUB_TOKEN='<token-with-pr-read>'
export REPO_SLUG='<org>/<repo>'
curl -fsSL \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${REPO_SLUG}/pulls?state=open&per_page=100"
```

Archive command output and response payload in this log for auditable PR-state reproduction.

## Branch initialization and protection governance (authoritative policy)

### Instruction-to-execution mapping
1. **Fetch authoritative branches from remote:** `git fetch --all --prune`.
2. **If remote has `origin/main`, create local tracking branch:** `git checkout -b main --track origin/main`.
3. **If remote does not have `main`, create it from agreed baseline commit and push with branch protections enabled**.
4. **Define branch protection requirements (required checks/reviews) in platform governance docs**.

### Verified execution receipts (2026-04-04 UTC)
```bash
git fetch --all --prune
```
- Exit code: `0`
- Result: completed, but no remotes were configured so no remote refs were updated.

```bash
git branch -r
```
- Exit code: `0`
- Output: *(empty)*
- Result: no remote-tracking branches exist.

```bash
git remote -v
```
- Exit code: `0`
- Output: *(empty)*
- Result: `origin` is undefined, so `origin/main` presence cannot be evaluated.

### Fail-closed branch decision table
- `origin` undefined -> **block** step (2) and step (3).
- `origin` defined and `origin/main` exists -> run step (2) exactly.
- `origin` defined and `origin/main` missing, baseline SHA approved, and admin authority available -> run step (3).
- Missing any prerequisite -> no branch publication or protection mutation occurs.

### Required branch protection profile for `main`
Apply immediately after initial `main` push and before merge traffic is enabled:

1. **Pull request reviews (required)**
   - Require at least `2` approving reviews.
   - Dismiss stale approvals on new commits.
   - Require review from code owners.
   - Block self-approval by the PR author.

2. **Required status checks (strict)**
   - Require branches to be up to date before merge.
   - Required checks (minimum):
     - `ci / test`
     - `ci / lint`
     - `ci / build`
     - `governance / traceability-gate`
   - Do not allow bypass by non-admin roles.

3. **History and merge strategy controls**
   - Require linear history.
   - Disallow force-pushes.
   - Disallow branch deletions.
   - Restrict merge methods to the approved strategy (squash or merge-commit, pick one per repo policy).

4. **Promotion integrity controls**
   - Require signed commits (if org policy supports signing enforcement).
   - Restrict who can push to `main` (automation plus designated maintainers only).
   - Require successful conversation resolution before merge.

### Gate conditions and blocking criteria
- **Artifact Contract Live**
  - Condition: branch/ruleset definition committed in governance docs.
  - Evidence: this document plus provider-side ruleset export.
  - Blocks promotion if missing.
- **Execution Integrity Live**
  - Condition: push and protection operations executed by authorized identity.
  - Evidence: provider audit log entries and command receipts.
  - Blocks promotion on unknown actor or missing audit trail.
- **Runtime/Service Authority Live**
  - Condition: required CI checks are wired and runnable on PR events.
  - Evidence: workflow run IDs for each required check.
  - Blocks promotion if any required check is absent or non-reporting.
- **Orchestration Live**
  - Condition: merge path only through protected PR flow.
  - Evidence: disabled direct pushes and validated protection settings.
  - Blocks promotion if direct push path remains open.
- **Traceability Complete**
  - Condition: instruction -> execution -> receipt chain is queryable.
  - Evidence: audit log entry, CI links, merge commit metadata.
  - Blocks promotion if chain cannot be reconstructed.

### Deterministic command set once prerequisites exist
```bash
# Preconditions: origin configured, baseline SHA approved, admin token available.
git fetch --all --prune

if git ls-remote --heads origin main | grep -q 'refs/heads/main'; then
  git checkout -B main --track origin/main
else
  git checkout -B main <baseline-sha>
  git push -u origin main
  # Apply branch protection via provider API or IaC ruleset toolchain.
fi
```

