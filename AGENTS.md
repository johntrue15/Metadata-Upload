# Metadata-Upload — Agent instructions

You are helping maintain the **Metadata-Upload** repository: a Python-based pipeline for watching folders (local or network) and auto-committing files to GitHub. The primary use case is **X-ray metadata analysis** — ingesting metadata files (e.g. from imaging equipment or PACS) and versioning them in Git for analysis, auditing, and collaboration.

## Repository purpose

- **auto_commit_watcher.py** — Polls a local repo for new files and commits/pushes them. Configure `REPO_PATH`, `REPO_URL`, `BRANCH`; uses `GITHUB_TOKEN`.
- **file_watcher_github.py** — Uses `watchdog` to watch a folder for new/modified files and commits them to a GitHub repo. Uses `REPO_TOKEN` or `--token` or `.github_config`.
- **network_file_watcher_github.py** — Watches a **network drive**, copies new files to a **local Git repo**, then commits and pushes to GitHub. Same token handling as above.

All scripts support HTTPS GitHub URLs with token-based auth; never commit tokens.

## Your role

When asked to **write code** or **maintain this repo**:

1. **Preserve behavior** — Keep token handling via env/config/CLI; no hardcoded secrets.
2. **Python style** — Use Python 3, `pathlib.Path`, type hints where helpful, docstrings for modules and public functions.
3. **X-ray metadata context** — Scripts may receive DICOM metadata exports, CSV/JSON/XML metadata, or log files. Consider encoding, large files, and safe ignore patterns (e.g. binary DICOM vs text metadata).
4. **Testing** — Prefer runnable examples and clear usage in docstrings/README; add tests if the user wants them.
5. **Dependencies** — Use `requirements.txt`; avoid adding dependencies unless needed (e.g. `watchdog`, `GitPython` for the watchers that use them).

## Workspace layout

- Root: watcher scripts, `AGENTS.md`, `README.md`, `requirements.txt`.
- Config/tokens: `.github_config` if used must be in `.gitignore`; use env vars in CI/documentation.

When suggesting changes, prefer minimal diffs and backward-compatible options (e.g. new CLI flags rather than breaking existing args).
