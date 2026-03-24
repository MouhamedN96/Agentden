use anyhow::{Context, Result};
use chrono::Utc;
use serde_json::json;
use std::{
    fs::{self, OpenOptions},
    io::Write,
    process::Command,
};

use crate::{experiment::Experiment, program::ResearchProgram};

pub struct TrackioLogger;

impl TrackioLogger {
    pub fn enabled(program: &ResearchProgram) -> bool {
        program.trackio.as_ref().map(|c| c.enabled).unwrap_or(false)
    }

    /// Logs each experiment to a local JSONL stream and (best-effort) to Trackio via Python API.
    pub fn log_experiment(program: &ResearchProgram, exp: &Experiment) -> Result<()> {
        if !Self::enabled(program) {
            return Ok(());
        }

        let cfg = program
            .trackio
            .as_ref()
            .context("trackio config missing despite enabled=true")?;

        let project = cfg.project.clone().unwrap_or_else(|| program.name.clone());
        let run_prefix = cfg
            .run_prefix
            .clone()
            .unwrap_or_else(|| program.name.clone());
        let run_name = format!("{}-gen-{:03}", run_prefix, exp.generation);

        let payload = json!({
            "timestamp": Utc::now(),
            "project": project,
            "run": run_name,
            "group": cfg.group,
            "space_id": cfg.space_id,
            "program": program.name,
            "generation": exp.generation,
            "experiment_id": exp.id,
            "status": exp.status,
            "hypothesis": exp.hypothesis,
            "metric_name": program.metric.name,
            "metric_value": exp.result_metric,
            "baseline": exp.baseline_metric,
            "delta": exp.delta(),
            "duration_ms": exp.duration_ms,
            "files_touched": exp.files_touched,
            "config": {
                "objective": program.objective,
                "route_policy": program.route_policy,
                "budget_secs": program.budget_secs,
                "min_delta": program.metric.min_delta,
            },
            "metrics": {
                (program.metric.name.clone()): exp.result_metric,
                "delta": exp.delta(),
                "duration_ms": exp.duration_ms,
            }
        });

        // Always write JSONL for deterministic, tool-agnostic ingestion.
        let log_path = program.trackio_log_path();
        if let Some(parent) = log_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let mut f = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_path)?;
        writeln!(f, "{}", payload)?;

        // Best-effort Trackio logging via Python API.
        let python_bin = cfg.python_bin.clone().unwrap_or_else(|| "python".into());
        let py = r#"
import json, os
payload = json.loads(os.environ["TRACKIO_PAYLOAD"])

import trackio

kwargs = {
    "project": payload["project"],
    "name": payload["run"],
    "config": payload["config"],
}
if payload.get("group"):
    kwargs["group"] = payload["group"]
if payload.get("space_id"):
    kwargs["space_id"] = payload["space_id"]

trackio.init(**kwargs)
metrics = {k: v for k, v in payload.get("metrics", {}).items() if v is not None}
if metrics:
    trackio.log(metrics)
trackio.finish()
"#;

        let status = Command::new(&python_bin)
            .arg("-c")
            .arg(py)
            .env("TRACKIO_PAYLOAD", payload.to_string())
            .current_dir(&program.repo_root)
            .status();

        match status {
            Ok(s) if s.success() => Ok(()),
            Ok(s) => anyhow::bail!("trackio python logging exited with status {s}"),
            Err(e) => anyhow::bail!("failed to invoke trackio python logging: {e}"),
        }
    }
}
