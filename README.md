# Metadata-Upload

Python tools that watch folders (local or network) and auto-commit files to GitHub. Built for **X-ray metadata analysis** — ingesting metadata from imaging equipment or PACS and versioning it in Git for analysis, auditing, and collaboration.

## Scripts

| Script | Purpose |
|--------|--------|
| **auto_commit_watcher.py** | Polls a local repo for new files; commits and pushes. Set `REPO_PATH`, `REPO_URL`, `BRANCH`; use `GITHUB_TOKEN`. |
| **file_watcher_github.py** | Watches a local folder with `watchdog`; commits new/modified files to a GitHub repo. |
| **network_file_watcher_github.py** | Watches a network path, copies files to a local Git repo, then commits and pushes to GitHub. |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Secrets:** Use environment variables or a local config file; never commit tokens.

- **auto_commit_watcher.py:** `GITHUB_TOKEN`
- **file_watcher_github.py** / **network_file_watcher_github.py:** `REPO_TOKEN` or `--token` or `.github_config` (add to `.gitignore`)

## API keys (add later)

We’ll add API keys for **Claude** and **Moltbot (OpenClaw)** when ready.

| Service | Where to add | Notes |
|--------|---------------|--------|
| **Claude** (Claude Code / Anthropic) | `.env` as `ANTHROPIC_API_KEY`, or sign in via Claude Code | [Console](https://console.anthropic.com) or Claude Pro/Max |
| **Moltbot** (OpenClaw) | `openclaw onboard` then `openclaw agents add` | Auth in `~/.openclaw/agents/.../auth-profiles.json` |

- Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` when you have it; `.env` is gitignored.
- OpenClaw does not use `.env` for model auth; use its wizard and `agents add` to configure providers.

## Claude Code

This repo is set up for [Claude Code](https://claude.com/claude-code): project settings in `.claude/settings.json`, context in `CLAUDE.md`. Open the project in Claude Code (`claude` in this directory) and add your Anthropic API key (or sign in) when ready.

## Quick start

```bash
# Watch a folder and push to GitHub
python file_watcher_github.py /path/to/watch https://github.com/username/Metadata-Upload.git

# Watch a network share → local repo → GitHub
python network_file_watcher_github.py "\\\\server\share" ./local_repo https://github.com/username/Metadata-Upload.git
```

## OpenClaw integration

This repo is set up for [OpenClaw](https://github.com/openclaw/openclaw) so you can use it for **writing code** and **maintaining** this project (and other X-ray metadata workflows).

### 1. Install OpenClaw

Requires **Node ≥22**.

```bash
npm install -g openclaw@latest
# or: pnpm add -g openclaw@latest
```

Then run the onboarding wizard and start the gateway:

```bash
openclaw onboard --install-daemon
openclaw gateway --port 18789 --verbose
```

### 2. Use this repo as the workspace

Point OpenClaw’s workspace to this repo so the agent sees `AGENTS.md` and the project skill:

- **Option A — config:** In `~/.openclaw/openclaw.json` set:
  ```json
  {
    "agents": {
      "defaults": {
        "workspace": "/Users/you/Documents/GitHub/Metadata-Upload"
      }
    }
  }
  ```
- **Option B — clone into default workspace:** Clone or symlink this repo under `~/.openclaw/workspace` so it’s the active project.

### 3. Talk to the agent

From the CLI (with gateway running):

```bash
openclaw agent --message "Add a README section for DICOM metadata file patterns"
openclaw agent --message "Review file_watcher_github.py for error handling"
```

Or use WebChat, Slack, Discord, etc. once channels are configured.

### 4. What’s in this repo for OpenClaw

- **AGENTS.md** — Injected into the agent; describes this repo, X-ray metadata context, and how to edit code safely.
- **.agents/skills/xray-metadata-upload/SKILL.md** — Skill that teaches the agent about the watchers, token handling, and common commands.

Use OpenClaw to add features, fix bugs, add tests, or extend the pipeline for new X-ray metadata formats.

## License

Use and modify as needed for your environment.
