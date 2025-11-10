
.PHONY: agent-bootstrap agent-plan agent-sprint agent-logs
agent-bootstrap:
	bash mortgage-agents/scripts/bootstrap.sh
agent-plan:
	python3 mortgage-agents/runner/orchestrator.py plan
agent-sprint:
	PHASE?=phase1
	bash mortgage-agents/scripts/run_sprint.sh $(PHASE)
agent-logs:
	@echo 'Logs in mortgage-agents/out/'
