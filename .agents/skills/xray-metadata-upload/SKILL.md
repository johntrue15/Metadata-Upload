# Skill: X-ray metadata upload repo

## When to use

Use this skill when the user is working in the **Metadata-Upload** repository or asks about X-ray metadata ingestion, file watchers, auto-commit to GitHub, or maintaining this codebase.

## What this repo does

- **Auto-commit watchers** — Three Python scripts that watch folders (local or network) and push new or changed files to a GitHub repository. Use case: X-ray/metadata files from imaging or PACS being versioned for analysis and audit.
- **Scripts:**
  - `auto_commit_watcher.py`: poll-based; config in file (`REPO_PATH`, `REPO_URL`, `BRANCH`, `GITHUB_TOKEN`).
  - `file_watcher_github.py`: `watchdog` + GitPython; args `folder_path`, `repo_url`; token from `REPO_TOKEN` or `--token` or `.github_config`.
  - `network_file_watcher_github.py`: watches network path, copies to local Git dir, then commit/push; same token sources.

## Code and repo maintenance

- **Secrets:** Tokens only via env (`GITHUB_TOKEN`, `REPO_TOKEN`), CLI `--token`, or local `.github_config` (must be in `.gitignore`). Never embed tokens in code.
- **Python:** 3.x, `pathlib.Path`, type hints and docstrings preferred. Dependencies in `requirements.txt` (e.g. `watchdog`, `GitPython`).
- **X-ray metadata:** Ingested files may be DICOM metadata exports, CSV/JSON/XML, or logs. Handle encoding and size; skip binaries or temp files via ignore patterns when appropriate.
- **Changes:** Prefer backward-compatible changes (new flags, optional args); keep README and docstrings in sync with usage.

## Quick commands (for agent or user)

```bash
# Local folder → GitHub
python file_watcher_github.py /path/to/watch https://github.com/user/repo.git

# Network share → local Git → GitHub
python network_file_watcher_github.py "\\\\server\\share" ./local_repo https://github.com/user/repo.git

# Poll-based (edit REPO_* in script first)
python auto_commit_watcher.py
```

Token: set `REPO_TOKEN` or `GITHUB_TOKEN` (for auto_commit_watcher) or pass `--token`.
