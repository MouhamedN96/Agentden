/// ObsidianWriter — writes experiment notes as Obsidian markdown
///
/// Output structure in the vault:
///
///   <vault>/<vault_folder>/<program_name>/
///     _session_YYYY-MM-DD.md        ← session header with program context
///     _summary.md                   ← live-updated loop summary
///     gen_001_win_val_bpb_2.314.md  ← per-experiment note
///     gen_002_loss_val_bpb_2.401.md
///     experiments.jsonl             ← raw JSONL log (also agent-memory compatible)
///
/// Obsidian frontmatter tags make experiments queryable in Dataview:
///   ```dataview
///   TABLE generation, status, result_metric, delta
///   FROM "autoresearch/colbert-wolof"
///   SORT generation DESC
///   ```
use anyhow::Result;
use chrono::Utc;
use std::{fs, path::PathBuf};

use crate::{
    experiment::{Experiment, ExperimentStatus},
    program::ResearchProgram,
    r#loop::LoopSummary,
};

pub struct ObsidianWriter {
    notes_dir: PathBuf,
    recent: Vec<String>,
}

impl ObsidianWriter {
    pub fn new(program: &ResearchProgram) -> Result<Self> {
        let notes_dir = program.vault_notes_dir();
        fs::create_dir_all(&notes_dir)?;
        Ok(Self {
            notes_dir,
            recent: vec![],
        })
    }

    /// Write the session header note (program context + objectives)
    pub fn write_session_header(&self, program: &ResearchProgram, context: &str) -> Result<()> {
        let date = Utc::now().format("%Y-%m-%d_%H-%M").to_string();
        let filename = format!("_session_{}.md", date);
        let path = self.notes_dir.join(&filename);

        let content = format!(
            r#"---
tags: [autoresearch, session, {name}]
program: "{name}"
objective: "{objective}"
metric: "{metric}"
date: "{date}"
max_experiments: {max}
budget_secs: {budget}
route_policy: "{route}"
---

# Research Session: {name}

**Objective:** {objective}

**Metric:** `{metric}` ({direction})

**Budget:** {max} experiments × {budget}s each

---

## Program Context

{context}

---

*Session started: {date}*
"#,
            name = program.name,
            objective = program.objective,
            metric = program.metric.name,
            date = date,
            max = program.max_experiments,
            budget = program.budget_secs,
            route = program.route_policy,
            direction = format!("{:?}", program.metric.direction),
            context = context,
        );

        fs::write(&path, content)?;
        Ok(())
    }

