# GitHub PR Operator Runbook (Fail-Closed)

## Scope
This runbook defines the exact operator commands for secure pull-request operations with `gh`, plus an API-script fallback.

## 0) One-time tool install (Ubuntu/Debian)
```bash
apt-get update
apt-get install -y gh jq
gh --version
jq --version
```

## 1) Authentication (least privilege)
Use a **fine-grained PAT** scoped only to the target repository with minimum permissions:
- Pull requests: Read and write
- Contents: Read
- Metadata: Read

Export token for current shell:
```bash
export GITHUB_TOKEN='<fine_grained_pat>'
```

Log in with token (non-interactive) and verify:
```bash
gh auth login --hostname github.com --with-token < <(printf '%s' "$GITHUB_TOKEN")
gh auth status
```

## 2) Preflight gate (required)
Run before any PR operation. This gate fails closed if any required condition is missing.
```bash
scripts/pr_preflight.sh
```

Validated conditions:
1. `git` installed
2. `gh` installed
3. `jq` installed
4. `gh` authenticated
5. `origin` remote configured
6. `origin` reachable
7. `origin/main` exists

## 3) PR operations via GitHub CLI
### List PRs
```bash
gh pr list --state open --limit 100
gh pr list --state all --limit 100
```

### Review PR
```bash
gh pr review <pr-number> --approve --body 'Approved after verification.'
gh pr review <pr-number> --request-changes --body 'Blocking issues found.'
gh pr review <pr-number> --comment --body 'Non-blocking feedback.'
```

### Merge PR
```bash
gh pr merge <pr-number> --squash --delete-branch
gh pr merge <pr-number> --merge --delete-branch
gh pr merge <pr-number> --rebase --delete-branch
```

### Close PR without merge
```bash
gh pr close <pr-number> --comment 'Closing without merge (reason).'
```

## 4) API fallback (equivalent operations)
If `gh` is unavailable, use `scripts/github_pr_api.sh`.

Required env:
```bash
export GITHUB_TOKEN='<fine_grained_pat_or_app_token>'
export REPO_SLUG='<org>/<repo>'
```

Commands:
```bash
scripts/github_pr_api.sh list open
scripts/github_pr_api.sh review <pr-number> approve 'Approved after verification.'
scripts/github_pr_api.sh merge <pr-number> squash
scripts/github_pr_api.sh close <pr-number>
```

## 5) Governance evidence to capture
For each operation, archive:
- command executed
- UTC timestamp
- exit code
- stdout/stderr
- operator identity (`gh auth status` output)
