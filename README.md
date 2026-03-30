# A-Den Personal Setup

Personal setup and workflow repository for running a custom Agent-OS Stack on VPS
## Provenance

- Base repository: [MouhamedN96/Agentden](https://github.com/MouhamedN96/Agentden)
- Related reference reviewed during this build: [RightNow-AI/openfang](https://github.com/RightNow-AI/openfang)
- Added in this branch: `agent-os-v4/` (Rust runtime + autoresearch loop)

## Scope In This Branch

- Personal-use workflow only.
- Adds `agent-os-v4/**` as a self-contained Rust workspace.
- Keeps existing AgentDen code (`cli/`, `council/`, `bridge/`, `coder/`) unchanged.
- Excludes local runtime artifacts and personal workspace files from commit.

## Current Agent-OS v4 State

- `agentd` includes `research` command path.
- `agent-autoresearch` is integrated and includes:
  - experiment loop runner
  - hook events through `agent-hooks`
  - Trackio-compatible event logging
  - model version registry and optional artifact snapshots
- compile verification completed for:
  - `cargo check -p agent-autoresearch -p agentd`
  - `cargo check` (workspace, from `agent-os-v4/`)

## Run Commands

```bash
cd agent-os-v4
cargo check -p agent-autoresearch -p agentd
cargo run -p agentd -- research --help
```

## Next Implementation Steps

1. Complete deployment scripts and service wiring on DigitalOcean.
2. Add chat entrypoints (Discord/Telegram) to the deployed runtime.
3. Expand tests from smoke coverage to repeatable CI checks.
