# Metadata-Upload — Claude Code context

This repo contains **Python watchers** that auto-commit files to GitHub. Use case: **X-ray metadata analysis** — ingesting metadata from imaging/PACS and versioning it in Git.

## Layout

- **auto_commit_watcher.py** — Polls a local repo for new files; commits and pushes. Uses `GITHUB_TOKEN`, `REPO_PATH`, `REPO_URL`, `BRANCH`.
- **file_watcher_github.py** — Watches a folder with `watchdog`; commits new/modified files. Uses `REPO_TOKEN` or `--token` or `.github_config`.
- **network_file_watcher_github.py** — Watches a network path, copies to local Git, then commit/push. Same token handling.

Dependencies: `requirements.txt` (watchdog, GitPython for the latter two). No tokens in code; use env or config only.

## AI / API keys (add later)

- **Claude** — For Claude Code / Anthropic API: set `ANTHROPIC_API_KEY` (e.g. in `.env` or your shell). Get keys at [console.anthropic.com](https://console.anthropic.com).
- **Moltbot (OpenClaw)** — OpenClaw uses its own auth store. After installing OpenClaw, run `openclaw onboard` and `openclaw agents add` (or copy auth from another agent). Workspace for this repo: set `agents.defaults.workspace` in `~/.openclaw/openclaw.json` to this directory.

Copy `.env.example` to `.env` and fill in keys when ready; `.env` is gitignored.
