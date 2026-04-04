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

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    printf 'ERROR: required command not found: %s\n' "$cmd" >&2
    exit 1
  }
}

validate_list_state() {
  local state="$1"
  case "$state" in
    open|closed|all) ;;
    *)
      printf 'ERROR: invalid list state: %s (expected: open|closed|all)\n' "$state" >&2
      exit 1
      ;;
  esac
}

validate_merge_method() {
  local method="$1"
  case "$method" in
    merge|squash|rebase) ;;
    *)
      printf 'ERROR: invalid merge method: %s (expected: merge|squash|rebase)\n' "$method" >&2
      exit 1
      ;;
  esac
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
  require_cmd curl
  require_cmd jq
  require_env GITHUB_TOKEN
  require_env REPO_SLUG

  local action="${1:-}"
  case "$action" in
    list)
      local state="${2:-open}"
      validate_list_state "$state"
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
      local payload
      payload="$(jq -cn --arg event "$event" --arg body "$body" '{event: $event, body: $body}')"
      api POST "/pulls/${pr_number}/reviews" "$payload" | jq '{id, state, body}'
      ;;
    merge)
      local pr_number="${2:-}"
      local method="${3:-squash}"
      [[ -n "$pr_number" ]] || { usage; exit 1; }
      validate_merge_method "$method"
      local payload
      payload="$(jq -cn --arg merge_method "$method" '{merge_method: $merge_method}')"
      api PUT "/pulls/${pr_number}/merge" "$payload" | jq '{merged, message, sha}'
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
