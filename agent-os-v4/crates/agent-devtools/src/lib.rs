use agent_core::{DevResult, DevTask};
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use std::process::Command;

#[async_trait]
pub trait DevAgentTool: Send + Sync {
    fn name(&self) -> &'static str;
    async fn execute(&self, task: DevTask) -> Result<DevResult>;
}

pub struct CodexTool {
    pub binary: String,
}

pub struct ClaudeCodeTool {
    pub binary: String,
}

fn make_result(success: bool, summary: String) -> DevResult {
    DevResult {
        success,
        summary,
        files_changed: vec![],
        branch: None,
        commit_sha: None,
        build_status: None,
        test_status: None,
        raw_log_path: None,
    }
}

#[async_trait]
impl DevAgentTool for CodexTool {
    fn name(&self) -> &'static str {
        "codex"
    }
    async fn execute(&self, task: DevTask) -> Result<DevResult> {
        let prompt = format!(
            "Implement this task in the repo. Objective: {}. Allowed paths: {:?}. Run tests if needed and summarize changes.",
            task.objective, task.allowed_paths
        );
        let status = Command::new(&self.binary)
            .arg("exec")
            .arg(prompt)
            .current_dir(&task.cwd)
            .status()
            .map_err(|e| anyhow!("failed to start codex: {e}"))?;
        Ok(make_result(
            status.success(),
            format!("codex exited with {status}"),
        ))
    }
}

#[async_trait]
impl DevAgentTool for ClaudeCodeTool {
    fn name(&self) -> &'static str {
        "claude_code"
    }
    async fn execute(&self, task: DevTask) -> Result<DevResult> {
        let prompt = format!(
            "Analyze and implement this task. Objective: {}. Allowed paths: {:?}. Preserve the supervisor architecture.",
            task.objective, task.allowed_paths
        );
        let status = Command::new(&self.binary)
            .arg("-p")
            .arg(prompt)
            .current_dir(&task.cwd)
            .status()
            .map_err(|e| anyhow!("failed to start claude code: {e}"))?;
        Ok(make_result(
            status.success(),
            format!("claude code exited with {status}"),
        ))
    }
}

pub struct WorktreeManager;

impl WorktreeManager {
    pub fn branch_name(objective: &str) -> String {
        let slug = objective
            .to_lowercase()
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
            .collect::<String>();
        format!("agent/{}", slug.trim_matches('-'))
    }
}
