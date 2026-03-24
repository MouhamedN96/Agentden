# Skills, Hooks, and Plugins

This layer adds three extension surfaces to Agent-OS.

## 1. Skills

Skills are reusable execution recipes. A skill is a directory under `skills/` with a `skill.json` manifest.

Use skills when you want Agent-OS to detect and apply a repeatable workflow, such as:
- repo refactors
- bugfix loops
- release prep
- doc generation

A skill should define:
- `name`
- `description`
- `triggers`
- `tools`
- `prompt_prelude`

## 2. Hooks

Hooks are event listeners. They fire when Agent-OS emits lifecycle events.

Suggested events:
- `devtask.started`
- `devtask.finished`
- `devtask.failed`
- `scheduler.job.started`
- `scheduler.job.finished`
- `plugin.invoked`

Hook config lives in `config/hooks/hooks.json`.

## 3. Plugins

Plugins are external adapters. They can be shell-based, MCP-based, HTTP-based, or native Rust crates later.

A plugin lives under `plugins/<name>/plugin.json`.

Suggested plugin uses:
- GitHub issue sync
- Slack digest generation
- deployment adapters
- private API clients

## Recommended runtime order

1. Intake task
2. Match skill(s)
3. Emit `devtask.started`
4. Run dev tool(s)
5. Emit `plugin.invoked` when needed
6. Emit `devtask.finished` or `devtask.failed`

## Dev rule

Keep plugins narrow and keep supervisor policy in Agent-OS. Do not bury policy in plugins.
