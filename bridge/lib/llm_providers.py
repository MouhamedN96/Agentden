"""
Multi-LLM Provider Support
Supports Groq, OpenRouter, Ollama Cloud, and more
"""

import os
import httpx
from typing import List, Dict, Any, Optional
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMProviderConfig:
    """Configuration for each LLM provider"""
    
    CONFIGS = {
        LLMProvider.GROQ: {
            "base_url": "https://api.groq.com/openai/v1",
            "default_model": "llama-3.1-70b-versatile",
            "models": {
                "fast": "llama-3.1-8b-instant",           # Ultra fast, cheap
                "balanced": "llama-3.1-70b-versatile",    # Good balance
                "quality": "llama-3.3-70b-versatile",     # Best quality
            },
            "cost_per_1m_tokens": {
                "input": 0.05,   # $0.05 per 1M input tokens
                "output": 0.08   # $0.08 per 1M output tokens
            },
            "speed": "ultra-fast",  # 500+ tokens/sec
            "requires_api_key": True,
            "env_var": "GROQ_API_KEY"
        },
        
        LLMProvider.OPENROUTER: {
            "base_url": "https://openrouter.ai/api/v1",
            "default_model": "anthropic/claude-3.5-sonnet",
            "models": {
                "fast": "google/gemini-2.0-flash-exp:free",  # Free!
                "balanced": "anthropic/claude-3.5-sonnet",
                "quality": "anthropic/claude-3.7-sonnet",
                "cheap": "meta-llama/llama-3.1-8b-instruct:free",  # Free!
            },
            "cost_per_1m_tokens": {
                "input": 3.0,    # Varies by model
                "output": 15.0   # Claude pricing
            },
            "speed": "fast",
            "requires_api_key": True,
            "env_var": "OPENROUTER_API_KEY"
        },
        
        LLMProvider.OLLAMA: {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            "default_model": "llama3.1:70b",
            "models": {
                "fast": "llama3.1:8b",
                "balanced": "llama3.1:70b",
                "quality": "qwen2.5:72b",
                "code": "deepseek-coder-v2:16b",
            },
            "cost_per_1m_tokens": {
                "input": 0.0,    # Self-hosted = FREE!
                "output": 0.0
            },
            "speed": "depends-on-hardware",
            "requires_api_key": False,
            "env_var": None
        },
        
        LLMProvider.ANTHROPIC: {
            "base_url": "https://api.anthropic.com/v1",
            "default_model": "claude-3-5-sonnet-20241022",
            "models": {
                "fast": "claude-3-5-haiku-20241022",
                "balanced": "claude-3-5-sonnet-20241022",
                "quality": "claude-3-7-sonnet-20250219",
            },
            "cost_per_1m_tokens": {
                "input": 3.0,
                "output": 15.0
            },
            "speed": "fast",
            "requires_api_key": True,
            "env_var": "ANTHROPIC_API_KEY"
        },
        
        LLMProvider.OPENAI: {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-4o",
            "models": {
                "fast": "gpt-4o-mini",
                "balanced": "gpt-4o",
                "quality": "o1",
            },
            "cost_per_1m_tokens": {
                "input": 2.5,
                "output": 10.0
            },
            "speed": "fast",
            "requires_api_key": True,
            "env_var": "OPENAI_API_KEY"
        }
    }
    
    @classmethod
    def get_config(cls, provider: LLMProvider) -> Dict[str, Any]:
        """Get configuration for a provider"""
        return cls.CONFIGS[provider]
    
    @classmethod
    def get_api_key(cls, provider: LLMProvider) -> Optional[str]:
        """Get API key from environment"""
        config = cls.get_config(provider)
        env_var = config.get("env_var")
        if env_var:
            return os.getenv(env_var)
        return None


class LLMClient:
    """Universal LLM client supporting multiple providers"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.GROQ, model: Optional[str] = None):
        self.provider = provider
        self.config = LLMProviderConfig.get_config(provider)
        self.model = model or self.config["default_model"]
        self.api_key = LLMProviderConfig.get_api_key(provider)
        
        if self.config["requires_api_key"] and not self.api_key:
            raise ValueError(f"API key required for {provider.value}. Set {self.config['env_var']}")
    
    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Send chat request to LLM provider"""
        
        headers = {"Content-Type": "application/json"}
        
        # Add authorization based on provider
        if self.provider == LLMProvider.ANTHROPIC:
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
            return await self._chat_anthropic(messages, temperature, headers)
        else:
            # OpenAI-compatible API (Groq, OpenRouter, Ollama, OpenAI)
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            return await self._chat_openai_compatible(messages, temperature, headers)
    
    async def _chat_openai_compatible(self, messages: List[Dict[str, str]], temperature: float, headers: Dict[str, str]) -> str:
        """Chat with OpenAI-compatible API"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.config['base_url']}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _chat_anthropic(self, messages: List[Dict[str, str]], temperature: float, headers: Dict[str, str]) -> str:
        """Chat with Anthropic API"""
        # Convert messages format
        system_message = None
        converted_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                converted_messages.append(msg)
        
        payload = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": 4096,
            "temperature": temperature
        }
        
        if system_message:
            payload["system"] = system_message
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.config['base_url']}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request"""
        cost_config = self.config["cost_per_1m_tokens"]
        input_cost = (input_tokens / 1_000_000) * cost_config["input"]
        output_cost = (output_tokens / 1_000_000) * cost_config["output"]
        return input_cost + output_cost


