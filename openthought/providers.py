"""
OpenThought LLM Providers - Multi-provider LLM integration.

Supports OpenAI, Kimi (Moonshot), Anthropic Claude, and custom providers.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-3.5-turbo)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using OpenAI API."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
            )
            
            return response.choices[0].message.content or ""
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        except Exception as e:
            raise ConnectionError(f"OpenAI API error: {e}")
    
    def get_model_name(self) -> str:
        return self.model
    
    @property
    def provider_name(self) -> str:
        return "openai"


class KimiProvider(BaseLLMProvider):
    """Kimi (Moonshot AI) provider."""
    
    def __init__(self, api_key: str, model: str = "moonshot-v1-8k", **kwargs):
        """
        Initialize Kimi provider.
        
        Args:
            api_key: Kimi API key
            model: Model name (default: moonshot-v1-8k)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get("base_url", "https://api.moonshot.cn/v1")
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using Kimi API."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
            )
            
            return response.choices[0].message.content or ""
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        except Exception as e:
            raise ConnectionError(f"Kimi API error: {e}")
    
    def get_model_name(self) -> str:
        return self.model
    
    @property
    def provider_name(self) -> str:
        return "kimi"


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", **kwargs):
        """
        Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-sonnet-4-20250514)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get("base_url", "https://api.anthropic.com")
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using Claude API."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Convert messages format for Claude
            system_message = None
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                    break
            
            user_messages = [m for m in messages if m["role"] != "system"]
            
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                system=system_message,
                messages=user_messages,
            )
            
            return response.content[0].text
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
        except Exception as e:
            raise ConnectionError(f"Claude API error: {e}")
    
    def get_model_name(self) -> str:
        return self.model
    
    @property
    def provider_name(self) -> str:
        return "claude"


class AzureProvider(BaseLLMProvider):
    """Azure OpenAI provider."""
    
    def __init__(
        self,
        api_key: str,
        deployment: str,
        api_version: str = "2024-02-01",
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            api_key: Azure API key
            deployment: Deployment name
            api_version: API version
            base_url: Azure endpoint URL
        """
        self.api_key = api_key
        self.deployment = deployment
        self.api_version = api_version
        self.base_url = base_url
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using Azure OpenAI API."""
        try:
            import openai
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.base_url,
            )
            
            response = client.chat.completions.create(
                deployment_id=self.deployment,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
            )
            
            return response.choices[0].message.content or ""
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        except Exception as e:
            raise ConnectionError(f"Azure API error: {e}")
    
    def get_model_name(self) -> str:
        return self.deployment
    
    @property
    def provider_name(self) -> str:
        return "azure"


# Provider registry
PROVIDERS = {
    "openai": OpenAIProvider,
    "kimi": KimiProvider,
    "moonshot": KimiProvider,
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,
    "azure": AzureProvider,
}


def create_provider(
    name: str,
    api_key: str,
    model: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """
    Create an LLM provider instance.
    
    Args:
        name: Provider name (openai, kimi, claude, azure)
        api_key: API key
        model: Optional model name override
        **kwargs: Additional provider arguments
    
    Returns:
        LLM provider instance
    
    Raises:
        ValueError: If provider is not supported
    
    Example:
        >>> from openthought.providers import create_provider
        >>> provider = create_provider("openai", "sk-xxx", model="gpt-4")
    """
    name = name.lower()
    
    if name not in PROVIDERS:
        raise ValueError(
            f"Unsupported provider: {name}. "
            f"Supported providers: {list(PROVIDERS.keys())}"
        )
    
    # Default models for each provider
    default_models = {
        "openai": "gpt-3.5-turbo",
        "kimi": "moonshot-v1-8k",
        "moonshot": "moonshot-v1-8k",
        "claude": "claude-sonnet-4-20250514",
        "anthropic": "claude-sonnet-4-20250514",
        "azure": None,  # Must be specified
    }
    
    final_model = model or default_models.get(name)
    
    if name == "azure" and not final_model:
        raise ValueError("Azure provider requires a deployment name")
    
    return PROVIDERS[name](api_key=api_key, model=final_model, **kwargs)


def get_available_providers() -> List[str]:
    """Get list of available provider names."""
    return list(PROVIDERS.keys())


def auto_detect_provider(api_key: str) -> Optional[str]:
    """
    Attempt to auto-detect provider from API key format.
    
    Args:
        api_key: The API key to analyze
    
    Returns:
        Detected provider name or None
    """
    if not api_key:
        return None
    
    # OpenAI keys typically start with sk-
    if api_key.startswith("sk-"):
        return "openai"
    
    # Anthropic keys typically start with sk-ant-api03-
    if api_key.startswith("sk-ant-api"):
        return "claude"
    
    # Kimi/API keys don't have a standard prefix
    # Could add more heuristics here
    
    return None


if __name__ == "__main__":
    print("Available providers:", get_available_providers())
    
    # Test provider creation
    try:
        provider = create_provider("openai", "test-key")
        print(f"Created provider: {provider.provider_name}")
    except Exception as e:
        print(f"Expected error: {e}")
