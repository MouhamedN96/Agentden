# Agent-OS Handoff Document
**For:** Claude Code / Codex  
**Status:** Scaffold complete, pre-compile  
**Last human session:** March 2026  
**First task:** Run `cargo build` and fix any errors before doing anything else.

---

## What This Project Is

A personal agent runtime running on a **DigitalOcean droplet**, deployed alongside ZeroClaw. `agentd` is a supervisor binary that:

- Dispatches dev tasks to **Claude Code** and **Codex** as bounded subprocesses
- Manages their lifecycle via hooks (started / finished / failed)
- Routes LLM calls through a configurable 5-tier cascade
- Runs as a **systemd user service** (`personal-agentd.service`)

This is not a product. It is dev infrastructure that sits on the DO server and automates development workflows across any repo you point it at.

### Filesystem layout on the droplet

```
~/src/zeroclaw/                    # ZeroClaw — runs separately
~/src/personal-agent-os-kit-v2/   # This repo
~/bin/                             # Local binaries
```

### Coexistence with ZeroClaw

Agent-OS and ZeroClaw run as separate systemd services. Different ports, different data directories. They do not share state. ZeroClaw triggers `agentd devtask` via CLI — Agent-OS is downstream of ZeroClaw in that flow.

---

## Current State: What Is Done

### Compiled? No. Written? Yes.

Every file has been authored but `cargo build` has never been run. Your first job is to compile it and fix whatever breaks.

### Fully implemented (needs compile verification)

**`crates/agentd/src/main.rs`** — 404 lines. Full CLI wired:
- `agentd run` — creates data dirs, starts supervisor (daemon loop is a stub)
- `agentd devtask --tool [codex|claude-code] --repo <path> --objective <text> [--skill <name>] [--dry-run] [--list-skills]`
- `agentd skills list` / `skills suggest --objective <text>`
- `agentd hooks simulate --event <name>` / `hooks fire --event <name>`
- `agentd plugins list` / `plugins invoke --name <name> --ctx KEY=VALUE`
- `agentd router show` / `router cascade --policy [offline|cheap|balanced|premium|fallback]`

**`crates/agent-hooks/src/lib.rs`** — Real execution:
- `fire_event_async()` — fires all hooks for an event **in parallel** via `tokio::task::spawn_blocking`
- `fire_event()` — synchronous sequential fallback
- `simulate_event()` — dry-run, no processes spawned
- Hook processes receive `AGENT_OS_EVENT` and `AGENT_OS_HOOK` env vars
- `HookDefinition.env` map injects extra vars per hook

**`crates/agent-plugins/src/lib.rs`** — Real invoke:
- `PluginRegistry::invoke(name, context)` — resolves entrypoint path, spawns subprocess
- Context passed as `PLUGIN_CTX_<KEY>` env vars (uppercased)
- Returns `PluginInvokeResult` with exit code, duration, error

**`crates/agent-router/src/lib.rs`** — Env-wired tier cascade:
- `LocalRouter::from_env()` — reads env vars, builds endpoint list sorted by tier
- `LocalRouter::choose(policy)` — returns best endpoint for a policy
- `LocalRouter::cascade(policy)` — returns all endpoints from that tier upward
- Tiers: OfflineFirst=1, Cheap=2, Balanced=3, Premium=4, Fallback=5

**`crates/agent-skills/src/lib.rs`** — Working:
- Loads skill manifests from `skills/` directory
- `suggest(objective)` — lowercase keyword match against `triggers`
- `get(name)` — exact name lookup
- Skill `prompt_prelude` injected before task dispatch

**`crates/agent-devtools/src/lib.rs`** — Working subprocess dispatch:
- `CodexTool::execute()` → `codex exec <prompt>` in repo dir
- `ClaudeCodeTool::execute()` → `claude -p <prompt>` in repo dir
- Binary paths from `CODEX_BIN` / `CLAUDE_CODE_BIN` env vars
- `WorktreeManager::branch_name(objective)` → slugified `agent/<name>` branch

### Stubs (compile but do nothing real)

