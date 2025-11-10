
import os, sys, subprocess, shlex, tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Local helpers
from autopm.scripts.llm import LLM
from autopm.scripts.git_author import ensure_author, git_clean

ROOT = Path(__file__).resolve().parents[2]  # repo root
AUTOPM = ROOT / "autopm"
OUT = AUTOPM / "out"
TASKS_YAML = OUT / "tasks" / "tasks.yaml"

def load_yaml(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run(cmd: str, check=True, env=None, cwd=None) -> subprocess.CompletedProcess:
    print(f"➜ {cmd}")
    return subprocess.run(shlex.split(cmd), check=check, env=env, cwd=cwd)

def gh_available() -> bool:
    try:
        subprocess.check_output(["gh","--version"])
        return True
    except Exception:
        return False

def read_config() -> Dict[str, Any]:
    cfg = load_yaml(AUTOPM/"config.yaml")
    if cfg.get("model_provider") == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        if os.getenv("OPENAI_API_KEY"):
            cfg["model_provider"] = "openai"
            cfg["model"] = "gpt-4.1-mini"
        else:
            print("ERROR: No LLM API key. Export ANTHROPIC_API_KEY or OPENAI_API_KEY.")
            sys.exit(2)
    return cfg

PROMPT_SYSTEM = (
    "You are a senior staff engineer. Output ONLY a unified diff (patch) rooted at the repo root. "
    "All paths must be correct. Keep changes minimal and compilable. No commentary."
)

def build_user_prompt(task: Dict[str, Any], plan_md: str, contracts: str, security: str) -> str:
    import yaml as _y
    return f"""
Context:
- Task (YAML):
```yaml
{_y.safe_dump(task, sort_keys=False)}
```

- Acceptance criteria are mandatory. Respect security gates (PII at rest; AuditEvent) when relevant.

Artifacts:
- Plan.md (excerpt):
```
{plan_md[:6000]}
```

- Data contracts:
```
{contracts}
```

- Security checklist:
```
{security}
```

Instruction:
Generate a SINGLE unified diff patch rooted at the repository root to implement ONLY this task.
If the task owner is "react"/"uiux", edit files under frontend-react (React 19 + TS + Router 7 + MUI preferred but keep minimal).
If owner is "django"/"backend", edit files under backend (Django + DRF), including models, serializers, viewsets, urls, migrations.
Add just enough code to compile and pass basic import/build/test.

Patch rules:
- Use correct relative paths from repo root.
- Include file adds/updates/removals as needed.
- Keep diffs small and self-contained.
- No prose, ONLY the unified diff.
"""

def apply_patch(patch_text: str) -> bool:
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".patch") as tf:
        tf.write(patch_text)
        tf.flush()
        patch_path = tf.name
    try:
        run(f"git apply -p0 --3way --index {patch_path}")
        return True
    except subprocess.CalledProcessError:
        print("git apply failed; saving patch to autopm/out/diffs/ and continuing.")
        diffs_dir = OUT / "diffs"
        diffs_dir.mkdir(parents=True, exist_ok=True)
        from pathlib import Path as _P
        _P(patch_path).rename(diffs_dir / (_P(patch_path).name))
        return False

def detect_commands(paths: List[str]) -> List[str]:
    cmds: List[str] = []
    if any(p.startswith("frontend-react/") for p in paths):
        cmds += [
            "npm --prefix frontend-react install",
            "npm --prefix frontend-react run build"
        ]
    if any(p.startswith("backend/") for p in paths):
        cmds += [
            "python manage.py makemigrations --check --dry-run || true",
            "pytest -q || true"
        ]
    return cmds

def files_from_patch(patch_text: str) -> List[str]:
    files: List[str] = []
    for line in patch_text.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            part = line.split()
            if len(part) >= 2:
                p = part[1]
                if p.startswith(("a/","b/")):
                    p = p[2:]
                if p and p != "/dev/null":
                    files.append(p)
    return sorted(set(files))