    /// Write a note for a single experiment
    pub fn write_experiment_note(
        &mut self,
        program: &ResearchProgram,
        exp: &Experiment,
    ) -> Result<()> {
        let status_str = match exp.status {
            ExperimentStatus::Win => "win",
            ExperimentStatus::Loss => "loss",
            ExperimentStatus::Error => "error",
            _ => "unknown",
        };

        let metric_str = exp
            .result_metric
            .map(|v| format!("{:.4}", v).replace('.', "_"))
            .unwrap_or("none".into());

        let filename = format!(
            "gen_{:03}_{}_{}_{}.md",
            exp.generation, status_str, program.metric.name, metric_str
        );
        let path = self.notes_dir.join(&filename);

        let delta_str = exp
            .delta()
            .map(|d| format!("{:+.4}", d))
            .unwrap_or("N/A".into());

        let tags = format!(
            "[autoresearch, {}, {}, gen-{:03}]",
            program.name, status_str, exp.generation
        );

        let content = format!(
            r#"---
tags: {tags}
program: "{name}"
generation: {gen}
experiment_id: "{id}"
status: "{status}"
hypothesis: "{hyp}"
baseline_metric: {baseline}
result_metric: {result}
delta: "{delta}"
duration_ms: {dur}
created_at: "{created}"
---

# Gen {gen:03} — {status_upper}: {metric}={result_display}

**Hypothesis:** {hyp}

**Patch:** {patch}

## Result

| Field | Value |
|-------|-------|
| Status | {status_upper} |
| Baseline | {baseline_display} |
| Result | {result_display} |
| Delta | {delta} |
| Duration | {dur}ms |

## Output (tail)

```
{stdout}
```

{error_section}

---
*Experiment: `{id}`*
*[[_summary]] | [[_session]]*
"#,
            tags = tags,
            name = program.name,
            gen = exp.generation,
            id = exp.id,
            status = status_str,
            hyp = exp.hypothesis.replace('"', "'"),
            baseline = exp
                .baseline_metric
                .map(|v| format!("{}", v))
                .unwrap_or("null".into()),
            result = exp
                .result_metric
                .map(|v| format!("{}", v))
                .unwrap_or("null".into()),
            delta = delta_str,
            dur = exp.duration_ms,
            created = exp.created_at.format("%Y-%m-%d %H:%M:%S"),
            metric = program.metric.name,
            status_upper = status_str.to_uppercase(),
            patch = exp.patch_summary,
            baseline_display = exp
                .baseline_metric
                .map(|v| format!("{:.4}", v))
                .unwrap_or("(first run)".into()),
            result_display = exp
                .result_metric
                .map(|v| format!("{:.4}", v))
                .unwrap_or("N/A".into()),
            stdout = exp.stdout_tail,
            error_section = exp
                .error
                .as_ref()
                .map(|e| format!("## Error\n\n```\n{}\n```\n", e))
                .unwrap_or_default(),
        );

        fs::write(&path, content)?;

        // Track for recent summaries
        let summary = format!(
            "Gen {:03} {}: {} → {} (Δ{})",
            exp.generation,
            status_str.to_uppercase(),
            exp.baseline_metric
                .map(|v| format!("{:.4}", v))
                .unwrap_or("?".into()),
            exp.result_metric
                .map(|v| format!("{:.4}", v))
                .unwrap_or("?".into()),
            delta_str
        );
        self.recent.push(summary);

        Ok(())
    }

    /// Write/update the loop summary note
    pub fn write_loop_summary(
        &self,
        program: &ResearchProgram,
        summary: &LoopSummary,
    ) -> Result<()> {
        let path = self.notes_dir.join("_summary.md");
        let win_rate = if summary.total_experiments > 0 {
            (summary.wins as f64 / summary.total_experiments as f64) * 100.0
        } else {
            0.0
        };

        let content = format!(
            r#"---
tags: [autoresearch, summary, {name}]
program: "{name}"
total_experiments: {total}
wins: {wins}
losses: {losses}
errors: {errors}
win_rate: {win_rate:.1}
final_metric: {final_metric}
metric_name: "{metric}"
updated: "{now}"
---

# Research Summary: {name}

## Stats

| | Value |
|--|--|
| Total experiments | {total} |
| Wins | {wins} ✅ |
| Losses | {losses} ❌ |
| Errors | {errors} ⚠️ |
| Win rate | {win_rate:.1}% |
| Final {metric} | **{final_metric_display}** |

## Dataview: All Experiments

```dataview
TABLE generation, status, result_metric, delta, duration_ms
FROM "{vault_folder}/{name}"
WHERE file.name != "_summary" AND file.name != "_session"
SORT generation ASC
```

## Dataview: Wins Only

```dataview
TABLE generation, result_metric, delta
FROM "{vault_folder}/{name}"
WHERE status = "win"
SORT generation ASC
```

---
*Last updated: {now}*
"#,
            name = program.name,
            total = summary.total_experiments,
            wins = summary.wins,
            losses = summary.losses,
            errors = summary.errors,
            win_rate = win_rate,
            final_metric = summary
                .final_metric
                .map(|v| format!("{}", v))
                .unwrap_or("null".into()),
            final_metric_display = summary
                .final_metric
                .map(|v| format!("{:.4}", v))
                .unwrap_or("N/A".into()),
            metric = summary.metric_name,
            vault_folder = program.vault_folder,
            now = Utc::now().format("%Y-%m-%d %H:%M:%S"),
        );

        fs::write(&path, content)?;
        Ok(())
    }

    /// Return the last N experiment summaries as strings (for LLM context)
    pub fn recent_summaries(&self, n: usize) -> Vec<String> {
        let start = self.recent.len().saturating_sub(n);
        self.recent[start..].to_vec()
    }
}
