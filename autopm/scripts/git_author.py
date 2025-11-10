import subprocess, re, os, sys

def get_git_config(key):
    try:
        return subprocess.check_output(["git","config","--get",key], text=True).strip()
    except subprocess.CalledProcessError:
        return ""

def ensure_author():
    name = get_git_config("user.name")
    email = get_git_config("user.email")
    target_name = "Anton Alexander"
    if name != target_name:
        print(f"[autopm] Forcing git author to '{target_name}' (was '{name or 'unset'}').")
    if not email:
        print("[autopm] WARNING: git user.email not set; commits will use 'anton@example.com'.")
        email = "anton@example.com"
    os.environ["GIT_AUTHOR_NAME"] = target_name
    os.environ["GIT_COMMITTER_NAME"] = target_name
    os.environ["GIT_AUTHOR_EMAIL"] = email
    os.environ["GIT_COMMITTER_EMAIL"] = email

def git_clean():
    # consider repo clean if there are no *tracked* changes
    try:
        subprocess.check_call(["git","diff-index","--quiet","HEAD","--"])
        return True
    except subprocess.CalledProcessError:
        return False

def git_branch(name):
    subprocess.check_call(["git","checkout","-b",name])

def git_add_all():
    subprocess.check_call(["git","add","."])

def git_commit(msg):
    subprocess.check_call(["git","commit","-m",msg])

if __name__ == "__main__":
    ensure_author()
    print("Author enforced.")
