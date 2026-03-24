use anyhow::Result;
use async_trait::async_trait;

#[async_trait]
pub trait LlmBackend: Send + Sync {
    async fn health(&self) -> Result<()>;
    fn name(&self) -> &'static str;
}

pub struct NoopBackend;

#[async_trait]
impl LlmBackend for NoopBackend {
    async fn health(&self) -> Result<()> {
        Ok(())
    }
    fn name(&self) -> &'static str {
        "noop"
    }
}
