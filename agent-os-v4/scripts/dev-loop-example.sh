#!/usr/bin/env bash
set -euo pipefail
TASK=${1:-"Implement agent-devtools wrappers"}
./target/debug/agentd devtask --tool claude_code --repo . --objective "$TASK" --allowed-path crates/agent-devtools --validate
