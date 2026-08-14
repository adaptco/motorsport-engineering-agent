---
name: github-pr-lifecycle
description: Standardize pull-request lifecycle operations, including normalized review updates and evidence-backed squash-merge readiness.
contract_version: "1.0"
policy_scope: write
source_of_truth:
  - scripts/github_pr_lifecycle.sh
  - scripts/github_pr_api.sh
---

# GitHub PR Lifecycle

## Required flow
1. Create or update PR.
2. Run `scripts/github_pr_lifecycle.sh normalize <pr_number> v3.8`.
3. Run review follow-up via `scripts/github_pr_api.sh post-yeet-followup <pr_number> "<test command>"`.
4. Resolve review conversations and re-run checks.
5. Merge with squash strategy when checks are green.

## Guardrails
- Do not merge while any required check is failing.
- Do not close review actions without evidence paths and test output.
- Use repo slug from `REPO_SLUG` or `gh repo view`.