| Crate | What exists | What's missing |
|---|---|---|
| `agent-memory` | `TaskJournal` with no-op `append_jsonl()` | Actual JSONL/SQLite writes |
| `agent-scheduler` | `ScheduledJob` struct with `next_run_at` | Cron loop, job dispatch |
| `agent-tools` | `Tool` trait, `ShellTool` that panics | Shell exec, git, fs, test runner |
| `agent-llm` | `LlmBackend` trait, `NoopBackend` | reqwest HTTP to OpenAI-compat endpoints |
| `agent-connectors` | `GitHubIssueRef` struct only | gh API calls, Slack API |
| `agentd run` | Creates data dirs, prints one line | Daemon loop, signal handling |

---

## Workspace Layout

```
personal-agent-os-kit-v2/
├── Cargo.toml                        # workspace — all 12 members listed
├── HANDOFF.md                        # this file
├── config/
│   ├── env.example                   # all env vars documented
│   └── hooks/hooks.json              # 4 hooks: started, finished, failed, slack-on-failure
├── scripts/
│   ├── bootstrap-do.sh               # apt deps + rustup + data dir creation
│   ├── deploy-systemd.sh             # installs personal-agentd.service
│   ├── healthcheck.sh                # checks cargo/codex/claude binaries
│   └── dev-loop-example.sh           # example devtask invocation
├── templates/systemd/
│   └── personal-agentd.service       # systemd user service unit
├── crates/
│   ├── agentd/          main binary  (src/main.rs — 404 lines)
│   ├── agent-core/      DevTask, DevResult, DevToolChoice types
│   ├── agent-devtools/  CodexTool, ClaudeCodeTool, WorktreeManager
│   ├── agent-hooks/     HookRegistry, fire_event_async, simulate_event
│   ├── agent-llm/       LlmBackend trait (stub)
│   ├── agent-memory/    TaskJournal (stub)
│   ├── agent-plugins/   PluginRegistry with invoke()
│   ├── agent-router/    LocalRouter with env-wired tier cascade
│   ├── agent-scheduler/ ScheduledJob (stub)
│   ├── agent-skills/    SkillRegistry with suggest()
│   └── agent-tools/     Tool trait, ShellTool (stub)
├── skills/
│   ├── bugfix-repair/skill.json      triggers: bug, fix, repair, failing test, panic
│   └── repo-refactor/skill.json      triggers: refactor, cleanup, rename, architecture
└── plugins/
    ├── github-sync/     plugin.json + plugin.sh (requires gh CLI)
    └── slack-digest/    plugin.json + plugin.sh (requires curl + SLACK_WEBHOOK_URL)
```

---

## Known Issues / Likely Compile Errors

Fix these in order. Do not add features until `cargo build` is clean.

### 1. `chrono` likely missing from `agent-scheduler`

`agent-scheduler/src/lib.rs` imports `use chrono::DateTime`. Check its `Cargo.toml` — `chrono` may not be listed. Fix:
```toml
chrono = { version = "0.4", features = ["serde"] }
```

### 2. `async-trait` — verify in `agent-tools`

`agent-tools/src/lib.rs` uses `#[async_trait]`. Verify `async-trait = "0.1"` is in its `Cargo.toml`. It exists in `agent-devtools` but needs confirming in `agent-tools`.

### 3. `agent-hooks` tokio features

Uses `tokio::task::spawn_blocking`. Its `Cargo.toml` has `features = ["rt-multi-thread", "macros"]`. If `spawn_blocking` not found, add `"rt"` to the features list.

### 4. `HookRunResult` shape — verify all call sites

New shape has 6 fields: `hook`, `event`, `status`, `exit_code`, `duration_ms`, `error`. Old shape had 3. `main.rs` was updated. If any other file still uses the old 3-field shape it will fail.

### 5. `emit_hooks` is `async fn` — call sites must `.await`

Both devtask call sites in `main.rs` have `.await`. If you see "future is not awaited" — this is why.

---

## DO Deployment Sequence

```bash
# On the droplet — run once
bash scripts/bootstrap-do.sh

# Copy and fill env
cp config/env.example .env
# edit .env with your keys

# Build
cargo build

# Deploy as systemd service
bash scripts/deploy-systemd.sh

# Check it's running
systemctl --user status personal-agentd
journalctl --user -u personal-agentd -f

# Healthcheck
bash scripts/healthcheck.sh
```

---

## Environment Variables