class LLMRouter:
    """Smart router that selects the best LLM for each task"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
    
    def _initialize_providers(self) -> Dict[str, LLMClient]:
        """Initialize available providers"""
        providers = {}
        
        # Try to initialize each provider
        for provider in LLMProvider:
            try:
                config = LLMProviderConfig.get_config(provider)
                if config["requires_api_key"]:
                    api_key = LLMProviderConfig.get_api_key(provider)
                    if not api_key:
                        continue
                
                providers[provider.value] = LLMClient(provider)
                print(f"✓ Initialized {provider.value}")
            except Exception as e:
                print(f"✗ Could not initialize {provider.value}: {e}")
        
        return providers
    
    def get_client(self, task_type: str = "balanced") -> LLMClient:
        """Get the best LLM client for a task type"""
        
        # Task-specific routing
        routing_rules = {
            "fast": ["groq", "ollama", "openrouter"],      # Speed priority
            "cheap": ["ollama", "groq", "openrouter"],     # Cost priority
            "quality": ["anthropic", "openai", "openrouter"],  # Quality priority
            "balanced": ["groq", "openrouter", "anthropic"]    # Balance
        }
        
        preferred_providers = routing_rules.get(task_type, routing_rules["balanced"])
        
        # Return first available provider
        for provider_name in preferred_providers:
            if provider_name in self.providers:
                return self.providers[provider_name]
        
        # Fallback to any available provider
        if self.providers:
            return list(self.providers.values())[0]
        
        raise RuntimeError("No LLM providers available")
    
    def get_cheapest_client(self) -> LLMClient:
        """Get the cheapest available client"""
        return self.get_client("cheap")
    
    def get_fastest_client(self) -> LLMClient:
        """Get the fastest available client"""
        return self.get_client("fast")
    
    def get_best_quality_client(self) -> LLMClient:
        """Get the highest quality client"""
        return self.get_client("quality")


# Cost comparison helper
def print_cost_comparison():
    """Print cost comparison across providers"""
    
    print("\n" + "="*80)
    print("LLM Provider Cost Comparison (per 1M tokens)")
    print("="*80)
    
    print(f"\n{'Provider':<15} {'Input':<12} {'Output':<12} {'Speed':<15} {'Notes'}")
    print("-"*80)
    
    for provider in LLMProvider:
        config = LLMProviderConfig.get_config(provider)
        costs = config["cost_per_1m_tokens"]
        
        input_cost = f"${costs['input']:.2f}" if costs['input'] > 0 else "FREE"
        output_cost = f"${costs['output']:.2f}" if costs['output'] > 0 else "FREE"
        speed = config["speed"]
        
        notes = ""
        if provider == LLMProvider.GROQ:
            notes = "⚡ Ultra-fast, cheap"
        elif provider == LLMProvider.OLLAMA:
            notes = "🏠 Self-hosted, FREE"
        elif provider == LLMProvider.OPENROUTER:
            notes = "🌐 Access all models"
        
        print(f"{provider.value:<15} {input_cost:<12} {output_cost:<12} {speed:<15} {notes}")
    
    print("\n" + "="*80)
    print("Estimated Cost per Review (avg 2000 input + 1000 output tokens)")
    print("="*80)
    
    for provider in LLMProvider:
        config = LLMProviderConfig.get_config(provider)
        costs = config["cost_per_1m_tokens"]
        
        review_cost = (2000 * costs['input'] + 1000 * costs['output']) / 1_000_000
        
        if review_cost == 0:
            cost_str = "FREE"
        else:
            cost_str = f"${review_cost:.4f}"
        
        print(f"{provider.value:<15} {cost_str}")
    
    print("\n" + "="*80)
    print("Monthly Cost Estimate (100 reviews)")
    print("="*80)
    
    for provider in LLMProvider:
        config = LLMProviderConfig.get_config(provider)
        costs = config["cost_per_1m_tokens"]
        
        monthly_cost = 100 * (2000 * costs['input'] + 1000 * costs['output']) / 1_000_000
        
        if monthly_cost == 0:
            cost_str = "FREE"
        else:
            cost_str = f"${monthly_cost:.2f}"
        
        print(f"{provider.value:<15} {cost_str}")
    
    print("\n" + "="*80)
    print("\nRecommendations:")
    print("  • Development: Use Ollama (free, local)")
    print("  • Production: Use Groq (fast, cheap)")
    print("  • High Quality: Use OpenRouter with Claude")
    print("  • Cost-Conscious: Use Groq or Ollama")
    print("  • Multi-Model: Use OpenRouter (access to all models)")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Print cost comparison
    print_cost_comparison()
    
    # Test router
    print("\nTesting LLM Router...")
    router = LLMRouter()
    
    print(f"\nFastest client: {router.get_fastest_client().provider.value}")
    print(f"Cheapest client: {router.get_cheapest_client().provider.value}")
    print(f"Best quality client: {router.get_best_quality_client().provider.value}")
