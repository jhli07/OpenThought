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


class CustomProvider(BaseLLMProvider):
    """
    Custom OpenAI-compatible provider.
    
    Allows users to connect to ANY service that implements the OpenAI Chat Completions API.
    
    Supports:
    - Local models (Ollama, LM Studio, LocalAI, vLLM)
    - Self-hosted servers
    - Any OpenAI-compatible API service
    
    Example:
        >>> from openthought import OpenThought
        >>> provider = CustomProvider(
        ...     api_key="ollama",
        ...     base_url="http://localhost:11434/v1",
        ...     model="llama3"
        ... )
        >>> ot = OpenThought(prompt="...", provider=provider)
    """
    
    def __init__(
        self,
        api_key: str = "not-needed",
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3",
        **kwargs
    ):
        """
        Initialize custom provider.
        
        Args:
            api_key: API key (can be any string, some local servers don't need it)
            base_url: Base URL of the API server (must end with /v1)
                     Examples:
                     - http://localhost:11434/v1 (Ollama)
                     - http://localhost:8000/v1 (vLLM)
                     - http://localhost:1234/v1 (LM Studio)
            model: Model name to use
            **kwargs: Additional arguments (temperature, max_tokens, etc.)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/') + '/v1'  # Ensure /v1 suffix
        self.model = model
        self.extra_kwargs = kwargs
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate response using custom OpenAI-compatible API.
        
        Args:
            messages: List of message dicts
            **kwargs: Additional arguments (temperature, max_tokens, etc.)
        
        Returns:
            Generated text response
        """
        try:
            import openai
            
            # Merge extra kwargs with call kwargs
            call_kwargs = {**self.extra_kwargs, **kwargs}
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=call_kwargs.get("temperature", 0.7),
                max_tokens=call_kwargs.get("max_tokens", 1000),
            )
            
            return response.choices[0].message.content or ""
        
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        except Exception as e:
            raise ConnectionError(f"Custom API error: {e}\nCheck your base_url and model name.")
    
    def get_model_name(self) -> str:
        return self.model
    
    @property
    def provider_name(self) -> str:
        return "custom"
    
    def get_info(self) -> Dict[str, str]:
        """Get provider information."""
        return {
            "provider": "custom",
            "base_url": self.base_url,
            "model": self.model,
            "api_key": "***" if self.api_key and self.api_key != "not-needed" else "not-needed",
        }


# Provider registry
PROVIDERS = {
    "openai": OpenAIProvider,
    "kimi": KimiProvider,
    "moonshot": KimiProvider,
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,
    "azure": AzureProvider,
    "custom": CustomProvider,
    "ollama": CustomProvider,
    "lmstudio": CustomProvider,
    "localai": CustomProvider,
    "vllm": CustomProvider,
}


# Common custom providers presets
CUSTOM_PROVIDER_PRESETS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3",
    },
    "lmstudio": {
        "base_url": "http://localhost:1234/v1",
        "model": "llama-3-8b-instruct",
    },
    "localai": {
        "base_url": "http://localhost:8080/v1",
        "model": "llama-2-7b",
    },
    "vllm": {
        "base_url": "http://localhost:8000/v1",
        "model": "llama-2-7b",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
    },
    "yi": {
        "base_url": "https://api.lingyiwanwu.com/v1",
        "model": "yi-34b-chat",
    },
    "moonshot-v1": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "model": "abab6.5s-chat",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4",
    },
}


