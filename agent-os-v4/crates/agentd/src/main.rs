use anyhow::{anyhow, Result};
use clap::{Parser, Subcommand, ValueEnum};
use std::{collections::HashMap, path::PathBuf};
use tracing_subscriber::{fmt, EnvFilter};

use agent_autoresearch::{
    ExperimentLoop, HypothesisResponse, LoopContext, NotebookLMExport, PatchRequest,
    ResearchProgram,
};
use agent_core::DevTask;
use agent_devtools::{ClaudeCodeTool, CodexTool, DevAgentTool};
use agent_hooks::{fire_event_async, simulate_event, HookRegistry};
use agent_plugins::PluginRegistry;
use agent_router::{LocalRouter, RoutePolicy};
use agent_skills::SkillRegistry;

// ── CLI definition ─────────────────────────────────────────────────────────

#[derive(Debug, Parser)]
#[command(name = "agentd", version, about = "Personal Agent OS supervisor")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Subcommand)]
enum Commands {
    /// Start the supervisor daemon (placeholder)
    Run,

    /// Dispatch a dev task to Codex or Claude Code
    Devtask {
        #[arg(long, help = "Dev tool to use")]
        tool: Option<ToolName>,
        #[arg(long, help = "Absolute path to repo")]
        repo: Option<String>,
        #[arg(long, help = "What to build or fix")]
        objective: Option<String>,
        #[arg(long, help = "Paths the tool is allowed to touch")]
        allowed_path: Vec<String>,
        #[arg(long, help = "Skill name to inject as prompt prelude")]
        skill: Option<String>,
        #[arg(
            long,
            default_value_t = false,
            help = "Simulate hooks without executing them"
        )]
        dry_run: bool,
        #[arg(
            long,
            default_value_t = false,
            help = "List skills matching objective, then exit"
        )]
        list_skills: bool,
    },

    /// Run the autonomous research loop from a program.md
    Research {
        #[arg(
            long,
            default_value = "skills/autoresearch/program.md",
            help = "Path to research program markdown"
        )]
        program: String,
        #[arg(long, help = "Experiment runner script/binary path")]
        run_script: String,
        #[arg(long, help = "Runner argument (repeatable)")]
        run_arg: Vec<String>,
        #[arg(long, help = "Dev tool for patch application")]
        tool: Option<ToolName>,
        #[arg(
            long,
            default_value_t = false,
            help = "Simulate hooks without executing them"
        )]
        dry_run_hooks: bool,
        #[arg(
            long,
            default_value_t = false,
            help = "Enable Trackio logging for this run"
        )]
        trackio: bool,
        #[arg(long, help = "Override model registry JSONL path")]
        model_registry_path: Option<String>,
    },

    /// MCP server management
    Mcp {
        #[arg(default_value = "serve")]
        action: String,
    },

    /// Skill management
    Skills {
        #[command(subcommand)]
        command: SkillsCommand,
    },

    /// Hook management
    Hooks {
        #[command(subcommand)]
        command: HooksCommand,
    },

    /// Plugin management
    Plugins {
        #[command(subcommand)]
        command: PluginsCommand,
    },

    /// LLM router inspection
    Router {
        #[command(subcommand)]
        command: RouterCommand,
    },
}

#[derive(Debug, Subcommand)]
enum SkillsCommand {
    /// List all available skills
    List,
    /// Suggest skills matching an objective
    Suggest {
        #[arg(long)]
        objective: String,
    },
}

#[derive(Debug, Subcommand)]
enum HooksCommand {
    /// Simulate (dry-run) hooks for a given event
    Simulate {
        #[arg(long)]
        event: String,
    },
    /// Actually fire hooks for a given event
    Fire {
        #[arg(long)]
        event: String,
    },
}

#[derive(Debug, Subcommand)]
enum PluginsCommand {
    /// List available plugins and their capabilities
    List,
    /// Invoke a plugin by name
    Invoke {
        #[arg(long)]
        name: String,
        /// Extra context as KEY=VALUE pairs passed as PLUGIN_CTX_<KEY> env vars
        #[arg(long, value_parser = parse_kv)]
        ctx: Vec<(String, String)>,
    },
}

#[derive(Debug, Subcommand)]
enum RouterCommand {
    /// Show configured LLM endpoints from environment
    Show,
    /// Show the cascade chain for a given policy
    Cascade {
        #[arg(long, default_value = "cheap")]
        policy: PolicyArg,
    },
}

