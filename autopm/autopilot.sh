
#!/usr/bin/env bash
set -euo pipefail

export GIT_AUTHOR_NAME="Anton Alexander"
export GIT_COMMITTER_NAME="Anton Alexander"
# email comes from your local git config (git config user.email)

# Ensure planning artifacts exist (safe; writes to autopm/out/)
python -m autopm.scripts.run_agents --plan

# Run autopilot with any flags passed through
python -m autopm.scripts.autopilot "$@"
