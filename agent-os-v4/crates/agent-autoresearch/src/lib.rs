pub mod experiment;
pub mod r#loop;
pub mod metrics;
pub mod model_registry;
pub mod notebooklm;
pub mod obsidian;
/// agent-autoresearch
///
/// Autonomous research arm for Agent-OS.
/// Inspired by karpathy/autoresearch — but wired into the Agent-OS skill/hook/router stack
/// and outputs structured Obsidian notes + NotebookLM-compatible export bundles.
///
/// Architecture:
///   ResearchProgram  — loaded from program.md (what the agent is researching)
///   Experiment       — a single hypothesis → run → metric cycle
///   ExperimentLoop   — the autonomous overnight driver
///   ObsidianWriter   — writes experiment notes as Obsidian markdown to vault
///   NotebookLMExport — bundles research notes into a NotebookLM-uploadable zip
///
/// Integration points with Agent-OS v4:
///   - Uses agent-hooks to fire "experiment.started" / "experiment.completed" events
///   - Uses agent-router for LLM calls (hypothesis generation, analysis)
///   - Uses agent-skills to load the "autoresearch" skill definition
///   - Uses agent-memory (TaskJournal) for JSONL experiment log
///   - Uses agent-scheduler to trigger nightly loops
pub mod program;
pub mod trackio;

pub use experiment::{Experiment, ExperimentResult, ExperimentStatus};
pub use metrics::MetricValue;
pub use model_registry::{ModelRegistry, ModelVersionRecord};
pub use notebooklm::NotebookLMExport;
pub use obsidian::ObsidianWriter;
pub use program::{ModelRegistryConfig, ResearchProgram, TrackioConfig};
pub use r#loop::{ExperimentLoop, HypothesisResponse, LoopContext, LoopSummary, PatchRequest};
pub use trackio::TrackioLogger;
