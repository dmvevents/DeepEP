#!/usr/bin/env bash
set -euo pipefail
echo "[agent] running light checks..."

if command -v python3 >/dev/null 2>&1; then
  if test -f manage.py; then
    (python3 manage.py check --deploy || true)
  fi
fi

if test -f package.json; then
  if command -v npm >/dev/null 2>&1; then
    (npm run -s typecheck || true)
    (npm run -s lint || true)
    (npm run -s build || true)
  fi
fi

echo "[agent] checks done."
