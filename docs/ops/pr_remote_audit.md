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
