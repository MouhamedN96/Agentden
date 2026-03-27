use agent_hooks::{fire_event, simulate_event, HookRegistry};
/// ExperimentLoop — the autonomous overnight research driver
///
/// This is the main loop that runs experiments, tracks the baseline,
/// calls the LLM for hypotheses, applies patches via supervised tools,
/// and writes results to the Obsidian vault.
///
/// Wiring into Agent-OS:
///   - Fires hooks via agent-hooks: "experiment.started", "experiment.completed", "loop.finished"
///   - Uses agent-router for LLM hypothesis generation (caller-provided callback)
///   - Uses agent-skills for the "autoresearch" skill prompt prelude (caller-provided callback)
///   - Writes JSONL to agent-memory TaskJournal-compatible path
use anyhow::{anyhow, Context, Result};
use serde_json::json;
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::PathBuf,
    process::Command,
};
use tracing::{debug, error, info, warn};

use crate::{
    experiment::{Experiment, ExperimentStatus},
    model_registry::ModelRegistry,
    obsidian::ObsidianWriter,
    program::{MetricDirection, ResearchProgram},
    trackio::TrackioLogger,
};

pub struct ExperimentLoop {
    pub program: ResearchProgram,
    pub program_context: String, // body of program.md after frontmatter
    obsidian: ObsidianWriter,
    generation: usize,
    baseline: Option<f64>,
    wins: usize,
    losses: usize,
    errors: usize,
    hooks: Option<HookRegistry>,
    dry_run_hooks: bool,
}

impl ExperimentLoop {
    pub fn new(program: ResearchProgram, program_context: String) -> Result<Self> {
        Self::new_with_hooks(program, program_context, None, false)
    }

    pub fn new_with_hooks(
        program: ResearchProgram,
        program_context: String,
        hooks: Option<HookRegistry>,
        dry_run_hooks: bool,
    ) -> Result<Self> {
        let obsidian = ObsidianWriter::new(&program)?;
        Ok(Self {
            program,
            program_context,
            obsidian,
            generation: 0,
            baseline: None,
            wins: 0,
            losses: 0,
            errors: 0,
            hooks,
            dry_run_hooks,
        })
    }

