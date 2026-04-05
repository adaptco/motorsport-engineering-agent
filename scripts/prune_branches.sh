#!/usr/bin/env bash
set -euo pipefail

# Prune local branches that are not main or current
prune_local() {
  echo "--- Local Branch Pruning ---"
  current_branch=$(git branch --show-current)
  for branch in $(git branch --format="%(refname:short)"); do
    if [[ "$branch" != "main" && "$branch" != "$current_branch" ]]; then
      if [[ "$branch" == codex/* || "$branch" == fix/* ]]; then
        echo "Deleting local branch: $branch"
        git branch -d "$branch" || true
      fi
    fi
  done
}

# Plan for remote pruning based on current refs
plan_remote_prune() {
  echo "--- Remote Branch Pruning Plan ---"
  # List remote branches starting with codex/ or fix/ from current tracking
  for full_branch in $(git branch -r --format="%(refname:short)"); do
    branch=${full_branch#origin/}
    if [[ "$branch" == "main" || "$branch" == "HEAD" || "$branch" == "$full_branch" ]]; then
      continue
    fi

    if [[ "$branch" == codex/* || "$branch" == fix/* ]]; then
      echo "[PROPOSAL] Delete remote branch: origin/$branch"
      # To execute: git push origin --delete "$branch"
    fi
  done
}

main() {
  prune_local
  plan_remote_prune
}

main "$@"
