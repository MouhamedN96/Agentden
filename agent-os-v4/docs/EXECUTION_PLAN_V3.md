# Execution Plan V3

## Goal
Extend Agent-OS so it can manage Codex and Claude Code as developer tools while also supporting reusable skills, lifecycle hooks, and external plugins.

## Order of implementation

### Phase 1
- wire skill registry into `agentd`
- add `skills list` and `skills suggest`
- inject `prompt_prelude` into dev tool requests

### Phase 2
- wire hook registry into devtask lifecycle
- emit `devtask.started`, `devtask.finished`, and `devtask.failed`
- add append-only JSONL event log

### Phase 3
- wire plugin registry
- add `plugins list` and `plugins invoke`
- implement first two real plugins: GitHub and Slack

### Phase 4
- add policy engine
- path budgets
- branch naming policy
- per-skill preferred dev tool strategy

## Claude Code prompt
Implement skill-aware task execution in Rust. Read `docs/SKILLS_HOOKS_PLUGINS.md`, then wire the skill registry into `agentd` so a devtask can optionally choose a matching skill and prepend the skill prelude to the developer tool prompt. Keep changes small and compile-focused.

## Codex prompt
Implement hook lifecycle support. Add `devtask.started` and `devtask.finished` event emission around dev tool execution, reading hook definitions from `config/hooks/hooks.json`. For this pass, simulating command execution is acceptable, but structure the code so real command execution can be enabled later.
