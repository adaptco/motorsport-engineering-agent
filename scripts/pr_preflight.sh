#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'PRECHECK_FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'PRECHECK_OK: %s\n' "$1"
}

command -v git >/dev/null 2>&1 || fail "git CLI is not installed"
pass "git CLI detected"

command -v gh >/dev/null 2>&1 || fail "gh CLI is not installed"
pass "gh CLI detected"

if ! gh auth status >/dev/null 2>&1; then
  fail "gh is not authenticated (run: gh auth login --with-token < <(printf '%s' \"\$GITHUB_TOKEN\"))"
fi
pass "gh authentication is valid"

remote_url="$(git remote get-url origin 2>/dev/null || true)"
[[ -n "${remote_url}" ]] || fail "git remote 'origin' is missing"
pass "origin remote configured (${remote_url})"

if ! git ls-remote --heads origin >/dev/null 2>&1; then
  fail "cannot reach origin or lack read permission"
fi
pass "origin is reachable"

if ! git ls-remote --exit-code --heads origin main >/dev/null 2>&1; then
  fail "origin/main branch does not exist"
fi
pass "origin/main exists"

printf 'PRECHECK_OK: all governance preflight checks passed\n'
