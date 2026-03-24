# DigitalOcean setup guide

This assumes you already have a droplet and ZeroClaw installed, and want to run this repo alongside it.

## Suggested filesystem layout

```text
~/src/zeroclaw
~/src/personal-agent-os-kit-v2
~/bin
```

## 1) Base packages

```bash
sudo apt-get update
sudo apt-get install -y build-essential pkg-config libssl-dev git curl unzip jq sqlite3 ripgrep just tmux
```

## 2) Rust toolchain

```bash
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
rustup default stable
```

## 3) Codex CLI

```bash
npm install -g @openai/codex
codex --help
```

## 4) Claude Code

Follow Anthropic's Linux install steps from the official docs.
After install:

```bash
claude --help || claude doctor
```

## 5) Repo bootstrap

```bash
cd ~/src
unzip personal-agent-os-kit-v2.zip
cd personal-agent-os-kit-v2
cp config/env.example .env
```

## 6) Build

```bash
cargo build
cargo test
```

## 7) systemd user service

```bash
mkdir -p ~/.config/systemd/user
cp templates/systemd/personal-agentd.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now personal-agentd
systemctl --user status personal-agentd
```

## 8) ZeroClaw coexistence

Run ZeroClaw and Agent-OS as separate services. Use different ports and data directories.
