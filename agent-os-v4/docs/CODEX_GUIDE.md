# Codex guide for this repo

## Role in this project

Codex is used as an **invokable development tool**, not as the top-level orchestrator.

## Recommended prompt pattern

```text
Implement <feature> in this Rust workspace.
Constraints:
- keep changes within <paths>
- do not change deployment scripts unless needed
- run cargo fmt and cargo test
- summarize changed files and follow-up work
```

## First tasks to assign

1. make workspace compile
2. implement `agent-devtools` wrappers
3. implement `worktree_manager`
4. add task journal persistence
5. add `agentd devtask` command
