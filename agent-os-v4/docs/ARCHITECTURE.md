# Architecture

## Goal

Build a **personal agent runtime** where the runtime itself supervises development workflows and can invoke external coding agents as tools.

## Layers

1. **Agent-OS Kernel**
   - task intake
   - planning
   - approvals
   - memory
   - scheduler
   - repo state
2. **Tool Layer**
   - shell, git, fs, tests
   - `codex` wrapper
   - `claude_code` wrapper
3. **LLM / Router Layer**
   - backend for Agent-OS internal reasoning
   - optional local router adapter
4. **Connectors**
   - GitHub
   - Slack / Telegram later

## Runtime supervision pattern

The runtime owns the workflow:

```text
User request
  -> Agent-OS planner
  -> worktree allocation
  -> invoke codex or claude_code tool
  -> inspect diff
  -> run build/tests
  -> optional repair pass
  -> summarize
  -> optional commit / PR
```

## Why this split

- keeps Codex / Claude Code optional and replaceable
- isolates repo changes in worktrees
- gives Agent-OS one source of truth for memory, permissions, and task history
