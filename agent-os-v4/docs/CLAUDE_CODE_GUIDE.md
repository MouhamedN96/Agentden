# Claude Code guide for this repo

## Role in this project

Claude Code is used as an **invokable development tool** for repo reasoning, architecture-aware edits, and repair passes.

## Recommended prompt pattern

```text
Analyze this workspace and implement <feature>.
Stay within <paths>.
Preserve the runtime-supervisor architecture where Agent-OS manages Codex and Claude Code as tools.
Run build/tests and summarize failures clearly.
```

## First tasks to assign

1. audit the scaffold and fix compile blockers
2. refine tool contracts and policies
3. implement validation flow
4. add structured run logging
5. add MCP control surface stub
