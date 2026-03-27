use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, fs, path::Path, process::Command, time::Instant};
use tokio::task;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HookDefinition {
    pub name: String,
    pub event: String,
    pub command: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default = "default_enabled")]
    pub enabled: bool,
    /// Optional extra env vars injected into the hook process
    #[serde(default)]
    pub env: HashMap<String, String>,
}

fn default_enabled() -> bool {
    true
}

#[derive(Debug, Default)]
pub struct HookRegistry {
    pub hooks: Vec<HookDefinition>,
}

impl HookRegistry {
    pub fn load_file(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        if !path.exists() {
            return Ok(Self::default());
        }
        let data = fs::read_to_string(path)?;
        let hooks: Vec<HookDefinition> = serde_json::from_str(&data)?;
        Ok(Self { hooks })
    }

    pub fn for_event(&self, event: &str) -> Vec<&HookDefinition> {
        self.hooks
            .iter()
            .filter(|h| h.enabled && h.event == event)
            .collect()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HookRunResult {
    pub hook: String,
    pub event: String,
    /// "ok" | "failed" | "error" | "simulated"
    pub status: String,
    pub exit_code: Option<i32>,
    pub duration_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

/// Fire all hooks for an event **in parallel**, wait for all to complete.
/// Never panics — errors are captured in HookRunResult.
pub async fn fire_event_async(registry: &HookRegistry, event: &str) -> Vec<HookRunResult> {
    let definitions: Vec<HookDefinition> = registry.for_event(event).into_iter().cloned().collect();

    let event_owned = event.to_string();

    let handles: Vec<_> = definitions
        .into_iter()
        .map(|hook| {
            let event = event_owned.clone();
            task::spawn_blocking(move || run_hook(&hook, &event))
        })
        .collect();

    let mut results = Vec::with_capacity(handles.len());
    for handle in handles {
        match handle.await {
            Ok(r) => results.push(r),
            Err(e) => results.push(HookRunResult {
                hook: "unknown".into(),
                event: event_owned.clone(),
                status: "error".into(),
                exit_code: None,
                duration_ms: 0,
                error: Some(format!("task panicked: {e}")),
            }),
        }
    }
    results
}

/// Synchronous version (used by CLI `hooks fire` subcommand outside async context).
pub fn fire_event(registry: &HookRegistry, event: &str) -> Vec<HookRunResult> {
    registry
        .for_event(event)
        .into_iter()
        .map(|hook| run_hook(hook, event))
        .collect()
}

/// Dry-run path: shows what would execute without spawning processes.
pub fn simulate_event(registry: &HookRegistry, event: &str) -> Vec<HookRunResult> {
    registry
        .for_event(event)
        .into_iter()
        .map(|hook| HookRunResult {
            hook: hook.name.clone(),
            event: event.to_string(),
            status: "simulated".into(),
            exit_code: None,
            duration_ms: 0,
            error: Some(format!("would run: {} {:?}", hook.command, hook.args)),
        })
        .collect()
}

fn run_hook(hook: &HookDefinition, event: &str) -> HookRunResult {
    let t = Instant::now();

    let result = Command::new(&hook.command)
        .args(&hook.args)
        .envs(&hook.env)
        .env("AGENT_OS_EVENT", event)
        .env("AGENT_OS_HOOK", &hook.name)
        .spawn()
        .and_then(|mut child| child.wait());

    let duration_ms = t.elapsed().as_millis() as u64;

    match result {
        Ok(status) => {
            let code = status.code();
            let ok = status.success();
            HookRunResult {
                hook: hook.name.clone(),
                event: event.to_string(),
                status: if ok { "ok".into() } else { "failed".into() },
                exit_code: code,
                duration_ms,
                error: if ok {
                    None
                } else {
                    Some(format!("exited {:?}", code))
                },
            }
        }
        Err(e) => HookRunResult {
            hook: hook.name.clone(),
            event: event.to_string(),
            status: "error".into(),
            exit_code: None,
            duration_ms,
            error: Some(e.to_string()),
        },
    }
}