def create_provider(
    name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """
    Create an LLM provider instance.
    
    Args:
        name: Provider name (openai, kimi, claude, azure, custom, ollama, etc.)
        api_key: API key (optional for some custom providers)
        model: Optional model name override
        base_url: Optional base URL (required for custom providers)
        **kwargs: Additional provider arguments
    
    Returns:
        LLM provider instance
    
    Raises:
        ValueError: If provider is not supported or missing required arguments
    
    Examples:
        >>> # Standard providers
        >>> create_provider("openai", "sk-xxx", model="gpt-4")
        >>> create_provider("kimi", "your-kimi-key")
        >>> create_provider("claude", "your-claude-key")
        
        >>> # Custom OpenAI-compatible provider (local Ollama)
        >>> create_provider("ollama", model="llama3")
        >>> create_provider("custom", base_url="http://localhost:11434/v1", model="llama3")
        
        >>> # Chinese providers
        >>> create_provider("qwen", "your-key", model="qwen-plus")
        >>> create_provider("deepseek", "your-key", model="deepseek-chat")
        >>> create_provider("zhipu", "your-key", model="glm-4")
    """
    name = name.lower()
    
    # Check if it's a preset for Chinese/local providers
    if name in CUSTOM_PROVIDER_PRESETS:
        preset = CUSTOM_PROVIDER_PRESETS[name]
        return CustomProvider(
            api_key=api_key or "",
            base_url=preset["base_url"],
            model=model or preset["model"],
            **kwargs
        )
    
    if name not in PROVIDERS:
        # Check if it's a valid custom provider request
        if base_url:
            return CustomProvider(
                api_key=api_key or "not-needed",
                base_url=base_url,
                model=model or "custom-model",
                **kwargs
            )
        
        # Provide helpful error message with suggestions
        suggestions = []
        if name in ["ollama", "lmstudio", "localai", "vllm"]:
            suggestions.append(f"Did you mean '{name}' preset? Use create_provider('{name}')")
        elif name in ["deepseek", "qwen", "yi", "zhipu", "minimax"]:
            suggestions.append(f"Try: create_provider('{name}', 'your-api_key')")
        
        raise ValueError(
            f"Unsupported provider: '{name}'. "
            f"Supported providers: openai, kimi, claude, azure, custom\n"
            f"Chinese providers: qwen, deepseek, zhipu, yi, minimax\n"
            f"Local servers: ollama, lmstudio, localai, vllm\n"
            + ("\n".join(suggestions) if suggestions else "")
        )
    
    # Default models for each provider
    default_models = {
        "openai": "gpt-3.5-turbo",
        "kimi": "moonshot-v1-8k",
        "moonshot": "moonshot-v1-8k",
        "claude": "claude-sonnet-4-20250514",
        "anthropic": "claude-sonnet-4-20250514",
        "azure": None,  # Must be specified
        "custom": "custom-model",
        "ollama": "llama3",
        "lmstudio": "llama-3-8b-instruct",
        "localai": "llama-2-7b",
        "vllm": "llama-2-7b",
    }
    
    final_model = model or default_models.get(name, "gpt-3.5-turbo")
    
    # Special handling for Azure
    if name == "azure" and not final_model:
        raise ValueError("Azure provider requires a deployment name")
    
    # Build kwargs for providers
    provider_kwargs = kwargs.copy()
    if base_url:
        provider_kwargs["base_url"] = base_url
    
    return PROVIDERS[name](api_key=api_key or "", model=final_model, **provider_kwargs)


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
    if api_key.startswith("sk-") and "ant" not in api_key:
        return "openai"
    
    # Anthropic keys typically start with sk-ant-api03-
    if api_key.startswith("sk-ant-api"):
        return "claude"
    
    # Kimi/API keys don't have a standard prefix
    # Could add more heuristics here
    
    return None


def list_all_providers() -> Dict[str, Dict[str, Any]]:
    """
    List all available providers with their information.
    
    Returns:
        Dict of provider name -> provider info
    """
    info = {}
    
    # Standard providers
    for name in ["openai", "kimi", "claude", "azure"]:
        info[name] = {
            "type": "cloud",
            "requires_api_key": True,
            "default_model": {
                "openai": "gpt-3.5-turbo",
                "kimi": "moonshot-v1-8k",
                "claude": "claude-sonnet-4-20250514",
                "azure": "your-deployment-name",
            }.get(name),
            "description": {
                "openai": "OpenAI GPT models (GPT-3.5, GPT-4)",
                "kimi": "Moonshot AI Kimi",
                "claude": "Anthropic Claude",
                "azure": "Microsoft Azure OpenAI",
            }.get(name),
        }
    
    # Custom/Local providers
    for name, preset in CUSTOM_PROVIDER_PRESETS.items():
        info[name] = {
            "type": "custom",
            "requires_api_key": False,
            "default_model": preset["model"],
            "base_url": preset["base_url"],
            "description": {
                "ollama": "Ollama local models (llama3, mistral, etc.)",
                "lmstudio": "LM Studio local server",
                "localai": "LocalAI",
                "vllm": "vLLM inference server",
                "deepseek": "DeepSeek Chat",
                "qwen": "Alibaba Qwen (通义千问)",
                "yi": "01.AI Yi (零一万物)",
                "moonshot-v1": "Moonshot Kimi API",
                "minimax": "MiniMax (海螺AI)",
                "zhipu": "Zhipu AI (智谱清言)",
            }.get(name),
        }
    
    return info


def test_provider_connection(
    name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    test_message: str = "Hello"
) -> Dict[str, Any]:
    """
    Test provider connection with a simple request.
    
    Args:
        name: Provider name
        api_key: API key
        base_url: Base URL for custom providers
        model: Model name
        test_message: Test message to send
    
    Returns:
        Dict with success status and message/details
    """
    try:
        provider = create_provider(
            name=name,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        
        messages = [
            {"role": "user", "content": test_message}
        ]
        
        response = provider.generate(messages, max_tokens=50)
        
        return {
            "success": True,
            "provider": provider.provider_name,
            "model": provider.get_model_name(),
            "response_preview": response[:100] if response else "Empty response",
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Check your API key, base URL, and model name",
        }


if __name__ == "__main__":
    print("=" * 60)
    print("OpenThought Providers")
    print("=" * 60)
    
    print("\n📦 Standard Cloud Providers:")
    for name in ["openai", "kimi", "claude", "azure"]:
        info = list_all_providers().get(name, {})
        print(f"  • {name}: {info.get('description', 'N/A')}")
    
    print("\n🏠 Local/Custom Providers:")
    for name in ["ollama", "lmstudio", "localai", "vllm"]:
        info = list_all_providers().get(name, {})
        print(f"  • {name}: {info.get('description', 'N/A')}")
    
    print("\n🇨🇳 Chinese Providers:")
    for name in ["qwen", "deepseek", "zhipu", "yi", "minimax"]:
        info = list_all_providers().get(name, {})
        print(f"  • {name}: {info.get('description', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Example usage:")
    print("=" * 60)
    print("""
    # OpenAI
    create_provider("openai", "sk-your-key", model="gpt-4")
    
    # Ollama (local)
    create_provider("ollama", model="llama3")
    
    # Custom server
    create_provider("custom", base_url="http://localhost:11434/v1", model="llama3")
    
    # Qwen
    create_provider("qwen", "your-api-key")
    """)
