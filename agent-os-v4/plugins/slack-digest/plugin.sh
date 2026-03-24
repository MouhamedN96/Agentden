#!/usr/bin/env bash
# slack-digest plugin — posts a task summary to a Slack webhook
# Context vars: PLUGIN_CTX_WEBHOOK=https://hooks.slack.com/...
#               PLUGIN_CTX_CHANNEL=#channel
#               PLUGIN_CTX_MESSAGE=summary text
set -euo pipefail

WEBHOOK="${PLUGIN_CTX_WEBHOOK:-${SLACK_WEBHOOK_URL:-}}"
CHANNEL="${PLUGIN_CTX_CHANNEL:-#agent-os}"
MESSAGE="${PLUGIN_CTX_MESSAGE:-agentd task completed}"
EVENT="${AGENT_OS_EVENT:-devtask.finished}"

if [[ -z "$WEBHOOK" ]]; then
  echo '{"error":"PLUGIN_CTX_WEBHOOK not set and SLACK_WEBHOOK_URL not in env"}' >&2
  exit 1
fi

PAYLOAD=$(jq -n \
  --arg channel "$CHANNEL" \
  --arg event   "$EVENT" \
  --arg msg     "$MESSAGE" \
  '{channel:$channel, text:"*[\($event)]* \($msg)"}')

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST -H "Content-Type: application/json" \
  -d "$PAYLOAD" "$WEBHOOK")

if [[ "$STATUS" == "200" ]]; then
  echo "{\"plugin\":\"slack-digest\",\"channel\":\"$CHANNEL\",\"http_status\":$STATUS,\"status\":\"ok\"}"
else
  echo "{\"plugin\":\"slack-digest\",\"channel\":\"$CHANNEL\",\"http_status\":$STATUS,\"status\":\"failed\"}" >&2
  exit 1
fi
