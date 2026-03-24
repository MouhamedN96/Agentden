# Personal Agent OS Kit V4

Personal-use Rust runtime for your own dev-task and research workflow.

## Repository Context

- This folder is committed inside `Agentden` as a separate workspace track.
- It is intended for personal operations only, not as a general SDK/package.

## Modules

- `agentd`: CLI/runtime entrypoint.
- `agent-core`: orchestration contracts and shared types.
- `agent-tools`: shell/git/fs/test tool wrappers.
- `agent-devtools`: Codex and Claude Code tool adapters.
- `agent-router`: backend/model routing.
- `agent-memory`: persistence layer scaffold.
- `agent-scheduler`: scheduled task scaffold.
- `agent-autoresearch`: experiment loop implementation.

## Implemented V4 Features

- `agentd research` command integrated with `agent-autoresearch`.
- Hook emission using `agent-hooks` event runner.
- Patch application path through devtool wrappers.
- Trackio-compatible JSONL logging in research loop.
- Model registry logging with optional version artifact snapshots.
- Obsidian note/session summary output generation.

## Verification

```bash
cargo check -p agent-autoresearch -p agentd
cargo check
cargo run -p agentd -- research --help
```

## Key Paths

- `crates/agentd/src/main.rs`
- `crates/agent-autoresearch/src/loop.rs`
- `crates/agent-autoresearch/src/program.rs`
- `crates/agent-autoresearch/src/trackio.rs`
- `crates/agent-autoresearch/src/model_registry.rs`
- `skills/autoresearch/program.md`

## Operations

- Deployment scripts: `scripts/`
- Service template: `templates/systemd/personal-agentd.service`
- Environment and hooks config: `config/`
