#!/usr/bin/env bash
set -euo pipefail
PHASE="${1:-phase1}"
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
echo "[agent] Running sprint for ${PHASE}..."
python3 mortgage-agents/runner/orchestrator.py run --phase "${PHASE}"
echo "[agent] Sprint run finished for ${PHASE}."
