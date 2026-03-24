use anyhow::{Context, Result};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    process::Command,
};
use uuid::Uuid;

use crate::{
    experiment::{Experiment, ExperimentStatus},
    program::ResearchProgram,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelVersionRecord {
    pub version_id: String,
    pub created_at: chrono::DateTime<Utc>,
    pub program_name: String,
    pub experiment_id: String,
    pub generation: usize,
    pub metric_name: String,
    pub metric_value: Option<f64>,
    pub baseline_metric: Option<f64>,
    pub hypothesis: String,
    pub patch_summary: String,
    pub files_touched: Vec<String>,
    pub git_commit: Option<String>,
    pub artifact_snapshot: Option<PathBuf>,
}

pub struct ModelRegistry;

impl ModelRegistry {
    pub fn enabled(program: &ResearchProgram) -> bool {
        program
            .model_registry
            .as_ref()
            .map(|c| c.enabled)
            .unwrap_or(false)
    }

    /// Register a winning experiment as a model version.
    pub fn record_if_win(
        program: &ResearchProgram,
        exp: &Experiment,
    ) -> Result<Option<ModelVersionRecord>> {
        if !Self::enabled(program) || exp.status != ExperimentStatus::Win {
            return Ok(None);
        }

        let cfg = program
            .model_registry
            .as_ref()
            .context("model_registry config missing despite enabled=true")?;

        let version_id = format!(
            "{}-g{:03}-{}-{}",
            cfg.version_prefix,
            exp.generation,
            Utc::now().format("%Y%m%d%H%M%S"),
            &Uuid::new_v4().to_string()[..8]
        );

        let artifact_snapshot = if let Some(src) = program.model_artifact_path() {
            if src.exists() {
                let target_root = program.model_versions_dir().join(&version_id);
                fs::create_dir_all(&target_root)?;
                let target = target_root.join(
                    src.file_name()
                        .map(|n| n.to_string_lossy().to_string())
                        .unwrap_or_else(|| "artifact.bin".into()),
                );
                snapshot_path(&src, &target)?;
                Some(target)
            } else {
                None
            }
        } else {
            None
        };

        let record = ModelVersionRecord {
            version_id,
            created_at: Utc::now(),
            program_name: program.name.clone(),
            experiment_id: exp.id.clone(),
            generation: exp.generation,
            metric_name: program.metric.name.clone(),
            metric_value: exp.result_metric,
            baseline_metric: exp.baseline_metric,
            hypothesis: exp.hypothesis.clone(),
            patch_summary: exp.patch_summary.clone(),
            files_touched: exp
                .files_touched
                .iter()
                .map(|p| p.to_string_lossy().to_string())
                .collect(),
            git_commit: read_git_commit(&program.repo_root),
            artifact_snapshot,
        };

        let registry_path = program.model_registry_path();
        if let Some(parent) = registry_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let mut f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(registry_path)?;
        writeln!(f, "{}", serde_json::to_string(&record)?)?;

        Ok(Some(record))
    }
}

fn read_git_commit(repo_root: &Path) -> Option<String> {
    let output = Command::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(repo_root)
        .output()
        .ok()?;

    if !output.status.success() {
        return None;
    }

    let sha = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if sha.is_empty() {
        None
    } else {
        Some(sha)
    }
}

fn snapshot_path(src: &Path, dst: &Path) -> Result<()> {
    if src.is_file() {
        if let Some(parent) = dst.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(src, dst)?;
        return Ok(());
    }

    if src.is_dir() {
        copy_dir_all(src, dst)?;
        return Ok(());
    }

    anyhow::bail!("unsupported artifact path: {}", src.display())
}

fn copy_dir_all(src: &Path, dst: &Path) -> Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let src_path = entry.path();
        let dst_path = dst.join(entry.file_name());
        if src_path.is_dir() {
            copy_dir_all(&src_path, &dst_path)?;
        } else {
            fs::copy(&src_path, &dst_path)?;
        }
    }
    Ok(())
}
