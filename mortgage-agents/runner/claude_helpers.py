import os, subprocess, tempfile, shlex

DEFAULT_ALLOWED_TOOLS = "Bash,Read,Grep,Glob,WebSearch,WebFetch,Edit,Write"

def call_claude(prompt: str,
                allowed_tools: str = None,
                accept_edits: bool = True,
                cwd: str = None,
                output_file: str = None) -> str:
    """
    Call the Claude CLI with a big prompt. We write the prompt to a temp file,
    then pass it via command substitution to avoid quoting issues.
    """
    allowed_tools = allowed_tools or os.environ.get("AGENT_ALLOWED_TOOLS", DEFAULT_ALLOWED_TOOLS)
    cmd = f'claude -p "$(cat {{prompt_file}})" --allowedTools "{allowed_tools}"'
    if accept_edits:
        cmd += " --permission-mode acceptEdits"
    cmd += " --output-format text"

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as tf:
        tf.write(prompt)
        tf.flush()
        prompt_path = tf.name

    cmd = cmd.replace("{prompt_file}", shlex.quote(prompt_path))
    proc = subprocess.run(["bash", "-lc", cmd], cwd=cwd, capture_output=True, text=True)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    rc = proc.returncode

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(stdout + ("\n\n[stderr]\n" + stderr if stderr else ""))
        except Exception:
            pass

    if rc != 0:
        raise RuntimeError(f"Claude CLI failed (rc={rc}): {stderr.strip()}")

    return stdout.strip()