#[derive(Debug, Clone, ValueEnum)]
enum ToolName {
    Codex,
    ClaudeCode,
}

#[derive(Debug, Clone, ValueEnum)]
enum PolicyArg {
    Offline,
    Cheap,
    Balanced,
    Premium,
    Fallback,
}

impl From<PolicyArg> for RoutePolicy {
    fn from(p: PolicyArg) -> Self {
        match p {
            PolicyArg::Offline => RoutePolicy::OfflineFirst,
            PolicyArg::Cheap => RoutePolicy::Cheap,
            PolicyArg::Balanced => RoutePolicy::Balanced,
            PolicyArg::Premium => RoutePolicy::Premium,
            PolicyArg::Fallback => RoutePolicy::Fallback,
        }
    }
}

fn parse_kv(s: &str) -> Result<(String, String), String> {
    s.split_once('=')
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .ok_or_else(|| format!("expected KEY=VALUE, got: {s}"))
}

// ── Entry point ────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    fmt().with_env_filter(EnvFilter::from_default_env()).init();
    let cli = Cli::parse();

    match cli.command {
        // ── Run ───────────────────────────────────────────────────────────
        Commands::Run => {
            let data_dir = std::env::var("AGENT_OS_DATA_DIR").unwrap_or_else(|_| "./data".into());
            for sub in &["logs", "sessions", "cache"] {
                std::fs::create_dir_all(format!("{data_dir}/{sub}"))?;
            }
            println!("agentd supervisor starting (data: {data_dir})");
        }

        Commands::Devtask {
            tool,
            repo,
            objective,
            allowed_path,
            skill,
            dry_run,
            list_skills,
        } => {
            let skills = SkillRegistry::load_dir("skills")?;

            // --list-skills: show matching skills for the objective and exit
            if list_skills {
                let obj = objective.as_deref().unwrap_or("");
                let matches = if obj.is_empty() {
                    skills.list()
                } else {
                    skills.suggest(obj)
                };
                if matches.is_empty() {
                    println!("No skills match: {obj}");
                    println!("All available skills:");
                    for s in skills.list() {
                        println!("  {}  —  {}", s.manifest.name, s.manifest.description);
                        println!("    triggers: {}", s.manifest.triggers.join(", "));
                    }
                } else {
                    println!("Matching skills for \"{}\":", obj);
                    for s in &matches {
                        println!();
                        println!("  name:        {}", s.manifest.name);
                        println!("  description: {}", s.manifest.description);
                        println!("  triggers:    {}", s.manifest.triggers.join(", "));
                        println!("  tools:       {}", s.manifest.tools.join(", "));
                        if let Some(prelude) = &s.manifest.prompt_prelude {
                            println!("  prelude:     {prelude}");
                        }
                    }
                    println!();
                    println!("Re-run with --skill {} to apply.", matches[0].manifest.name);
                }
                return Ok(());
            }

            // Normal dispatch path — tool/repo/objective are required
            let tool = tool.ok_or_else(|| anyhow!("--tool is required (codex or claude-code)"))?;
            let repo = repo.ok_or_else(|| anyhow!("--repo is required"))?;
            let objective = objective.ok_or_else(|| anyhow!("--objective is required"))?;

            let hooks = HookRegistry::load_file("config/hooks/hooks.json")?;

            emit_hooks(&hooks, "devtask.started", dry_run).await;

            let objective = if let Some(skill_name) = skill.as_deref() {
                let s = skills
                    .get(skill_name)
                    .ok_or_else(|| anyhow!("skill not found: {skill_name}"))?;
                if let Some(prelude) = &s.manifest.prompt_prelude {
                    format!("{}\n\nTask:\n{}", prelude, objective)
                } else {
                    objective
                }
            } else {
                // Auto-suggest skill if one matches and none was specified
                let suggestions = skills.suggest(&objective);
                if !suggestions.is_empty() {
                    eprintln!(
                        "[skills] tip: skill '{}' matches this objective. Re-run with --skill {} to apply.",
                        suggestions[0].manifest.name, suggestions[0].manifest.name
                    );
                }
                objective
            };

            let task = DevTask {
                objective,
                repo_path: repo.clone(),
                cwd: repo,
                allowed_paths: allowed_path,
                forbidden_paths: vec![],
                run_tests: true,
                create_branch: true,
                commit_if_success: false,
                model_hint: None,
            };

            let result = match tool {
                ToolName::Codex => {
                    let t = CodexTool {
                        binary: std::env::var("CODEX_BIN").unwrap_or_else(|_| "codex".into()),
                    };
                    t.execute(task).await?
                }
                ToolName::ClaudeCode => {
                    let t = ClaudeCodeTool {
                        binary: std::env::var("CLAUDE_CODE_BIN")
                            .unwrap_or_else(|_| "claude".into()),
                    };
                    t.execute(task).await?
                }
            };

            let finish_event = if result.success {
                "devtask.finished"
            } else {
                "devtask.failed"
            };
            emit_hooks(&hooks, finish_event, dry_run).await;

            println!("{}", serde_json::to_string_pretty(&result)?);
        }

        Commands::Research {
            program,
            run_script,
            run_arg,
            tool,
            dry_run_hooks,
            trackio,
            model_registry_path,
        } => {
            let selected_tool = tool.unwrap_or(ToolName::Codex);
            let (mut program_cfg, program_context) = ResearchProgram::load(&program)?;
            if trackio {
                let cfg = program_cfg.trackio.get_or_insert_with(Default::default);
                cfg.enabled = true;
            }
            if let Some(path) = model_registry_path {
                let cfg = program_cfg
                    .model_registry
                    .get_or_insert_with(Default::default);
                cfg.enabled = true;
                cfg.registry_path = Some(PathBuf::from(path));
            }
            let hooks = HookRegistry::load_file("config/hooks/hooks.json")?;
            let mut loop_runner = ExperimentLoop::new_with_hooks(
                program_cfg,
                program_context,
                Some(hooks),
                dry_run_hooks,
            )?;

            let skill_prelude = SkillRegistry::load_dir("skills").ok().and_then(|reg| {
                reg.get("autoresearch")
                    .and_then(|skill| skill.manifest.prompt_prelude.clone())
            });

            let hypothesis_fn = move |ctx: LoopContext| {
                let prelude = skill_prelude.clone();
                async move {
                    let system_prompt = ctx.to_system_prompt();
                    let patch_instructions = if let Some(prelude) = prelude {
                        format!("{}\n\n{}", prelude, system_prompt)
                    } else {
                        system_prompt
                    };

                    Ok(HypothesisResponse {
                        hypothesis: format!(
                            "Generation {}: improve {} for {}",
                            ctx.generation, ctx.metric_name, ctx.program_name
                        ),
                        patch_summary: "Agent-OS supervised patch application".into(),
                        patch_instructions,
                    })
                }
            };

            let codex_bin = std::env::var("CODEX_BIN").unwrap_or_else(|_| "codex".into());
            let claude_bin = std::env::var("CLAUDE_CODE_BIN").unwrap_or_else(|_| "claude".into());
            let apply_patch_fn = move |req: PatchRequest| {
                let tool = selected_tool.clone();
                let codex_bin = codex_bin.clone();
                let claude_bin = claude_bin.clone();
                async move {
                    let objective = build_patch_objective(&req);
                    let repo = req.repo_root.to_string_lossy().to_string();
                    let task = DevTask {
                        objective,
                        repo_path: repo.clone(),
                        cwd: repo,
                        allowed_paths: req.editable_files.clone(),
                        forbidden_paths: req.protected_files.clone(),
                        run_tests: false,
                        create_branch: false,
                        commit_if_success: false,
                        model_hint: None,
                    };

                    let result = match tool {
                        ToolName::Codex => {
                            let t = CodexTool { binary: codex_bin };
                            t.execute(task).await?
                        }
                        ToolName::ClaudeCode => {
                            let t = ClaudeCodeTool { binary: claude_bin };
                            t.execute(task).await?
                        }
                    };

                    if !result.success {
                        return Err(anyhow!("patch tool reported failure: {}", result.summary));
                    }

                    Ok(())
                }
            };

            let run_args_ref: Vec<&str> = run_arg.iter().map(String::as_str).collect();
            let summary = loop_runner
                .run(hypothesis_fn, apply_patch_fn, &run_script, &run_args_ref)
                .await?;

            if loop_runner.program.notebooklm_export_path.is_some() {
                if let Err(e) = NotebookLMExport::build_digest(&loop_runner.program) {
                    eprintln!("[notebooklm] digest export failed: {e}");
                }
                if let Err(e) = NotebookLMExport::build_zip(&loop_runner.program) {
                    eprintln!("[notebooklm] zip export failed: {e}");
                }
            }

            println!("{}", serde_json::to_string_pretty(&summary)?);
        }

        // ── MCP ───────────────────────────────────────────────────────────
        Commands::Mcp { action } => {
            println!("mcp placeholder: {action}");
        }

        // ── Skills ────────────────────────────────────────────────────────
        Commands::Skills { command } => {
            let reg = SkillRegistry::load_dir("skills")?;
            match command {
                SkillsCommand::List => {
                    for skill in reg.list() {
                        println!("{}\t{}", skill.manifest.name, skill.manifest.description);
                    }
                }
                SkillsCommand::Suggest { objective } => {
                    let matches = reg.suggest(&objective);
                    if matches.is_empty() {
                        println!("no matching skills for: {objective}");
                    } else {
                        for skill in matches {
                            println!("{}\t{}", skill.manifest.name, skill.manifest.description);
                        }
                    }
                }
            }
        }

        // ── Hooks ─────────────────────────────────────────────────────────
        Commands::Hooks { command } => {
            let reg = HookRegistry::load_file("config/hooks/hooks.json")?;
            match command {
                HooksCommand::Simulate { event } => {
                    for r in simulate_event(&reg, &event) {
                        println!("{}", serde_json::to_string_pretty(&r)?);
                    }
                }
                HooksCommand::Fire { event } => {
                    for r in fire_event_async(&reg, &event).await {
                        println!("{}", serde_json::to_string_pretty(&r)?);
                    }
                }
            }
        }

        // ── Plugins ───────────────────────────────────────────────────────
        Commands::Plugins { command } => {
            let reg = PluginRegistry::load_dir("plugins")?;
            match command {
                PluginsCommand::List => {
                    for plugin in reg.list() {
                        println!(
                            "{}\t{}\t{}",
                            plugin.manifest.name,
                            plugin.manifest.kind,
                            plugin.manifest.capabilities.join(",")
                        );
                    }
                }
                PluginsCommand::Invoke { name, ctx } => {
                    let context: HashMap<String, String> = ctx.into_iter().collect();
                    let result = reg.invoke(&name, &context)?;
                    println!("{}", serde_json::to_string_pretty(&result)?);
                }
            }
        }

        // ── Router ────────────────────────────────────────────────────────
        Commands::Router { command } => {
            let router = LocalRouter::from_env().unwrap_or_else(|e| {
                eprintln!("router: {e}");
                std::process::exit(1);
            });
            match command {
                RouterCommand::Show => {
                    println!(
                        "{:<6} {:<12} {:<45} {}",
                        "Tier", "Policy", "Base URL", "Model"
                    );
                    println!("{}", "-".repeat(90));
                    for ep in &router.endpoints {
                        println!(
                            "{:<6} {:<12} {:<45} {}",
                            ep.tier,
                            format!("{:?}", ep.policy),
                            ep.base_url,
                            ep.model
                        );
                    }
                }
                RouterCommand::Cascade { policy } => {
                    let chain = router.cascade(policy.into());
                    println!("Cascade order ({} endpoints):", chain.len());
                    for ep in chain {
                        println!("  Tier {} — {} — {}", ep.tier, ep.base_url, ep.model);
                    }
                }
            }
        }
    }

    Ok(())
}

// ── Helpers ────────────────────────────────────────────────────────────────

fn build_patch_objective(req: &PatchRequest) -> String {
    format!(
        "Autoresearch patch execution (generation {gen})\n\
Program: {program}\n\
Objective: {objective}\n\n\
Hypothesis:\n{hypothesis}\n\n\
Patch Summary:\n{patch_summary}\n\n\
Patch Instructions:\n{instructions}\n\n\
Constraints:\n\
- Only modify paths in editable_files\n\
- Never modify protected_files\n\
- Apply the change now; do not wait for confirmation\n",
        gen = req.generation,
        program = req.program_name,
        objective = req.objective,
        hypothesis = req.hypothesis,
        patch_summary = req.patch_summary,
        instructions = req.patch_instructions,
    )
}

async fn emit_hooks(registry: &HookRegistry, event: &str, dry_run: bool) {
    let results = if dry_run {
        simulate_event(registry, event)
    } else {
        fire_event_async(registry, event).await
    };
    for r in results {
        eprintln!("[hook] {} → {} ({}ms)", r.hook, r.status, r.duration_ms);
        if let Some(err) = &r.error {
            eprintln!("       {err}");
        }
    }
}
