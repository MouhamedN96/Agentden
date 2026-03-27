use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevTask {
    pub objective: String,
    pub repo_path: String,
    pub cwd: String,
    pub allowed_paths: Vec<String>,
    pub forbidden_paths: Vec<String>,
    pub run_tests: bool,
    pub create_branch: bool,
    pub commit_if_success: bool,
    pub model_hint: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DevResult {
    pub success: bool,
    pub summary: String,
    pub files_changed: Vec<String>,
    pub branch: Option<String>,
    pub commit_sha: Option<String>,
    pub build_status: Option<String>,
    pub test_status: Option<String>,
    pub raw_log_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DevToolChoice {
    Codex,
    ClaudeCode,
    BothSequentially,
}
