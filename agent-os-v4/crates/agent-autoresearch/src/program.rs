/// ResearchProgram — loaded from program.md
///
/// This mirrors Karpathy's program.md concept but extended:
/// - Defines the research objective and metric to optimize
/// - Specifies what files the agent is allowed to modify
/// - Sets the budget (time per run, max experiments)
/// - Defines Obsidian vault path and NotebookLM export settings
/// - Adds optional Trackio logging and model versioning
/// - Maps to an Agent-OS skill for agent pickup
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::{
    fs,
    path::{Path, PathBuf},
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResearchProgram {
    /// Short name, used as Obsidian folder name
    pub name: String,

    /// What are we trying to improve? Free text, injected into every LLM prompt
    pub objective: String,

    /// The metric we're optimizing. Lower or higher?
    pub metric: MetricConfig,

    /// Files the agent is permitted to edit (relative to repo_root)
    pub editable_files: Vec<String>,

    /// Files the agent must never touch
    #[serde(default)]
    pub protected_files: Vec<String>,

    /// Max wall-clock seconds per experiment run
    #[serde(default = "default_budget_secs")]
    pub budget_secs: u64,

    /// Max number of experiments per loop session
    #[serde(default = "default_max_experiments")]
    pub max_experiments: usize,

    /// Root of the repo being researched
    pub repo_root: PathBuf,

    /// Obsidian vault path — where notes are written
    pub obsidian_vault: PathBuf,

    /// Subfolder inside the vault for this research program
    #[serde(default = "default_vault_folder")]
    pub vault_folder: String,

    /// Optional: webhook URL to POST experiment results to
    #[serde(skip_serializing_if = "Option::is_none")]
    pub webhook_url: Option<String>,

    /// NotebookLM export: path to write the export bundle zip
    #[serde(skip_serializing_if = "Option::is_none")]
    pub notebooklm_export_path: Option<PathBuf>,

    /// Agent-OS router policy for LLM calls in this loop
    /// Maps to agent-router RoutePolicy names: "Cheap", "Balanced", "Premium"
    #[serde(default = "default_route_policy")]
    pub route_policy: String,

    /// Optional Trackio experiment tracking.
    #[serde(default)]
    pub trackio: Option<TrackioConfig>,

    /// Optional model versioning registry for winning experiments.
    #[serde(default)]
    pub model_registry: Option<ModelRegistryConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricConfig {
    /// Name shown in notes and logs (e.g. "val_bpb", "retrieval_mrr", "latency_ms")
    pub name: String,

    /// "lower_is_better" or "higher_is_better"
    pub direction: MetricDirection,

    /// Minimum improvement delta to consider an experiment a "win"
    #[serde(default = "default_min_delta")]
    pub min_delta: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum MetricDirection {
    LowerIsBetter,
    HigherIsBetter,
}

impl MetricDirection {
    pub fn is_improvement(&self, baseline: f64, candidate: f64, min_delta: f64) -> bool {
        match self {
            MetricDirection::LowerIsBetter => baseline - candidate >= min_delta,
            MetricDirection::HigherIsBetter => candidate - baseline >= min_delta,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct TrackioConfig {
    #[serde(default)]
    pub enabled: bool,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub project: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub run_prefix: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub group: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub space_id: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub python_bin: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub log_path: Option<PathBuf>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelRegistryConfig {
    #[serde(default)]
    pub enabled: bool,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub registry_path: Option<PathBuf>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub versions_dir: Option<PathBuf>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub artifact_path: Option<PathBuf>,

    #[serde(default = "default_version_prefix")]
    pub version_prefix: String,
}

impl Default for ModelRegistryConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            registry_path: None,
            versions_dir: None,
            artifact_path: None,
            version_prefix: default_version_prefix(),
        }
    }
}

fn default_budget_secs() -> u64 {
    300
} // 5 minutes, matching Karpathy
fn default_max_experiments() -> usize {
    100
}
fn default_vault_folder() -> String {
    "autoresearch".into()
}
fn default_route_policy() -> String {
    "Cheap".into()
}
fn default_min_delta() -> f64 {
    0.001
}
fn default_version_prefix() -> String {
    "model".into()
}

impl ResearchProgram {
    /// Load from a program.md file using TOML frontmatter fenced with ---
    /// The rest of the file after frontmatter is treated as free-text context
    /// injected into the agent's system prompt.
    pub fn load(path: impl AsRef<Path>) -> Result<(Self, String)> {
        let path = path.as_ref();
        let raw = fs::read_to_string(path)
            .with_context(|| format!("reading program.md at {}", path.display()))?;

        // Parse TOML frontmatter between --- delimiters
        let (frontmatter, body) = parse_frontmatter(&raw)?;
        let program: Self = toml::from_str(&frontmatter)
            .with_context(|| "parsing program.md frontmatter as TOML")?;

        Ok((program, body))
    }

    /// Vault path for this program's notes folder
    pub fn vault_notes_dir(&self) -> PathBuf {
        self.obsidian_vault
            .join(&self.vault_folder)
            .join(&self.name)
    }

    /// Path for the experiment JSONL log
    pub fn experiment_log_path(&self) -> PathBuf {
        self.vault_notes_dir().join("experiments.jsonl")
    }

    /// Path for Trackio-compatible local event log.
    pub fn trackio_log_path(&self) -> PathBuf {
        let default = self.vault_notes_dir().join("trackio_events.jsonl");
        self.trackio
            .as_ref()
            .and_then(|c| c.log_path.clone())
            .map(|p| self.resolve_path(p))
            .unwrap_or(default)
    }

    /// Path for append-only model registry index.
    pub fn model_registry_path(&self) -> PathBuf {
        let default = self
            .repo_root
            .join(".agent-os")
            .join("model_registry.jsonl");
        self.model_registry
            .as_ref()
            .and_then(|c| c.registry_path.clone())
            .map(|p| self.resolve_path(p))
            .unwrap_or(default)
    }

    /// Root folder where model version snapshots are stored.
    pub fn model_versions_dir(&self) -> PathBuf {
        let default = self.repo_root.join(".agent-os").join("model_versions");
        self.model_registry
            .as_ref()
            .and_then(|c| c.versions_dir.clone())
            .map(|p| self.resolve_path(p))
            .unwrap_or(default)
    }

    /// Optional artifact path to snapshot for winning experiments.
    pub fn model_artifact_path(&self) -> Option<PathBuf> {
        self.model_registry
            .as_ref()
            .and_then(|c| c.artifact_path.clone())
            .map(|p| self.resolve_path(p))
    }

    fn resolve_path(&self, path: PathBuf) -> PathBuf {
        if path.is_absolute() {
            path
        } else {
            self.repo_root.join(path)
        }
    }
}

fn parse_frontmatter(raw: &str) -> Result<(String, String)> {
    let lines: Vec<&str> = raw.lines().collect();
    if lines.first().map(|l| l.trim()) != Some("---") {
        anyhow::bail!("program.md must start with --- TOML frontmatter");
    }
    let end = lines[1..]
        .iter()
        .position(|l| l.trim() == "---")
        .map(|i| i + 1)
        .ok_or_else(|| anyhow::anyhow!("program.md frontmatter not closed with ---"))?;

    let frontmatter = lines[1..end].join("\n");
    let body = lines[end + 1..].join("\n");
    Ok((frontmatter, body))
}
