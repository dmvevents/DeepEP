# autopm/ — Autonomous Product & Engineering Agent System

Drop this folder **autopm/** into the root of your repo (e.g., `/Users/antonalexander/Github/real_estate_app`), then run:

```bash
# 1) (Optional) create/activate a venv
python3.11 -m venv .venv && source .venv/bin/activate

# 2) install deps
pip install -r autopm/requirements.txt

# 3) run a dry-run planning pass (no commits yet)
python autopm/scripts/run_agents.py --plan

# 4) generate critiques & concrete tasks, then open PR branches with commits (requires clean git)
python autopm/scripts/run_agents.py --execute

# Extra: live file-watcher mode (auto-runs personas on changes; careful in big repos)
python autopm/scripts/run_agents.py --watch
```

**LLM keys:** set one or both:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

**Git author lock:** Commits are forced to author **Anton Alexander** using your local git email. See `autopm/scripts/git_author.py`.

---

## What this does

- Spins up **multi-persona agents** (PM, UI/UX, React, Django, Owner, QA) with **role prompts** in `autopm/personas/`.
- Consumes your **roadmap & acceptance criteria** in `autopm/backlog/` and the **product brief** in `autopm/brief/`.
- Generates a **Jira-style plan** + **story checklists** → writes to `autopm/out/plan.*`.
- Produces **concrete code tasks** and **review notes** → commits to feature branches under `autopm/branches.yaml`.
- Enforces **security/compliance gates** (PII at rest, audit events) via checklists in `autopm/compliance/`.
- Leaves a paper trail in `autopm/out/` and `git` (branches + commit messages).

> Tip: keep your existing Claude Code or local agents running — this tool talks to APIs and your local git; it doesn't hijack your Claude session.

---

## Safety & Idempotence

- **Read-only planning** with `--plan` (no file writes outside `autopm/out/`).
- **Transactional writes** with `--execute`: creates a git branch per epic, writes code/doc stubs via Jinja templates, runs formatters, then **commits with author pinned to Anton Alexander**.
- **No destructive ops**: will refuse to run if there are uncommitted changes (`git status` dirty).

---

## Configuration

Edit `autopm/config.yaml`:
- `repo_root`: set to `..` if `autopm/` is nested at repo root (default).
- `model_provider`: `anthropic` or `openai`; `model`: e.g., `claude-3-7-sonnet` or `gpt-4.1-mini`.
- `branch_prefix`: e.g., `autopm/phase1-`.
- `personas`: enable/disable roles and weights.

---

## Outputs

- `autopm/out/plan.md` and `plan.json`
- `autopm/out/critiques/*.md` (per persona)
- `autopm/out/tasks/*.yaml` (machine-actionable task sets)
- Git branches with templated code/docs & checklists

---

## Uninstall

Delete the `autopm/` folder and remove any branches matching `branch_prefix`.
