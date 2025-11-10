#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
source mortgage-agents/scripts/git_helpers.sh

ensure_clean_git
mkdir -p mortgage-agents/out logs

commit_snapshot_if_needed
branch=$(create_agent_branch)
echo "Created agent branch: $branch"

mkdir -p mortgage-agents/out/plans mortgage-agents/out/logs mortgage-agents/out/runs
echo "Bootstrap complete. You are now on branch: $branch"
