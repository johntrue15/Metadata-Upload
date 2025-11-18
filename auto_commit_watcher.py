#!/usr/bin/env python3
"""
Simple folder watcher that auto-commits NEW files to GitHub.

Usage (from terminal or PyCharm run config):
    python auto_commit_watcher.py

Config:
    - Set REPO_PATH to your local repo folder.
    - Set REPO_URL to your GitHub HTTPS URL (no token in it).
    - Set BRANCH to the branch you want to push to (e.g., "main" or "master").
    - Set the GITHUB_TOKEN environment variable to a PAT with repo access.
"""

import os
import time
import subprocess
from pathlib import Path

# ========================
# CONFIG — EDIT THESE
# ========================

# Local repo path (the folder PyCharm is using for this project)
REPO_PATH = Path(r"/path/to/your/local/repo").resolve()

# GitHub repo URL (normal HTTPS form, NO TOKEN in it)
# Example: "https://github.com/username/repo.git"
REPO_URL = "https://github.com/username/repo.git"

# Branch to push to
BRANCH = "main"  # or "master", etc.

# Name of the environment variable that holds your token
TOKEN_ENV_VAR = "GITHUB_TOKEN"

# How often to poll for new files (seconds)
POLL_INTERVAL = 3

# Optional: ignore patterns (relative paths containing any of these substrings)
IGNORE_SUBSTRINGS = [
    ".git",
    "__pycache__",
    ".idea",
    ".venv",
]


# ========================
# HELPER FUNCTIONS
# ========================

def run_git(*args):
    """Run a git command in REPO_PATH and return (exit_code, stdout, stderr)."""
    cmd = ["git", "-C", str(REPO_PATH), *args]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    out, err = proc.communicate()
    return proc.returncode, out.strip(), err.strip()


def ensure_git_repo():
    """Make sure REPO_PATH is a git repo."""
    code, out, err = run_git("rev-parse", "--is-inside-work-tree")
    if code != 0 or out != "true":
        raise RuntimeError(f"{REPO_PATH} is not a git repository.\nGit says: {err or out}")


def get_token():
    token = os.getenv(TOKEN_ENV_VAR)
    if not token:
        raise RuntimeError(
            f"Environment variable {TOKEN_ENV_VAR} is not set.\n"
            f"Set it to your GitHub Personal Access Token."
        )
    if len(token) < 10:
        raise RuntimeError("GitHub token looks too short; is it correct?")
    return token


def make_authenticated_url(token: str) -> str:
    """Turn https://github.com/user/repo.git into https://TOKEN@github.com/user/repo.git"""
    if not REPO_URL.startswith("https://"):
        raise ValueError("REPO_URL must be an HTTPS URL (https://github.com/...)")
    return REPO_URL.replace("https://", f"https://{token}@")


def should_ignore(path: Path) -> bool:
    rel = path.relative_to(REPO_PATH)
    rel_str = str(rel)
    for s in IGNORE_SUBSTRINGS:
        if s in rel_str:
            return True
    return False


def list_all_files() -> set[Path]:
    """Return a set of ALL non-ignored files under REPO_PATH (recursive)."""
    files = set()
    for root, dirs, filenames in os.walk(REPO_PATH):
        root_path = Path(root)
        # Skip .git and other ignored directories early
        dirs[:] = [d for d in dirs if not should_ignore(root_path / d)]
        for name in filenames:
            p = root_path / name
            if not should_ignore(p):
                files.add(p)
    return files


def commit_and_push(new_files: set[Path], auth_url: str):
    if not new_files:
        return

    # Convert to paths relative to REPO_PATH for git add
    rel_paths = [str(f.relative_to(REPO_PATH)) for f in new_files]

    print(f"\n🔍 New files detected:")
    for p in rel_paths:
        print(f"  + {p}")

    # Stage the new files
    code, out, err = run_git("add", *rel_paths)
    if code != 0:
        print(f"❌ git add failed:\n{err or out}")
        return

    # Commit
    msg = "Auto-commit new files: " + ", ".join(rel_paths)
    code, out, err = run_git("commit", "-m", msg)
    if code != 0:
        # Common case: "nothing to commit"
        print(f"⚠️ git commit did not create a commit:\n{err or out}")
        return

    print(f"✅ Commit created:\n{out}")

    # Push using auth URL
    code, out, err = run_git("push", auth_url, f"HEAD:{BRANCH}")
    if code != 0:
        print(f"❌ git push failed:\n{err or out}")
        return

    print(f"🚀 Successfully pushed to {REPO_URL} ({BRANCH})")


# ========================
# MAIN LOOP
# ========================

def main():
    print(f"📁 Repo path : {REPO_PATH}")
    print(f"🌐 Repo URL  : {REPO_URL}")
    print(f"🌿 Branch    : {BRANCH}")
    print(f"🔑 Token var : {TOKEN_ENV_VAR}")
    print(f"⏱  Interval  : {POLL_INTERVAL} s")

    if not REPO_PATH.exists():
        raise RuntimeError(f"Repo path does not exist: {REPO_PATH}")

    ensure_git_repo()
    token = get_token()
    auth_url = make_authenticated_url(token)

    print("\n✅ Git repo OK.")
    print("✅ Token found.")
    print("👀 Watching for NEW files. Press Ctrl+C to stop.\n")

    known_files = list_all_files()

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            current_files = list_all_files()
            # Only detect files that are in current_files but not in known_files
            new_files = current_files - known_files

            if new_files:
                commit_and_push(new_files, auth_url)

            known_files = current_files
    except KeyboardInterrupt:
        print("\n👋 Stopped watching.")


if __name__ == "__main__":
    main()
