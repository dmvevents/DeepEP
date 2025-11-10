#!/usr/bin/env python3
import os, sys, json, yaml, time, subprocess, argparse
from typing import Dict, Any
from claude_helpers import call_claude

def repo_root() -> str:
    proc = subprocess.run(["bash","-lc","git rev-parse --show-toplevel"], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else os.getcwd()

REPO_ROOT = repo_root()
AGENT_ROOT = os.path.join(REPO_ROOT, "mortgage-agents")
OUT_DIR = os.path.join(AGENT_ROOT, "out")
PLANS_DIR = os.path.join(OUT_DIR, "plans")
RUNS_DIR = os.path.join(OUT_DIR, "runs")
LOGS_DIR = os.path.join(OUT_DIR, "logs")

os.makedirs(PLANS_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def read_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def git_status() -> str:
    return subprocess.run(["bash","-lc","git status --porcelain"], capture_output=True, text=True).stdout.strip()

def git_commit(msg: str):
    name = subprocess.run(["bash","-lc","git config user.name"], capture_output=True, text=True).stdout.strip()
    email = subprocess.run(["bash","-lc","git config user.email"], capture_output=True, text=True).stdout.strip()
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": name or "Anton Alexander",
        "GIT_AUTHOR_EMAIL": email or "anton@example.com",
        "GIT_COMMITTER_NAME": name or "Anton Alexander",
        "GIT_COMMITTER_EMAIL": email or "anton@example.com",
    })
    subprocess.run(["bash","-lc","git add -A"], check=True, env=env)
    subprocess.run(["bash","-lc",f"git commit -m {json.dumps(msg)} || true"], check=False, env=env)

def run_checks():
    subprocess.run(["bash","-lc","bash mortgage-agents/scripts/test_checks.sh"], check=False)

def persona_prompt(persona: str, phase: str, task: Dict[str, Any]) -> str:
    prompts_dir = os.path.join(AGENT_ROOT, "prompts")
    system_file = {
        "pm": "SYSTEM_PM.md",
        "frontend": "SYSTEM_DEV_FRONTEND.md",
        "backend": "SYSTEM_DEV_BACKEND.md",
        "ux": "SYSTEM_UX.md",
        "compliance": "SYSTEM_COMPLIANCE.md",
        "owner": "SYSTEM_OWNER.md",
        "critic": "CRITIC.md",
    }.get(persona, "SYSTEM_DEV_BACKEND.md")
    system_path = os.path.join(prompts_dir, system_file)

    with open(system_path, "r", encoding="utf-8") as f:
        system_text = f.read()

    pm_ctx_path = os.path.join(AGENT_ROOT, "context", "pm_roadmap.md")
    system_text += f"""

# Context files to open with the Read tool (DO NOT paste, just read from disk)
- {pm_ctx_path}
- PROJECTSTATUSREPORT.md (if present at repo root)
- ENHANCEDTAXDATA_SCHEMA.md (if present)
- IMPLEMENTATION_SUMMARY.md (if present)
- README.md or docs/* (if present)

# Task
Phase: {phase}
Epic: {task.get('epic','')}
Story: {task.get('story','')}
Acceptance Criteria:
{task.get('acceptance','')}

# Instructions
- Use Read/Grep/Glob tools to inspect the repo and above context files.
- Make the minimal, production-ready edits to satisfy the acceptance criteria.
- Write or adjust tests if obvious.
- Keep code idiomatic (Django/DRF/React/MUI) and production-safe (PII, RBAC).
- After edits, run lightweight self-checks (npm build/typecheck; manage.py check).
- Summarize what changed in <=12 lines.
"""
    return system_text

def ensure_plan(phase: str) -> Dict[str, Any]:
    plan_path = os.path.join(PLANS_DIR, f"{phase}_plan.json")
    if os.path.exists(plan_path):
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f)

    seed_path = os.path.join(AGENT_ROOT, "backlog", f"seed_{phase}.yaml")
    if not os.path.exists(seed_path):
        raise FileNotFoundError(f"Missing backlog seed: {seed_path}")
    seed = read_yaml(seed_path)

    pm_prompt = open(os.path.join(AGENT_ROOT, "prompts", "SYSTEM_PM.md"), "r", encoding="utf-8").read()
    pm_prompt += f"""

# Task
Refine the following backlog for Phase: {phase}. Produce a compact JSON plan with an array 'tasks', each with:
- id (short slug)
- epic
- story
- acceptance (3-6 bullets)
- persona (backend|frontend|ux|compliance|owner)
- estimate_hours (int)
- priority (1-5)

Backlog seed YAML to read from disk: {seed_path}

IMPORTANT:
- Save output in strict JSON only. No prose. No markdown.
- Keep 6-12 tasks.
"""
    out_file = os.path.join(LOGS_DIR, f"plan_{phase}_{int(time.time())}.log")
    result = call_claude(pm_prompt, cwd=REPO_ROOT, output_file=out_file)
    try:
        plan = json.loads(result)
    except Exception:
        plan = {"tasks": seed.get("tasks", [])}

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    return plan

def run_phase(phase: str):
    plan = ensure_plan(phase)
    tasks = plan.get("tasks", [])
    for i, task in enumerate(tasks, 1):
        persona = task.get("persona") or "backend"
        prompt = persona_prompt(persona, phase, task)
        log_path = os.path.join(LOGS_DIR, f"{phase}_{persona}_{task.get('id','task')}_{int(time.time())}.log")
        print(f"[agent] ({i}/{len(tasks)}) {persona} → {task.get('id','task')}")
        try:
            _ = call_claude(prompt, cwd=REPO_ROOT, output_file=log_path)
            if git_status():
                msg = f"{task.get('commit_prefix','feat')}: {persona}: {task.get('story','task')}"
                git_commit(msg)
            run_checks()
        except Exception as e:
            errfile = os.path.join(LOGS_DIR, f"ERR_{phase}_{persona}_{task.get('id','task')}.log")
            with open(errfile, "w", encoding="utf-8") as f:
                f.write(str(e))
            print(f"[agent] ERROR on task {task.get('id')}: {e}")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Create/refresh the JSON plan for PHASE (env or arg).")
    p_plan.add_argument("--phase", default=os.environ.get("PHASE","phase1"))

    p_run = sub.add_parser("run", help="Execute a phase backlog via personas.")
    p_run.add_argument("--phase", required=True)

    args = ap.parse_args()
    if args.cmd == "plan":
        plan = ensure_plan(args.phase)
        out = os.path.join(PLANS_DIR, f"{args.phase}_plan.json")
        print(f"[agent] Wrote plan to {out} with {len(plan.get('tasks',[]))} tasks.")
    elif args.cmd == "run":
        run_phase(args.phase)

if __name__ == "__main__":
    main()
