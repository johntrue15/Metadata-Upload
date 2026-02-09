#!/usr/bin/env bash
# Install OpenClaw in this repo and run a quick test.
# Requires Node.js >= 22. If missing, install from https://nodejs.org/ or:
#   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
#   source ~/.nvm/nvm.sh && nvm install 22 && nvm use 22

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== 1. Checking Node.js ==="
if ! command -v node &>/dev/null; then
  echo "Node.js not found. Install Node >= 22 first:"
  echo "  https://nodejs.org/"
  echo "  or: nvm install 22"
  exit 1
fi
NODE_VER=$(node -v)
echo "Found $NODE_VER"

MAJOR=$(node -e "console.log(process.version.slice(1).split('.')[0])")
if [ "$MAJOR" -lt 22 ]; then
  echo "OpenClaw requires Node >= 22. Current: $NODE_VER"
  exit 1
fi

echo ""
echo "=== 2. Installing dependencies (openclaw) ==="
npm install

echo ""
echo "=== 3. OpenClaw version ==="
npx openclaw --version 2>/dev/null || npx openclaw -v 2>/dev/null || true

echo ""
echo "=== 4. Quick agent test (gateway must be running) ==="
echo "If the gateway is not running, start it in another terminal:"
echo "  npx openclaw gateway --port 18789 --verbose"
echo ""
echo "Then run:"
echo "  npx openclaw agent --message \"Summarize the three Python watcher scripts in this repo\""
echo ""
read -p "Start gateway in background and run one agent test now? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[yY] ]]; then
  echo "Starting gateway in background..."
  npx openclaw gateway --port 18789 --verbose &
  GWPID=$!
  sleep 5
  echo "Running agent test..."
  npx openclaw agent --message "In one short paragraph, what does this repository do and what are the three Python scripts?" || true
  kill $GWPID 2>/dev/null || true
fi

echo ""
echo "=== Done ==="
echo "To use OpenClaw: set agents.defaults.workspace to: $REPO_ROOT"
echo "  in ~/.openclaw/openclaw.json"
