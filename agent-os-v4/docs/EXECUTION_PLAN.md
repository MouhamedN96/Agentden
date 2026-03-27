# Execution plan

## Objective

Finish the scaffold into a working personal dev-agent runtime where Agent-OS manages Codex and Claude Code as tools.

## Milestones

### Milestone 1 — Buildable kernel
- wire workspace dependencies
- implement config loading
- implement logging
- finish `agentd` CLI (`run`, `devtask`, `mcp serve` placeholder)
- make `cargo build` pass

### Milestone 2 — Safe dev-tool wrappers
- implement `CodexTool`
- implement `ClaudeCodeTool`
- implement timeout / output capture
- implement path allowlists
- persist task logs

### Milestone 3 — Worktree orchestration
- create / clean worktrees
- branch naming strategy
- git diff summary
- diff budget checks

### Milestone 4 — Validation pipeline
- run `cargo fmt --check`
- run `cargo clippy`
- run `cargo test`
- summarize failures
- optional cross-tool repair pass

### Milestone 5 — Long-running agent service
- scheduler
- task journal
- recurring jobs
- HTTP or MCP control surface

## Recommended development split

### Use Claude Code for
- codebase understanding
- architecture changes
- debugging build/test failures
- writing integration glue

### Use Codex for
- focused implementations
- repetitive scaffolding
- fast patch generation
- isolated refactors

## Suggested loop

1. Claude Code maps the repo and creates/updates a work plan.
2. Codex implements one bounded task.
3. Agent-OS runs validation.
4. Claude Code reviews and repairs.
5. Agent-OS commits or opens a PR after approval.
