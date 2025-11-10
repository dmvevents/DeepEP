#!/usr/bin/env bash
set -euo pipefail

ensure_clean_git() {
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Not a git repository. Please run inside your repo." >&2
    exit 1
  fi
}

current_branch() {
  git rev-parse --abbrev-ref HEAD
}

create_agent_branch() {
  local ts="$(date +%Y%m%d-%H%M%S)"
  local branch="agent/autopm-${ts}"
  git checkout -b "$branch"
  echo "$branch"
}

commit_snapshot_if_needed() {
  if [[ -n "$(git status --porcelain)" ]]; then
    local name="$(git config user.name || true)"
    local email="$(git config user.email || true)"
    if [[ -z "$name" || -z "$email" ]]; then
      echo "Git user.name or user.email not set. Please configure git." >&2
      exit 1
    fi
    GIT_AUTHOR_NAME="$name" GIT_AUTHOR_EMAIL="$email"     GIT_COMMITTER_NAME="$name" GIT_COMMITTER_EMAIL="$email"     git add -A
    git commit -m "chore(agent): snapshot before autonomous agent run"
  fi
}

commit_if_changes() {
  if [[ -n "$(git status --porcelain)" ]]; then
    local msg="${1:-chore(agent): checkpoint}"
    local name="$(git config user.name)"
    local email="$(git config user.email)"
    GIT_AUTHOR_NAME="$name" GIT_AUTHOR_EMAIL="$email"     GIT_COMMITTER_NAME="$name" GIT_COMMITTER_EMAIL="$email"     git add -A
    git commit -m "$msg"
  fi
}
