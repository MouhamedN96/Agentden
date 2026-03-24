use anyhow::{bail, Result};
use async_trait::async_trait;
use serde_json::Value;

#[async_trait]
pub trait Tool: Send + Sync {
    fn name(&self) -> &'static str;
    async fn run(&self, input: Value) -> Result<Value>;
}

pub struct ShellTool;

#[async_trait]
impl Tool for ShellTool {
    fn name(&self) -> &'static str {
        "shell"
    }
    async fn run(&self, _input: Value) -> Result<Value> {
        bail!("not implemented")
    }
}
