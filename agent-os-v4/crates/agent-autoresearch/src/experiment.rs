/// Experiment — a single hypothesis → patch → run → metric cycle
///
/// Lifecycle:
///   Pending → Running → Completed(Win|Loss|Error)
///
/// Each experiment:
///   1. Agent proposes a hypothesis (LLM call via agent-router)
///   2. Agent applies a patch to the editable file(s)
///   3. Runner executes the training/eval script with time budget
///   4. Metric is extracted from stdout/file
///   5. Compared to baseline → kept or reverted
///   6. Result written to JSONL log + Obsidian note
use anyhow::Result;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::{
    path::PathBuf,
    process::Stdio,
    time::{Duration, Instant},
};
use tokio::process::Command;
use uuid::Uuid;

use crate::metrics::MetricValue;
use crate::program::ResearchProgram;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ExperimentStatus {
    Pending,
    Running,
    Win,
    Loss,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Experiment {
    pub id: String,
    pub program_name: String,
    pub generation: usize,
    pub hypothesis: String,
    pub patch_summary: String,
    pub baseline_metric: Option<f64>,
    pub result_metric: Option<f64>,
    pub status: ExperimentStatus,
    pub duration_ms: u64,
    pub stdout_tail: String,
    pub error: Option<String>,
    pub created_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    /// Files that were modified in this experiment
    pub files_touched: Vec<PathBuf>,
}

#[derive(Debug)]
pub struct ExperimentResult {
    pub metric: Option<f64>,
    pub stdout: String,
    pub stderr: String,
    pub exit_code: Option<i32>,
    pub duration: Duration,
}

impl Experiment {
    pub fn new(program_name: &str, generation: usize, hypothesis: &str) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            program_name: program_name.to_string(),
            generation,
            hypothesis: hypothesis.to_string(),
            patch_summary: String::new(),
            baseline_metric: None,
            result_metric: None,
            status: ExperimentStatus::Pending,
            duration_ms: 0,
            stdout_tail: String::new(),
            error: None,
            created_at: Utc::now(),
            completed_at: None,
            files_touched: vec![],
        }
    }

    /// Run the experiment script and capture output + metric
    pub async fn run_script(
        &mut self,
        program: &ResearchProgram,
        script: &str,
        args: &[&str],
    ) -> Result<ExperimentResult> {
        self.status = ExperimentStatus::Running;
        let start = Instant::now();

        let timeout = Duration::from_secs(program.budget_secs);

        let output = tokio::time::timeout(
            timeout,
            Command::new(script)
                .args(args)
                .current_dir(&program.repo_root)
                .env("EXPERIMENT_ID", &self.id)
                .env("EXPERIMENT_GENERATION", self.generation.to_string())
                .env("METRIC_NAME", &program.metric.name)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .output(),
        )
        .await;

        let duration = start.elapsed();

        match output {
            Ok(Ok(out)) => {
                let stdout = String::from_utf8_lossy(&out.stdout).to_string();
                let stderr = String::from_utf8_lossy(&out.stderr).to_string();
                let exit_code = out.status.code();

                // Extract metric from stdout — looks for lines like:
                //   METRIC val_bpb=2.314
                //   val_bpb: 2.314
                let metric = extract_metric_from_output(&stdout, &program.metric.name);

                // Keep last 2000 chars of stdout for the note
                let tail_start = stdout.len().saturating_sub(2000);
                self.stdout_tail = stdout[tail_start..].to_string();
                self.duration_ms = duration.as_millis() as u64;

                Ok(ExperimentResult {
                    metric,
                    stdout,
                    stderr,
                    exit_code,
                    duration,
                })
            }
            Ok(Err(e)) => {
                self.status = ExperimentStatus::Error;
                self.error = Some(e.to_string());
                self.duration_ms = duration.as_millis() as u64;
                Err(e.into())
            }
            Err(_) => {
                // Timeout
                self.status = ExperimentStatus::Error;
                self.error = Some(format!(
                    "experiment timed out after {}s",
                    program.budget_secs
                ));
                self.duration_ms = duration.as_millis() as u64;
                Err(anyhow::anyhow!("experiment timed out"))
            }
        }
    }

    /// Finalize after comparing to baseline
    pub fn finalize(&mut self, result_metric: f64, is_win: bool) {
        self.result_metric = Some(result_metric);
        self.completed_at = Some(Utc::now());
        self.status = if is_win {
            ExperimentStatus::Win
        } else {
            ExperimentStatus::Loss
        };
    }

    pub fn mark_error(&mut self, err: &str) {
        self.status = ExperimentStatus::Error;
        self.error = Some(err.to_string());
        self.completed_at = Some(Utc::now());
    }

    /// Delta vs baseline (positive = improvement in the right direction)
    pub fn delta(&self) -> Option<f64> {
        match (self.baseline_metric, self.result_metric) {
            (Some(b), Some(r)) => Some(b - r), // caller interprets sign
            _ => None,
        }
    }

    pub fn as_metric_value(&self) -> Option<MetricValue> {
        self.result_metric.map(|v| MetricValue {
            name: format!("{}_gen{}", self.program_name, self.generation),
            value: v,
            generation: self.generation,
            experiment_id: self.id.clone(),
        })
    }
}

/// Extract a named metric from stdout.
/// Supports formats:
///   METRIC val_bpb=2.314
///   val_bpb: 2.314
///   {"val_bpb": 2.314}
fn extract_metric_from_output(stdout: &str, metric_name: &str) -> Option<f64> {
    for line in stdout.lines().rev() {
        // METRIC name=value
        if let Some(rest) = line.strip_prefix("METRIC ") {
            if let Some(val_str) = rest
                .split_whitespace()
                .find(|s| s.starts_with(metric_name))
                .and_then(|s| s.split('=').nth(1))
            {
                if let Ok(v) = val_str.parse::<f64>() {
                    return Some(v);
                }
            }
        }

        // name: value
        if line.trim_start().starts_with(metric_name) {
            if let Some(val_str) = line.split(':').nth(1) {
                if let Ok(v) = val_str.trim().parse::<f64>() {
                    return Some(v);
                }
            }
        }

        // JSON {"name": value}
        if line.contains(metric_name) && line.contains('{') {
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(line) {
                if let Some(num) = v.get(metric_name).and_then(|n| n.as_f64()) {
                    return Some(num);
                }
            }
        }
    }
    None
}
