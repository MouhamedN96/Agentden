/// NotebookLMExport — bundles Obsidian research notes into a NotebookLM-uploadable package
///
/// NotebookLM has no public API (as of March 2026), so integration is file-based:
///
/// 1. EXPORT:  Collects all .md notes from the vault folder → writes a zip bundle
///             Each note becomes a "source" document in NotebookLM
///
/// 2. WATCH:   Optional file watcher — when vault folder changes, auto-rebuild export zip
///             (Uses the `notify` crate)
///
/// 3. DIGEST:  Generates a single consolidated research-digest.md that can be uploaded
///             as one NotebookLM source with full experiment history
///
/// Upload workflow (manual):
///   1. Loop finishes → export zip written to notebooklm_export_path
///   2. Open NotebookLM → New Notebook → Upload files from zip
///   3. Ask: "What's the best hypothesis for the next round of experiments?"
///   4. Feed answer back into program.md context for next session
///
/// For Obsidian → NotebookLM sync, the recommended workflow is:
///   obsidian-to-notebooklm plugin (community) OR manual upload of digest.md
use anyhow::Result;
use chrono::Utc;
use std::{
    fs,
    io::{Read, Write},
    path::PathBuf,
};

use crate::program::ResearchProgram;

pub struct NotebookLMExport;

impl NotebookLMExport {
    /// Build a zip bundle of all experiment notes for NotebookLM upload
    pub fn build_zip(program: &ResearchProgram) -> Result<PathBuf> {
        let export_path = match &program.notebooklm_export_path {
            Some(p) => p.clone(),
            None => program
                .vault_notes_dir()
                .parent()
                .unwrap()
                .join(format!("{}-notebooklm-export.zip", program.name)),
        };

        let notes_dir = program.vault_notes_dir();
        if !notes_dir.exists() {
            anyhow::bail!("vault notes dir does not exist: {}", notes_dir.display());
        }

        let file = fs::File::create(&export_path)?;
        let mut zip = zip::ZipWriter::new(file);
        let options = zip::write::SimpleFileOptions::default()
            .compression_method(zip::CompressionMethod::Deflated);

        for entry in fs::read_dir(&notes_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.extension().and_then(|e| e.to_str()) == Some("md") {
                let filename = path.file_name().unwrap().to_string_lossy();
                let mut content = String::new();
                fs::File::open(&path)?.read_to_string(&mut content)?;
                zip.start_file(filename.as_ref(), options)?;
                zip.write_all(content.as_bytes())?;
            }
        }

        zip.finish()?;

        tracing::info!("NotebookLM export written: {}", export_path.display());

        Ok(export_path)
    }

    /// Generate a single consolidated research digest markdown file
    /// Suitable for uploading as ONE NotebookLM source with full history
    pub fn build_digest(program: &ResearchProgram) -> Result<PathBuf> {
        let notes_dir = program.vault_notes_dir();
        let digest_path = notes_dir.join("_notebooklm_digest.md");

        let mut digest = format!(
            r#"# Research Digest: {}

**Objective:** {}
**Metric:** {} ({:?})
**Generated:** {}

This document is a consolidated export of all autoresearch experiments for NotebookLM analysis.

---

"#,
            program.name,
            program.objective,
            program.metric.name,
            program.metric.direction,
            Utc::now().format("%Y-%m-%d %H:%M:%S"),
        );

        // Append all experiment notes sorted by name (gen_001, gen_002, ...)
        let mut notes: Vec<PathBuf> = fs::read_dir(&notes_dir)?
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .filter(|p| {
                p.extension().and_then(|e| e.to_str()) == Some("md")
                    && p.file_name()
                        .and_then(|n| n.to_str())
                        .map(|n| n.starts_with("gen_"))
                        .unwrap_or(false)
            })
            .collect();
        notes.sort();

        for note_path in notes {
            let mut content = String::new();
            fs::File::open(&note_path)?.read_to_string(&mut content)?;
            digest.push_str(&content);
            digest.push_str("\n\n---\n\n");
        }

        // Append NotebookLM prompt suggestions
        digest.push_str(&format!(
            r#"
## Suggested NotebookLM Queries

1. What patterns emerge from the winning experiments vs losing experiments?
2. What hypothesis should we try next to improve {}?
3. What have we ruled out so far?
4. What is the most impactful change we've made?
5. Summarize the research trajectory from generation 1 to the latest.
"#,
            program.metric.name
        ));

        fs::write(&digest_path, &digest)?;
        tracing::info!("NotebookLM digest written: {}", digest_path.display());

        Ok(digest_path)
    }

    /// Watch the vault folder and rebuild export on changes
    /// Returns a JoinHandle — cancel it to stop watching
    pub fn watch_and_export(program: ResearchProgram) -> tokio::task::JoinHandle<()> {
        tokio::spawn(async move {
            use notify::{Config, RecommendedWatcher, RecursiveMode, Watcher};
            use std::sync::mpsc;

            let (tx, rx) = mpsc::channel();
            let notes_dir = program.vault_notes_dir();

            let mut watcher = match RecommendedWatcher::new(tx, Config::default()) {
                Ok(w) => w,
                Err(e) => {
                    tracing::error!("watcher setup failed: {e}");
                    return;
                }
            };

            if let Err(e) = watcher.watch(&notes_dir, RecursiveMode::Recursive) {
                tracing::error!("watcher.watch failed: {e}");
                return;
            }

            tracing::info!("Watching vault for changes: {}", notes_dir.display());

            loop {
                match rx.recv() {
                    Ok(_event) => {
                        // Debounce: small sleep to batch rapid changes
                        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
                        if let Err(e) = Self::build_digest(&program) {
                            tracing::warn!("digest rebuild failed: {e}");
                        }
                        if let Err(e) = Self::build_zip(&program) {
                            tracing::warn!("zip rebuild failed: {e}");
                        }
                    }
                    Err(e) => {
                        tracing::error!("watcher channel error: {e}");
                        break;
                    }
                }
            }
        })
    }
}
