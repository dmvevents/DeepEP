.PHONY: autopm-install autopm-plan autopm-execute autopm-watch

autopm-install:
	python3.11 -m venv .venv && . .venv/bin/activate && pip install -r autopm/requirements.txt

autopm-plan:
	python autopm/scripts/run_agents.py --plan

autopm-execute:
	python autopm/scripts/run_agents.py --execute

autopm-watch:
	python autopm/scripts/run_agents.py --watch
