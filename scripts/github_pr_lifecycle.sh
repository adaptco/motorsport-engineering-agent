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
    version_tag defaults to v3.8.

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

detect_gh_cmd() {
  if [[ -n "${GH_CMD:-}" ]]; then
    echo "${GH_CMD}"
    return
  fi
  if command -v gh >/dev/null 2>&1; then
    echo "gh"
    return
  fi
  if command -v gh.exe >/dev/null 2>&1; then
    echo "gh.exe"
    return
  fi
  if [[ -x "/c/Program Files/GitHub CLI/gh.exe" ]]; then
    echo "/c/Program Files/GitHub CLI/gh.exe"
    return
  fi
  echo "ERROR: required command not found: gh" >&2
  exit 1
}

repo_slug() {
  local gh_cmd="$1"
  if [[ -n "${REPO_SLUG:-}" ]]; then
    echo "${REPO_SLUG}"
    return
  fi
  "$gh_cmd" repo view --json nameWithOwner -q .nameWithOwner
}

ensure_auth() {
  local gh_cmd="$1"
  "$gh_cmd" auth status >/dev/null 2>&1 || {
    echo "ERROR: gh is not authenticated. Run: gh auth login" >&2
    exit 1
  }
}

ensure_label() {
  local gh_cmd="$1"
  local repo="$2"
  local label="$3"
  if ! "$gh_cmd" label list --repo "$repo" --search "$label" --json name -q ".[].name" | grep -Fxq "$label"; then
    "$gh_cmd" label create "$label" --repo "$repo" --color "1D76DB" --description "Automated lifecycle version tag"
  fi
}

normalize_pr() {
  local gh_cmd="$1"
  local pr_number="$2"
  local version_tag="${3:-v3.8}"
  local repo
  repo="$(repo_slug "$gh_cmd")"

  ensure_label "$gh_cmd" "$repo" "$version_tag"
  "$gh_cmd" pr edit "$pr_number" --repo "$repo" --add-label "$version_tag"

  local body
  body="$(cat <<EOF
### Automated PR Lifecycle Update
- Version normalization tag applied: \`$version_tag\`
- Workflow checks should be green before merge
- Review follow-up uses \`scripts/github_pr_api.sh post-yeet-followup\`
- Merge policy: squash merge after review threads are resolved
EOF
)"
  "$gh_cmd" pr comment "$pr_number" --repo "$repo" --body "$body"

  echo "normalized_pr=$pr_number repo=$repo label=$version_tag"
}

bulk_tag() {
  local gh_cmd="$1"
  local label="$2"
  local state="${3:-open}"
  local limit="${PR_BULK_LIMIT:-200}"
  local repo
  repo="$(repo_slug "$gh_cmd")"
  ensure_label "$gh_cmd" "$repo" "$label"

  "$gh_cmd" pr list --repo "$repo" --state "$state" --limit "$limit" --json number | jq -r '.[].number' | while read -r pr; do
    [[ -n "$pr" ]] || continue
    "$gh_cmd" pr edit "$pr" --repo "$repo" --add-label "$label" >/dev/null
    echo "tagged_pr=$pr label=$label"
  done
}

main() {
  require_cmd jq
  local gh_cmd
  gh_cmd="$(detect_gh_cmd)"
  ensure_auth "$gh_cmd"

  local cmd="${1:-}"
  case "$cmd" in
    normalize)
      local pr_number="${2:-}"
      local version_tag="${3:-v3.8}"
      [[ -n "$pr_number" ]] || { usage; exit 1; }
      normalize_pr "$gh_cmd" "$pr_number" "$version_tag"
      ;;
    bulk-tag)
      local label="${2:-}"
      local state="${3:-open}"
      [[ -n "$label" ]] || { usage; exit 1; }
      bulk_tag "$gh_cmd" "$label" "$state"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
