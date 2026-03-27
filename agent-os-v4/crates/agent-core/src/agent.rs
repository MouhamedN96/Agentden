use crate::{DevResult, DevTask, DevToolChoice};

#[derive(Debug, Default)]
pub struct AgentSupervisor;

impl AgentSupervisor {
    pub fn choose_dev_tool(&self, task: &DevTask) -> DevToolChoice {
        let obj = task.objective.to_lowercase();
        if obj.contains("architecture") || obj.contains("debug") || obj.contains("repair") {
            DevToolChoice::ClaudeCode
        } else {
            DevToolChoice::Codex
        }
    }

    pub fn summarize(&self, result: &DevResult) -> String {
        format!(
            "success={} files_changed={} summary={}",
            result.success,
            result.files_changed.len(),
            result.summary
        )
    }
}