Minimum for local dev (no cloud keys needed):
```bash
RUST_LOG=info
AGENT_OS_DATA_DIR=./data
CODEX_BIN=codex
CLAUDE_CODE_BIN=claude
```

For router to work with cloud fallback:
```bash
# Tier 2 — cheap/fast
SILICONFLOW_API_KEY=your_key
SILICONFLOW_CHEAP_MODEL=liquid/lfm2-1.2b

# Tier 4 — premium
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-sonnet-4-6
```

For plugins:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
GITHUB_TOKEN=your_token   # read by gh CLI automatically
```

---

## Build and Test Sequence

```bash
# Step 1: compile
cargo build 2>&1 | head -60

# Step 2: verify CLI
cargo run -- --help
cargo run -- skills list
cargo run -- hooks simulate --event devtask.started
cargo run -- router show

# Step 3: dry-run dispatch (no real subprocess fired)
cargo run -- devtask \
  --tool claude-code \
  --repo ~/src/my-repo \
  --objective "add error handling to src/main.rs" \
  --allowed-path src/main.rs \
  --dry-run

# Step 4: live dispatch
cargo run -- devtask \
  --tool claude-code \
  --repo ~/src/my-repo \
  --objective "fix the failing test in src/audio.rs" \
  --skill bugfix-repair \
  --allowed-path src/audio.rs

# Step 5: plugin invoke
cargo run -- plugins invoke \
  --name github-sync \
  --ctx REPO=owner/repo-name
```

---

## Roadmap (from EXECUTION_PLAN.md, in order)

### Milestone 1 — Buildable kernel ← YOU ARE HERE
- wire workspace deps ✓
- implement CLI ✓  
- `cargo build` passes ← **next task**

### Milestone 2 — Safe dev-tool wrappers
- timeout + output capture on `CodexTool` / `ClaudeCodeTool` (currently fire-and-forget)
- path allowlist enforcement at supervisor level (currently passed in prompt only)
- `TaskJournal` writes actual JSONL to `data/logs/tasks.jsonl`

Target API for TaskJournal:
```rust
impl TaskJournal {
    pub fn new(data_dir: &str) -> Result<Self>
    pub fn append(&self, result: &DevResult, event: &str) -> Result<()>
    pub fn tail(&self, n: usize) -> Result<Vec<serde_json::Value>>
}
```
Wire into `main.rs` Devtask arm after result. No external deps needed — `std::fs::OpenOptions` with append mode.

### Milestone 3 — Worktree orchestration
- `WorktreeManager` creates/cleans git worktrees (currently only generates branch name)
- git diff summary after task
- diff budget enforcement (`AGENT_OS_MAX_CHANGED_FILES`)

### Milestone 4 — Validation pipeline
- `cargo fmt --check`, `cargo clippy`, `cargo test` after each task
- failure summary fed back to repair pass

### Milestone 5 — Long-running service
- Scheduler tick in `agentd run` daemon loop
- Recurring jobs (periodic repo maintenance, dependency updates)
- HTTP or MCP control surface

---

## Recommended Tool Split

Use Claude Code for:
- understanding the codebase
- architecture changes
- debugging compile/test failures
- writing integration glue between crates

Use Codex for:
- focused single-function implementations
- repetitive scaffolding (e.g. implementing ShellTool, GitTool)
- fast isolated patches

---

## Prompts That Work

For initial compile fix (Claude Code):
```
Read HANDOFF.md. Run `cargo build 2>&1 | head -60`. Fix all compile errors.
Do not add new features until the build is clean.
Allowed paths: crates/
```

For Milestone 2 — TaskJournal (Codex):
```
Read HANDOFF.md section "Milestone 2". Implement TaskJournal in crates/agent-memory/src/lib.rs.
Append DevResult as a JSON line to data/logs/tasks.jsonl on every devtask completion.
Wire into crates/agentd/src/main.rs Devtask arm after the result is returned.
Allowed paths: crates/agent-memory/, crates/agentd/src/main.rs
```

For timeout on dev tools (Codex):
```
Read HANDOFF.md. Add timeout support to CodexTool and ClaudeCodeTool in crates/agent-devtools/src/lib.rs.
Read AGENT_OS_DEV_TIMEOUT_SECS from env (default 1800). Kill the subprocess and return an error result if exceeded.
Use tokio::time::timeout. Allowed paths: crates/agent-devtools/
```