    /// Run the full autonomous loop.
    ///
    /// `hypothesis_fn`: async function that takes current context and returns
    /// hypothesis + patch instructions.
    /// `apply_patch_fn`: async function that receives a patch request and applies
    /// it via a supervised devtool (Codex/Claude Code) or a custom runner.
    pub async fn run<F, Fut, A, AFut>(
        &mut self,
        mut hypothesis_fn: F,
        mut apply_patch_fn: A,
        run_script: &str,
        run_args: &[&str],
    ) -> Result<LoopSummary>
    where
        F: FnMut(LoopContext) -> Fut,
        Fut: std::future::Future<Output = Result<HypothesisResponse>>,
        A: FnMut(PatchRequest) -> AFut,
        AFut: std::future::Future<Output = Result<()>>,
    {
        info!(
            "Starting autoresearch loop: {} | max_experiments={}",
            self.program.name, self.program.max_experiments
        );

        // Init vault dir
        fs::create_dir_all(self.program.vault_notes_dir())?;

        // Write loop session header note
        self.obsidian
            .write_session_header(&self.program, &self.program_context)?;

        for i in 0..self.program.max_experiments {
            self.generation = i + 1;

            info!(
                "Generation {} / {}",
                self.generation, self.program.max_experiments
            );

            // Build context for LLM
            let ctx = LoopContext {
                generation: self.generation,
                program_name: self.program.name.clone(),
                objective: self.program.objective.clone(),
                metric_name: self.program.metric.name.clone(),
                metric_direction: metric_direction_label(&self.program.metric.direction)
                    .to_string(),
                baseline: self.baseline,
                wins: self.wins,
                losses: self.losses,
                recent_experiments: self.obsidian.recent_summaries(5),
                program_context: self.program_context.clone(),
            };

            // Get hypothesis from LLM
            let hyp = match hypothesis_fn(ctx).await {
                Ok(h) => h,
                Err(e) => {
                    error!("hypothesis_fn failed: {e}");
                    self.errors += 1;
                    continue;
                }
            };

            let mut exp = Experiment::new(&self.program.name, self.generation, &hyp.hypothesis);
            exp.patch_summary = hyp.patch_summary.clone();
            exp.baseline_metric = self.baseline;

            // Fire hook: experiment.started
            self.fire_hook("experiment.started", &exp);

            // Apply patch through caller-provided executor
            let patch_request = PatchRequest {
                generation: self.generation,
                program_name: self.program.name.clone(),
                repo_root: self.program.repo_root.clone(),
                objective: self.program.objective.clone(),
                hypothesis: hyp.hypothesis.clone(),
                patch_summary: hyp.patch_summary.clone(),
                patch_instructions: hyp.patch_instructions,
                editable_files: self.program.editable_files.clone(),
                protected_files: self.program.protected_files.clone(),
            };

            if let Err(e) = apply_patch_fn(patch_request).await {
                error!("Gen {} patch apply failed: {e}", self.generation);
                exp.mark_error(&format!("patch apply failed: {e}"));
                self.errors += 1;
                self.revert_patch()?;
                self.finalize_experiment(&exp)?;
                continue;
            }

            // Validate touched files against editable/protected policy.
            let changed_files = self.collect_changed_files()?;
            exp.files_touched = changed_files.iter().map(PathBuf::from).collect();
            if let Err(e) = self.validate_touched_files(&changed_files) {
                error!("Gen {} patch policy violation: {e}", self.generation);
                exp.mark_error(&format!("patch policy violation: {e}"));
                self.errors += 1;
                self.revert_patch()?;
                self.finalize_experiment(&exp)?;
                continue;
            }

            // Run the experiment script
            match exp.run_script(&self.program, run_script, run_args).await {
                Ok(result) => {
                    if let Some(metric) = result.metric {
                        let is_win = match self.baseline {
                            Some(b) => self.program.metric.direction.is_improvement(
                                b,
                                metric,
                                self.program.metric.min_delta,
                            ),
                            None => true, // first run always sets baseline
                        };

                        exp.finalize(metric, is_win);

                        if self.baseline.is_none() || is_win {
                            info!(
                                "Gen {} WIN: {} → {} ({})",
                                self.generation,
                                self.baseline
                                    .map(|b| format!("{b:.4}"))
                                    .unwrap_or("(none)".into()),
                                metric,
                                self.program.metric.name
                            );
                            self.baseline = Some(metric);
                            self.wins += 1;
                        } else {
                            info!(
                                "Gen {} LOSS: {} vs baseline {:.4}",
                                self.generation,
                                metric,
                                self.baseline.unwrap_or_default()
                            );
                            self.losses += 1;
                            // Revert patch
                            self.revert_patch()?;
                        }
                    } else {
                        warn!("Gen {}: no metric found in output", self.generation);
                        exp.mark_error("metric not found in output");
                        self.errors += 1;
                        self.revert_patch()?;
                    }
                }
                Err(e) => {
                    error!("Gen {} run_script error: {e}", self.generation);
                    exp.mark_error(&e.to_string());
                    self.errors += 1;
                    self.revert_patch()?;
                }
            }

            self.finalize_experiment(&exp)?;
        }

        let summary = LoopSummary {
            program_name: self.program.name.clone(),
            total_experiments: self.generation,
            wins: self.wins,
            losses: self.losses,
            errors: self.errors,
            final_metric: self.baseline,
            metric_name: self.program.metric.name.clone(),
        };

        // Write final summary note
        self.obsidian.write_loop_summary(&self.program, &summary)?;

        // Fire hook: loop.finished
        self.fire_hook_raw("loop.finished", &serde_json::to_value(&summary)?);

        info!(
            "Loop finished: {} wins / {} losses / {} errors | final {}={:?}",
            self.wins, self.losses, self.errors, self.program.metric.name, self.baseline
        );

        Ok(summary)
    }

    fn finalize_experiment(&mut self, exp: &Experiment) -> Result<()> {
        // Write to JSONL log
        self.append_jsonl(exp)?;

        // Write Obsidian note for this experiment
        self.obsidian.write_experiment_note(&self.program, exp)?;

        if let Err(e) = TrackioLogger::log_experiment(&self.program, exp) {
            warn!("trackio logging failed for gen {}: {e}", exp.generation);
        }

        if exp.status == ExperimentStatus::Win {
            if let Err(e) = ModelRegistry::record_if_win(&self.program, exp) {
                warn!(
                    "model version registration failed for gen {}: {e}",
                    exp.generation
                );
            }
        }

        // Fire hook: experiment.completed
        self.fire_hook("experiment.completed", exp);

        Ok(())
    }

    fn collect_changed_files(&self) -> Result<Vec<String>> {
        let mut changed: Vec<String> = Vec::new();

        let diff_sets: &[&[&str]] = &[
            &["diff", "--name-only"],
            &["diff", "--name-only", "--cached"],
        ];
        for args in diff_sets {
            let output = Command::new("git")
                .args(*args)
                .current_dir(&self.program.repo_root)
                .output()
                .with_context(|| "running git diff --name-only")?;

            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                return Err(anyhow!("git diff failed: {}", stderr.trim()));
            }

            for line in String::from_utf8_lossy(&output.stdout).lines() {
                let file = line.trim();
                if !file.is_empty() && !changed.iter().any(|f| f == file) {
                    changed.push(file.to_string());
                }
            }
        }

