# Tooling model

## External dev tools, supervised internally

Agent-OS treats Codex and Claude Code as **subordinate dev tools**.

### Contract

- Agent-OS scopes the task
- Agent-OS allocates a worktree
- Agent-OS invokes the tool
- Agent-OS validates the result
- Agent-OS decides whether to retry, repair, commit, or stop

## Safety controls

- worktree isolation
- path allowlists / deny lists
- timeout per task
- changed-file budget
- no auto-merge by default
