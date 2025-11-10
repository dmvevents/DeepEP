#!/usr/bin/env bash
set -euo pipefail
if pgrep -fa "claude" >/dev/null 2>&1; then
  echo "Killing running Claude CLI processes..."
  pkill -f claude || true
else
  echo "No Claude CLI processes found."
fi