        Ok(changed)
    }

    fn validate_touched_files(&self, changed_files: &[String]) -> Result<()> {
        for file in changed_files {
            if self
                .program
                .protected_files
                .iter()
                .any(|rule| path_matches_rule(file, rule))
            {
                return Err(anyhow!("patch touched protected path: {file}"));
            }

            if !self.program.editable_files.is_empty()
                && !self
                    .program
                    .editable_files
                    .iter()
                    .any(|rule| path_matches_rule(file, rule))
            {
                return Err(anyhow!("patch touched path outside editable_files: {file}"));
            }
        }

        Ok(())
    }

    fn revert_patch(&self) -> Result<()> {
        let changed_files = match self.collect_changed_files() {
            Ok(files) if !files.is_empty() => files,
            Ok(_) => self.program.editable_files.clone(),
            Err(e) => {
                warn!("failed to enumerate changed files for revert: {e}");
                self.program.editable_files.clone()
            }
        };

        for file in &changed_files {
            let status = Command::new("git")
                .args(["checkout", "HEAD", "--", file])
                .current_dir(&self.program.repo_root)
                .status();
            if let Err(e) = status {
                warn!("git checkout revert failed for {file}: {e}");
            }
        }
        Ok(())
    }

    fn append_jsonl(&self, exp: &Experiment) -> Result<()> {
        let log_path = self.program.experiment_log_path();
        let parent = log_path
            .parent()
            .ok_or_else(|| anyhow!("experiment_log_path has no parent directory"))?;
        fs::create_dir_all(parent)?;
        let mut f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_path)?;
        let line = serde_json::to_string(exp)?;
        writeln!(f, "{}", line)?;
        Ok(())
    }

    fn fire_hook(&self, event: &str, exp: &Experiment) {
        let payload = json!({
            "event": event,
            "experiment_id": exp.id,
            "generation": exp.generation,
            "program": exp.program_name,
            "status": exp.status,
            "metric": exp.result_metric,
            "baseline": exp.baseline_metric,
            "files_touched": exp.files_touched,
        });
        self.fire_hook_raw(event, &payload);
    }

    fn fire_hook_raw(&self, event: &str, payload: &serde_json::Value) {
        let Some(registry) = &self.hooks else {
            debug!("hook event (no registry): {} payload={}", event, payload);
            return;
        };

        let results = if self.dry_run_hooks {
            simulate_event(registry, event)
        } else {
            fire_event(registry, event)
        };

        for r in results {
            if r.status != "ok" && r.status != "simulated" {
                warn!(
                    "hook {} for event {} returned status {} ({:?})",
                    r.hook, event, r.status, r.error
                );
            }
        }
    }
}

fn path_matches_rule(path: &str, rule: &str) -> bool {
    let normalized_path = path.replace('\\', "/");
    let mut normalized_rule = rule.replace('\\', "/");

    if normalized_rule.is_empty() {
        return false;
    }

    while normalized_rule.ends_with('/') {
        normalized_rule.pop();
    }

    normalized_path == normalized_rule || normalized_path.starts_with(&(normalized_rule + "/"))
}

fn metric_direction_label(direction: &MetricDirection) -> &'static str {
    match direction {
        MetricDirection::LowerIsBetter => "lower",
        MetricDirection::HigherIsBetter => "higher",
    }
}

#[derive(Debug, Clone)]
pub struct PatchRequest {
    pub generation: usize,
    pub program_name: String,
    pub repo_root: PathBuf,
    pub objective: String,
    pub hypothesis: String,
    pub patch_summary: String,
    pub patch_instructions: String,
    pub editable_files: Vec<String>,
    pub protected_files: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct LoopContext {
    pub generation: usize,
    pub program_name: String,
    pub objective: String,
    pub metric_name: String,
    pub metric_direction: String,
    pub baseline: Option<f64>,
    pub wins: usize,
    pub losses: usize,
    pub recent_experiments: Vec<String>,
    pub program_context: String,
}

impl LoopContext {
    /// Build the system prompt for the LLM hypothesis call
    pub fn to_system_prompt(&self) -> String {
        format!(
            r#"You are an autonomous research agent optimizing: {objective}

Metric: {metric} ({direction} is better)
Current baseline: {baseline}
Session: generation {gen} | {wins} wins, {losses} losses so far

Research context:
{context}

Recent experiments:
{recent}

Your task: Propose ONE concrete hypothesis to improve {metric}.
- Be specific about what to change and why
- Learn from what has worked/failed
- Make incremental changes — one thing at a time
"#,
            objective = self.objective,
            metric = self.metric_name,
            direction = self.metric_direction,
            baseline = self
                .baseline
                .map(|b| format!("{b:.4}"))
                .unwrap_or("not yet measured".into()),
            gen = self.generation,
            wins = self.wins,
            losses = self.losses,
            context = self.program_context,
            recent = self.recent_experiments.join("\n"),
        )
    }
}

#[derive(Debug)]
pub struct HypothesisResponse {
    pub hypothesis: String,
    pub patch_instructions: String,
    pub patch_summary: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct LoopSummary {
    pub program_name: String,
    pub total_experiments: usize,
    pub wins: usize,
    pub losses: usize,
    pub errors: usize,
    pub final_metric: Option<f64>,
    pub metric_name: String,
}
