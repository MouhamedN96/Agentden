use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::env;

/// Maps to a 5-tier LLM cascade:
/// Tier1=OfflineFirst, Tier2=Cheap, Tier3/4=Balanced/Premium
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum RoutePolicy {
    /// Tier 1 — on-device / local llama.cpp, no network needed
    OfflineFirst,
    /// Tier 2 — SiliconFlow Liquid models, cheap cloud
    Cheap,
    /// Tier 3 — SiliconFlow Qwen 72B, larger context
    Balanced,
    /// Tier 4 — Anthropic Claude, technical/moderation tasks
    Premium,
    /// Tier 5 — HuggingFace fallback, cost backstop
    Fallback,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouterEndpoint {
    pub tier: u8,
    pub policy: RoutePolicy,
    pub base_url: String,
    pub model: String,
    pub api_key: String,
}

pub struct LocalRouter {
    pub endpoints: Vec<RouterEndpoint>,
}

impl LocalRouter {
    /// Build router from environment variables.
    /// Required: ANTHROPIC_API_KEY or OPENAI_API_KEY
    /// Optional: SILICONFLOW_API_KEY, HF_API_KEY, LOCAL_LLM_URL
    pub fn from_env() -> Result<Self> {
        let mut endpoints: Vec<RouterEndpoint> = Vec::new();

        // Tier 1 — local llama.cpp (OpenAI-compat server at LOCAL_LLM_URL)
        if let Ok(url) = env::var("LOCAL_LLM_URL") {
            endpoints.push(RouterEndpoint {
                tier: 1,
                policy: RoutePolicy::OfflineFirst,
                base_url: url,
                model: env::var("LOCAL_LLM_MODEL").unwrap_or_else(|_| "smollm2-360m-q4".into()),
                api_key: "local".into(),
            });
        }

        // Tier 2 — SiliconFlow Liquid LFM2 (cheap)
        if let Ok(key) = env::var("SILICONFLOW_API_KEY") {
            endpoints.push(RouterEndpoint {
                tier: 2,
                policy: RoutePolicy::Cheap,
                base_url: "https://api.siliconflow.cn/v1".into(),
                model: env::var("SILICONFLOW_CHEAP_MODEL")
                    .unwrap_or_else(|_| "liquid/lfm2-1.2b".into()),
                api_key: key.clone(),
            });
            // Tier 3 — SiliconFlow Qwen (balanced)
            endpoints.push(RouterEndpoint {
                tier: 3,
                policy: RoutePolicy::Balanced,
                base_url: "https://api.siliconflow.cn/v1".into(),
                model: env::var("SILICONFLOW_BALANCED_MODEL")
                    .unwrap_or_else(|_| "qwen/qwen2.5-72b-instruct".into()),
                api_key: key,
            });
        }

        // Tier 4 — Anthropic Claude (premium)
        if let Ok(key) = env::var("ANTHROPIC_API_KEY") {
            endpoints.push(RouterEndpoint {
                tier: 4,
                policy: RoutePolicy::Premium,
                base_url: "https://api.anthropic.com/v1".into(),
                model: env::var("ANTHROPIC_MODEL").unwrap_or_else(|_| "claude-sonnet-4-6".into()),
                api_key: key,
            });
        }

        // Tier 5 — HuggingFace fallback
        if let Ok(key) = env::var("HF_API_KEY") {
            endpoints.push(RouterEndpoint {
                tier: 5,
                policy: RoutePolicy::Fallback,
                base_url: "https://api-inference.huggingface.co/v1".into(),
                model: env::var("HF_MODEL")
                    .unwrap_or_else(|_| "mistralai/Mistral-7B-Instruct-v0.2".into()),
                api_key: key,
            });
        }

        // Also honour legacy OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL
        // so existing env.example keeps working
        if endpoints.is_empty() {
            let url =
                env::var("OPENAI_BASE_URL").unwrap_or_else(|_| "http://127.0.0.1:8402/v1".into());
            let key = env::var("OPENAI_API_KEY").unwrap_or_else(|_| "replace-me".into());
            let model = env::var("OPENAI_MODEL").unwrap_or_else(|_| "blockrun/auto".into());
            endpoints.push(RouterEndpoint {
                tier: 2,
                policy: RoutePolicy::Cheap,
                base_url: url,
                model,
                api_key: key,
            });
        }

        if endpoints.is_empty() {
            return Err(anyhow!(
                "No LLM endpoints configured. Set SILICONFLOW_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY."
            ));
        }

        endpoints.sort_by_key(|e| e.tier);
        Ok(Self { endpoints })
    }

    /// Return the best endpoint for a policy, cascading up tiers if needed.
    pub fn choose(&self, policy: RoutePolicy) -> Result<&RouterEndpoint> {
        // Exact match first
        if let Some(e) = self.endpoints.iter().find(|e| e.policy == policy) {
            return Ok(e);
        }
        // Cascade: return lowest available tier
        self.endpoints
            .first()
            .ok_or_else(|| anyhow!("no endpoints configured"))
    }

    /// Cascade: try preferred policy, then walk up tiers.
    pub fn cascade(&self, preferred: RoutePolicy) -> Vec<&RouterEndpoint> {
        let preferred_tier = self
            .endpoints
            .iter()
            .find(|e| e.policy == preferred)
            .map(|e| e.tier)
            .unwrap_or(0);

        let mut result: Vec<&RouterEndpoint> = self
            .endpoints
            .iter()
            .filter(|e| e.tier >= preferred_tier)
            .collect();

        result.sort_by_key(|e| e.tier);
        result
    }
}
