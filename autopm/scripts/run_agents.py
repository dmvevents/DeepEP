import os, sys, json, yaml, time, glob, subprocess, textwrap
from pathlib import Path
from rich import print
from autopm.scripts.llm import LLM
from autopm.scripts.git_author import ensure_author, git_clean, git_branch, git_add_all, git_commit

PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parent
AUTOPM = PKG
OUT = AUTOPM / "out"
PERSONAS = AUTOPM / "personas"

def load_yaml(p): 
    with open(p,"r",encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dirs():
    (OUT / "critiques").mkdir(parents=True, exist_ok=True)
    (OUT / "tasks").mkdir(parents=True, exist_ok=True)

def load_config():
    cfg = load_yaml(AUTOPM/"config.yaml")
    return cfg

def pick_provider(cfg):
    pref = cfg["model_provider"]
    if pref == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        if os.getenv("OPENAI_API_KEY"):
            cfg["model_provider"] = "openai"
            cfg["model"] = "gpt-4.1-mini"
        else:
            print("[red]No API keys set. Export ANTHROPIC_API_KEY or OPENAI_API_KEY.[/red]")
            sys.exit(1)
    return cfg

def persona_text(name):
    return Path(PERSONAS/f"{name}.md").read_text(encoding="utf-8")

def brief_text():
    return (ROOT/"autopm/brief/pm_input.md").read_text(encoding="utf-8")

def roadmap_yaml():
    return (ROOT/"autopm/backlog/roadmap.yaml").read_text(encoding="utf-8")

def contracts_text():
    return (ROOT/"autopm/contracts/contracts.yaml").read_text(encoding="utf-8")

def plan(llm):
    system = "You are an expert program manager producing a concrete, minimal, high-signal delivery plan."
    user = f"""Using the roadmap (YAML), data contracts, and brief produce:
- A concise plan table (epics → branches → acceptance keys).
- A JSON backlog with stories (id, title, owner persona, acceptance, files to touch).
Roadmap YAML:
```yaml
{roadmap_yaml()}
```
Contracts:
```
{contracts_text()}
```
Brief:
```
{brief_text()}
```
"""
    content = llm.complete(system, user)
    (OUT/"plan.md").write_text(content, encoding="utf-8")
    # Try to extract JSON block if present
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end>start:
        try:
            js = json.loads(content[start:end+1])
            (OUT/"plan.json").write_text(json.dumps(js, indent=2), encoding="utf-8")
        except Exception:
            pass
    print("[green]Wrote plan to out/plan.md[/green]")

def critique(llm, role):
    system = f"You are {role.upper()} performing a hard-nosed critique with actionable fixes only."
    user = f"""Context:
Roadmap:
```yaml
{roadmap_yaml()}
```
Contracts:
```
{contracts_text()}
```
Output: bullet list of top gaps and concrete changes (files, components, endpoints), no fluff.
"""
    content = llm.complete(system, user)
    (OUT/"critiques"/f"{role}.md").write_text(content, encoding="utf-8")
    print(f"[cyan]Wrote critique for {role}[/cyan]")

def generate_tasks(llm):
    system = "You are a tech lead writing granular, testable tasks that can be executed independently."
    user = f"""Using the plan and critiques, output machine-actionable YAML tasks grouped by epic, with:
- id, title, owner (react/django/uiux/qa/pm), acceptance, changes (paths), tests.
Plan:
```
{(OUT/'plan.md').read_text(encoding='utf-8') if (OUT/'plan.md').exists() else ''}
```
Critiques:
- PM:
{(OUT/'critiques'/'pm.md').read_text(encoding='utf-8') if (OUT/'critiques'/'pm.md').exists() else ''}

- UIUX:
{(OUT/'critiques'/'uiux.md').read_text(encoding='utf-8') if (OUT/'critiques'/'uiux.md').exists() else ''}

- React:
{(OUT/'critiques'/'react.md').read_text(encoding='utf-8') if (OUT/'critiques'/'react.md').exists() else ''}

- Django:
{(OUT/'critiques'/'django.md').read_text(encoding='utf-8') if (OUT/'critiques'/'django.md').exists() else ''}

- Owner:
{(OUT/'critiques'/'owner.md').read_text(encoding='utf-8') if (OUT/'critiques'/'owner.md').exists() else ''}

- QA:
{(OUT/'critiques'/'qa.md').read_text(encoding='utf-8') if (OUT/'critiques'/'qa.md').exists() else ''}
"""
    content = llm.complete(system, user)
    (OUT/"tasks"/"tasks.yaml").write_text(content.replace("```yaml","").replace("```",""), encoding="utf-8")
    print("[magenta]Wrote tasks to out/tasks/tasks.yaml[/magenta]")

def execute_commits(cfg):
    # minimal example: create branches per epic and drop TODO stubs
    import yaml
    epics = yaml.safe_load((ROOT/"autopm/backlog/roadmap.yaml").read_text(encoding="utf-8"))["epics"]
    if not git_clean():
        print("[red]Repo is dirty. Commit or stash changes first.[/red]")
        sys.exit(2)
    ensure_author()
    for epic in epics:
        for br in epic.get("branches", []):
            branch = f"{cfg['branch_prefix']}{epic['key']}-{br}"
            print(f"[bold]Creating branch {branch}[/bold]")
            subprocess.check_call(["git","checkout","-b",branch])
            # Create stub files under app paths if they exist; otherwise under autopm/out/stubs
            stubpath = ROOT/"autopm/out/stubs"/epic["key"]/br.replace("/","__")
            stubpath.mkdir(parents=True, exist_ok=True)
            (stubpath/"README.md").write_text(f"# TODO for {epic['title']} → {br}\n", encoding="utf-8")
            # Commit
            subprocess.check_call(["git","add","."])
            subprocess.check_call(["git","commit","-m",f"{epic['key']}: scaffold {br} (autopm)"])
    # return to previous branch
    subprocess.check_call(["git","checkout","-"])

def main():
    import argparse
    ensure_dirs()
    cfg = pick_provider(load_config())
    llm = LLM(cfg["model_provider"], cfg["model"], cfg["temperature"], cfg["max_output_tokens"])
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--critique", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--watch", action="store_true")
    args = ap.parse_args()

    if args.plan or (not args.critique and not args.execute and not args.watch):
        plan(llm)
        for role in ["pm","uiux","react","django","owner","qa"]:
            critique(llm, role)
        generate_tasks(llm)

    if args.execute:
        execute_commits(cfg)

    if args.watch:
        # simple watchdog on repo (debounced)
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        import threading

        class Handler(FileSystemEventHandler):
            def __init__(self):
                self._pending = False
                self._lock = threading.Lock()

            def on_any_event(self, event):
                if any(glob.fnmatch.fnmatch(event.src_path, pat) for pat in cfg.get("watch_ignore_globs", [])):
                    return
                with self._lock:
                    if not self._pending:
                        self._pending = True
                        threading.Timer(2.0, self._run).start()

            def _run(self):
                print("[yellow]Change detected. Re-planning...[/yellow]")
                plan(llm)
                for role in ["pm","uiux","react","django","owner","qa"]:
                    critique(llm, role)
                generate_tasks(llm)
                with self._lock:
                    self._pending = False

        obs = Observer()
        obs.schedule(Handler(), path=str((ROOT / "..").resolve()), recursive=True)
        obs.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            obs.stop()
        obs.join()

if __name__ == "__main__":
    main()
