#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y build-essential pkg-config libssl-dev git curl unzip jq sqlite3 ripgrep just tmux
if ! command -v rustup >/dev/null 2>&1; then
  curl https://sh.rustup.rs -sSf | sh -s -- -y
fi
source "$HOME/.cargo/env"
rustup default stable

# Create runtime directories agent-os needs at startup
AGENT_DATA_DIR="${AGENT_OS_DATA_DIR:-./data}"
mkdir -p \
  "$AGENT_DATA_DIR/logs" \
  "$AGENT_DATA_DIR/sessions" \
  "$AGENT_DATA_DIR/cache"
echo "agent-os data dirs created at $AGENT_DATA_DIR"
