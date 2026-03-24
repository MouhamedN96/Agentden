use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    fs,
    path::{Path, PathBuf},
    process::Command,
    time::Instant,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginManifest {
    pub name: String,
    pub version: String,
    pub entrypoint: String,
    pub kind: String,
    #[serde(default)]
    pub capabilities: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct PluginRef {
    pub manifest: PluginManifest,
    pub root: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginInvokeResult {
    pub plugin: String,
    pub status: String,
    pub exit_code: Option<i32>,
    pub duration_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

#[derive(Debug, Default)]
pub struct PluginRegistry {
    plugins: Vec<PluginRef>,
}

impl PluginRegistry {
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
            let manifest_path = path.join("plugin.json");
            if !manifest_path.exists() {
                continue;
            }
            let data = fs::read_to_string(&manifest_path)?;
            let manifest: PluginManifest = serde_json::from_str(&data)?;
            reg.plugins.push(PluginRef {
                manifest,
                root: path,
            });
        }
        Ok(reg)
    }

    pub fn list(&self) -> &[PluginRef] {
        &self.plugins
    }

    pub fn get(&self, name: &str) -> Option<&PluginRef> {
        self.plugins.iter().find(|p| p.manifest.name == name)
    }

    /// Invoke a plugin by name, passing context as environment variables.
    /// Context keys become PLUGIN_CTX_<KEY> env vars in the subprocess.
    pub fn invoke(
        &self,
        name: &str,
        context: &HashMap<String, String>,
    ) -> Result<PluginInvokeResult> {
        let plugin = self
            .get(name)
            .ok_or_else(|| anyhow!("plugin not found: {name}"))?;

        let entrypoint = plugin.root.join(&plugin.manifest.entrypoint);
        if !entrypoint.exists() {
            return Err(anyhow!(
                "plugin entrypoint not found: {}",
                entrypoint.display()
            ));
        }

        let t = Instant::now();

        let result = Command::new(&entrypoint)
            .current_dir(&plugin.root)
            .env("PLUGIN_NAME", &plugin.manifest.name)
            .env("PLUGIN_VERSION", &plugin.manifest.version)
            .env(
                "PLUGIN_CAPABILITIES",
                plugin.manifest.capabilities.join(","),
            )
            .envs(
                context
                    .iter()
                    .map(|(k, v)| (format!("PLUGIN_CTX_{}", k.to_uppercase()), v)),
            )
            .spawn()
            .and_then(|mut child| child.wait());

        let duration_ms = t.elapsed().as_millis() as u64;

        Ok(match result {
            Ok(status) => {
                let code = status.code();
                let ok = status.success();
                PluginInvokeResult {
                    plugin: name.to_string(),
                    status: if ok { "ok".into() } else { "failed".into() },
                    exit_code: code,
                    duration_ms,
                    error: if ok {
                        None
                    } else {
                        Some(format!("exited {:?}", code))
                    },
                }
            }
            Err(e) => PluginInvokeResult {
                plugin: name.to_string(),
                status: "error".into(),
                exit_code: None,
                duration_ms,
                error: Some(e.to_string()),
            },
        })
    }
}
