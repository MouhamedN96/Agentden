#!/usr/bin/env bash
# github-sync plugin — syncs open issues/PRs to local JSONL log
# Context vars: PLUGIN_CTX_REPO=owner/repo  PLUGIN_CTX_OUTPUT_DIR=data/logs
set -euo pipefail

REPO="${PLUGIN_CTX_REPO:-}"
OUTPUT_DIR="${PLUGIN_CTX_OUTPUT_DIR:-data/logs}"
LOG_FILE="${OUTPUT_DIR}/github-sync.jsonl"

if [[ -z "$REPO" ]]; then
  echo '{"error":"PLUGIN_CTX_REPO not set. Pass --ctx REPO=owner/repo"}' >&2
  exit 1
fi

if ! command -v gh &>/dev/null; then
  echo '{"error":"gh CLI not installed — https://cli.github.com"}' >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Append issues
gh issue list \
  --repo "$REPO" \
  --state open \
  --json number,title,state,labels,createdAt,url \
  --limit 50 \
  | jq -c --arg repo "$REPO" '.[] + {repo:$repo,kind:"issue"}' >> "$LOG_FILE"

# Append PRs
gh pr list \
  --repo "$REPO" \
  --state open \
  --json number,title,state,labels,createdAt,url \
  --limit 50 \
  | jq -c --arg repo "$REPO" '.[] + {repo:$repo,kind:"pr"}' >> "$LOG_FILE"

echo "{\"plugin\":\"github-sync\",\"repo\":\"$REPO\",\"log\":\"$LOG_FILE\",\"status\":\"ok\"}"
