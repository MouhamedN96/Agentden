use anyhow::{anyhow, Result};
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{
    collections::HashMap,
    fs,
    path::{Path, PathBuf},
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillManifest {
    pub name: String,
    pub version: String,
    pub description: String,
    #[serde(default)]
    pub triggers: Vec<String>,
    #[serde(default)]
    pub tools: Vec<String>,
    #[serde(default)]
    pub prompt_prelude: Option<String>,
}

#[derive(Debug, Clone)]
pub struct Skill {
    pub manifest: SkillManifest,
    pub root: PathBuf,
}

#[async_trait]
pub trait SkillExecutor: Send + Sync {
    async fn execute(&self, skill: &Skill, input: Value) -> Result<Value>;
}

#[derive(Debug, Default)]
pub struct SkillRegistry {
    by_name: HashMap<String, Skill>,
}

impl SkillRegistry {
    pub fn load_dir(dir: impl AsRef<Path>) -> Result<Self> {
        let mut reg = Self::default();
        let dir = dir.as_ref();
        if !dir.exists() {
            return Ok(reg);
        }
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            if !path.is_dir() {
                continue;
            }
            let manifest_path = path.join("skill.json");
            if !manifest_path.exists() {
                continue;
            }
            let data = fs::read_to_string(&manifest_path)?;
            let manifest: SkillManifest = serde_json::from_str(&data)?;
            reg.by_name.insert(
                manifest.name.clone(),
                Skill {
                    manifest,
                    root: path,
                },
            );
        }
        Ok(reg)
    }

    pub fn get(&self, name: &str) -> Option<&Skill> {
        self.by_name.get(name)
    }

    pub fn list(&self) -> Vec<&Skill> {
        let mut items: Vec<&Skill> = self.by_name.values().collect();
        items.sort_by(|a, b| a.manifest.name.cmp(&b.manifest.name));
        items
    }

    pub fn suggest(&self, objective: &str) -> Vec<&Skill> {
        let objective = objective.to_lowercase();
        self.list()
            .into_iter()
            .filter(|skill| {
                skill
                    .manifest
                    .triggers
                    .iter()
                    .any(|t| objective.contains(&t.to_lowercase()))
            })
            .collect()
    }
}

pub struct PromptSkillExecutor;

#[async_trait]
impl SkillExecutor for PromptSkillExecutor {
    async fn execute(&self, skill: &Skill, input: Value) -> Result<Value> {
        let objective = input
            .get("objective")
            .and_then(|v| v.as_str())
            .unwrap_or_default();
        Ok(serde_json::json!({
            "skill": skill.manifest.name,
            "description": skill.manifest.description,
            "prompt_prelude": skill.manifest.prompt_prelude,
            "objective": objective,
            "tools": skill.manifest.tools,
            "root": skill.root,
        }))
    }
}

pub fn require_skill<'a>(registry: &'a SkillRegistry, name: &str) -> Result<&'a Skill> {
    registry
        .get(name)
        .ok_or_else(|| anyhow!("skill not found: {name}"))
}
