#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/github_pr_lifecycle.sh normalize <pr_number> [version_tag]
  scripts/github_pr_lifecycle.sh bulk-tag <tag> [state]

Commands:
  normalize
    Add a version tag label and post a standardized lifecycle comment on one PR.
    version_tag defaults to v3.6.3.

  bulk-tag
    Apply a label to all pull requests in the requested state.
    state defaults to open.

Requirements:
  - gh CLI authenticated for the target repository.
  - jq installed.
  - Run from repository root or set REPO_SLUG.
USAGE
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "ERROR: required command not found: $cmd" >&2
    exit 1
  }
}

repo_slug() {
  if [[ -n "${REPO_SLUG:-}" ]]; then
    echo "${REPO_SLUG}"
    return
  fi
  gh repo view --json nameWithOwner -q .nameWithOwner
}

ensure_auth() {
  gh auth status >/dev/null 2>&1 || {
    echo "ERROR: gh is not authenticated. Run: gh auth login" >&2
    exit 1
  }
}

ensure_label() {
  local repo="$1"
  local label="$2"
  if ! gh label list --repo "$repo" --search "$label" --json name -q ".[].name" | grep -Fxq "$label"; then
    gh label create "$label" --repo "$repo" --color "1D76DB" --description "Automated lifecycle version tag"
  fi
}

normalize_pr() {
  local pr_number="$1"
  local version_tag="${2:-v3.6.3}"
  local repo
  repo="$(repo_slug)"

  ensure_label "$repo" "$version_tag"
  gh pr edit "$pr_number" --repo "$repo" --add-label "$version_tag"

  local body
  body="$(cat <<EOF
### Automated PR Lifecycle Update
- Version normalization tag applied: \`$version_tag\`
- Workflow checks should be green before merge
- Review follow-up uses \`scripts/github_pr_api.sh post-yeet-followup\`
- Merge policy: squash merge after review threads are resolved
EOF
)"
  gh pr comment "$pr_number" --repo "$repo" --body "$body"

  echo "normalized_pr=$pr_number repo=$repo label=$version_tag"
}

bulk_tag() {
  local label="$1"
  local state="${2:-open}"
  local repo
  repo="$(repo_slug)"
  ensure_label "$repo" "$label"

  gh pr list --repo "$repo" --state "$state" --limit 200 --json number | jq -r '.[].number' | while read -r pr; do
    [[ -n "$pr" ]] || continue
    gh pr edit "$pr" --repo "$repo" --add-label "$label" >/dev/null
    echo "tagged_pr=$pr label=$label"
  done
}

main() {
  require_cmd gh
  require_cmd jq
  ensure_auth

  local cmd="${1:-}"
  case "$cmd" in
    normalize)
      local pr_number="${2:-}"
      local version_tag="${3:-v3.6.3}"
      [[ -n "$pr_number" ]] || { usage; exit 1; }
      normalize_pr "$pr_number" "$version_tag"
      ;;
    bulk-tag)
      local label="${2:-}"
      local state="${3:-open}"
      [[ -n "$label" ]] || { usage; exit 1; }
      bulk_tag "$label" "$state"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
