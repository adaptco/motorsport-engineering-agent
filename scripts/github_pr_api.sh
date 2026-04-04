#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/github_pr_api.sh list [state]
  scripts/github_pr_api.sh review <pr_number> <approve|comment|request_changes> [body]
  scripts/github_pr_api.sh merge <pr_number> [merge_method]
  scripts/github_pr_api.sh close <pr_number>

Required environment:
  GITHUB_TOKEN   Fine-grained PAT or GitHub App token with pull-request permissions.
  REPO_SLUG      Repository slug in org/repo format.
USAGE
}

require_env() {
  local key="$1"
  [[ -n "${!key:-}" ]] || {
    printf 'ERROR: %s is required\n' "$key" >&2
    exit 1
  }
}

api() {
  local method="$1"
  local path="$2"
  local data="${3:-}"

  if [[ -n "$data" ]]; then
    curl -fsSL -X "$method" \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${REPO_SLUG}${path}" \
      -d "$data"
  else
    curl -fsSL -X "$method" \
      -H "Authorization: Bearer ${GITHUB_TOKEN}" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/${REPO_SLUG}${path}"
  fi
}

main() {
  require_env GITHUB_TOKEN
  require_env REPO_SLUG

  local action="${1:-}"
  case "$action" in
    list)
      local state="${2:-open}"
      api GET "/pulls?state=${state}&per_page=100" | jq '.[] | {number, title, state, head: .head.ref, base: .base.ref}'
      ;;
    review)
      local pr_number="${2:-}"
      local event="${3:-}"
      local body="${4:-Automated review via API script.}"
      [[ -n "$pr_number" && -n "$event" ]] || { usage; exit 1; }
      case "$event" in
        approve) event="APPROVE" ;;
        comment) event="COMMENT" ;;
        request_changes) event="REQUEST_CHANGES" ;;
        *) printf 'ERROR: invalid review event\n' >&2; exit 1 ;;
      esac
      api POST "/pulls/${pr_number}/reviews" "{\"event\":\"${event}\",\"body\":\"${body}\"}" | jq '{id, state, body}'
      ;;
    merge)
      local pr_number="${2:-}"
      local method="${3:-squash}"
      [[ -n "$pr_number" ]] || { usage; exit 1; }
      api PUT "/pulls/${pr_number}/merge" "{\"merge_method\":\"${method}\"}" | jq '{merged, message, sha}'
      ;;
    close)
      local pr_number="${2:-}"
      [[ -n "$pr_number" ]] || { usage; exit 1; }
      api PATCH "/pulls/${pr_number}" '{"state":"closed"}' | jq '{number, state, title}'
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