def open_pr(branch: str, title: str, body: str) -> Optional[str]:
    if not gh_available():
        print("gh CLI not available; skipping PR creation.")
        return None
    try:
        out = subprocess.check_output(
            ["gh","pr","create","--fill","--title",title,"--body",body,"--base","master","--head",branch],
            text=True
        ).strip()
        print(out)
        return out
    except subprocess.CalledProcessError as e:
        print("gh pr create failed:", e)
        return None

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", help="Filter to tasks whose id/title begins with this epic key (e.g. PHASE1)", default=None)
    ap.add_argument("--owner", help="Filter by owner (react,django,uiux,qa,pm)", default=None)
    ap.add_argument("--limit", type=int, default=3, help="Max tasks to attempt this run")
    ap.add_argument("--push", action="store_true", help="Push branches to origin after commit")
    ap.add_argument("--pr", action="store_true", help="Open PRs via GitHub CLI (gh)")
    ap.add_argument("--merge", action="store_true", help="Auto-merge PRs after open (requires protection rules satisfied)")
    ap.add_argument("--yes", action="store_true", help="No confirmations; apply, commit, continue")
    args = ap.parse_args()

    ensure_author()

    cfg = read_config()
    llm = LLM(cfg["model_provider"], cfg["model"], cfg.get("temperature",0.2), cfg.get("max_output_tokens",3000))

    if not TASKS_YAML.exists():
        print("No tasks found at autopm/out/tasks/tasks.yaml. Run --plan first.")
        sys.exit(1)

    tasks_raw = load_yaml(TASKS_YAML)

    task_items: List[Dict[str,Any]] = []
    if isinstance(tasks_raw, dict) and "tasks" in tasks_raw:
        task_items = tasks_raw["tasks"]
    elif isinstance(tasks_raw, list):
        task_items = tasks_raw
    else:
        for v in tasks_raw.values() if isinstance(tasks_raw, dict) else []:
            if isinstance(v, list):
                task_items.extend(v)

    def matches(t: Dict[str,Any]) -> bool:
        if args.epic and args.epic not in (t.get("id","") + t.get("title","")):
            return False
        if args.owner and args.owner != t.get("owner"):
            return False
        return True

    filtered = [t for t in task_items if matches(t)]
    if not filtered:
        print("No tasks matched your filters.")
        sys.exit(0)
    filtered = filtered[:args.limit]

    plan_md = (OUT/"plan.md").read_text(encoding="utf-8") if (OUT/"plan.md").exists() else ""
    contracts = (AUTOPM/"contracts"/"contracts.yaml").read_text(encoding="utf-8")
    security = (AUTOPM/"compliance"/"SECURITY_CHECKLIST.md").read_text(encoding="utf-8")

    if not git_clean():
        print("Repo is dirty. Commit or stash first.")
        sys.exit(2)

    bprefix = cfg.get("branch_prefix","autopm/")

    for t in filtered:
        tid = str(t.get("id") or t.get("title","untitled")).lower().replace(" ","-").replace("/","-")
        epic_key = (t.get("epic") or t.get("id","")).split(":")[0] if t.get("id") else None

        # Find a base branch for the epic; else master
        branches = subprocess.check_output(["git","branch","--list"], text=True).splitlines()
        base_branch = "master"
        if epic_key:
            for b in branches:
                name = b.strip().lstrip("* ").strip()
                if name.startswith(bprefix) and epic_key in name:
                    base_branch = name
                    break

        task_branch = f"{bprefix}{(epic_key or 'TASK')}-task-{tid[:32]}"
        run(f"git checkout {base_branch}")
        rc = subprocess.call(["git","rev-parse","--verify","--quiet",task_branch])
        if rc != 0:
            run(f"git checkout -b {task_branch}")
        else:
            run(f"git checkout {task_branch}")

        # Ask LLM for patch
        user = build_user_prompt(t, plan_md, contracts, security)
        print(f"\n🧠 Generating patch for task: {t.get('title','(no title)')}")
        patch_text = llm.complete(PROMPT_SYSTEM, user).strip()

        ok = apply_patch(patch_text)
        if not ok:
            print("Patch failed to apply cleanly. Saved to autopm/out/diffs/.")
            if not args.yes:
                try:
                    inp = input("Continue to next task? [Y/n] ").strip().lower()
                except EOFError:
                    inp = "y"
                if inp == "n":
                    sys.exit(3)
            continue

        changed = files_from_patch(patch_text)
        for c in detect_commands(changed):
            try:
                run(c, check=False)
            except Exception:
                pass

        run(f'git commit -m "{t.get("id","TASK")}: {t.get("title","apply patch")}"')

        if args.push:
            run(f"git push -u origin {task_branch}", check=False)
        if args.pr and gh_available():
            title = f"{t.get('id','TASK')}: {t.get('title','')}".strip()
            try:
                out = subprocess.check_output(
                    ["gh","pr","create","--fill","--title",title,"--body",f"Automated by autopm autopilot for task {t.get('id')}","--base","master","--head",task_branch],
                    text=True
                ).strip()
                print(out)
                if args.merge:
                    subprocess.run(["gh","pr","merge","--auto","--squash",out], check=False)
            except subprocess.CalledProcessError as e:
                print("gh pr create failed:", e)

    print("\n✅ Autopilot run complete.")

if __name__ == "__main__":
    main()
