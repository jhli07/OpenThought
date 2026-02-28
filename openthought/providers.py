"""
OpenThought LLM Providers v3.0 - Multi-provider LLM integration.

Refactored for:
- Streaming support
- Async/await
- Unified provider abstraction
- Better error handling
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, Type
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 60
    max_retries: int = 3


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers with sync/async/streaming support."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client = None
    
    @abstractmethod
    def _init_client(self):
        """Initialize the underlying client."""
        pass
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM (sync)."""
        pass
    
    @abstractmethod
    async def agenerate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM (async)."""
        pass
    
    @abstractmethod
    async def astream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate responses (async)."""
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


class OpenAICompatProvider(BaseLLMProvider):
    """
    Base provider for OpenAI-compatible APIs.
    
    Handles common logic for OpenAI, Kimi, DeepSeek, Qwen, etc.
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client."""
        try:
            import openai
            self._client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url or "https://api.openai.com/v1",
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using OpenAI-compatible API."""
        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=False,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            self._handle_error(e)
    
    async def agenerate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.generate(messages, **kwargs)
        )
    
    async def astream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate responses."""
        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            self._handle_error(e)
    
    def _handle_error(self, error: Exception) -> None:
        """Handle and transform errors."""
        error_str = str(error).lower()
        
        if "rate_limit" in error_str or "429" in error_str:
            raise ProviderError(f"Rate limit exceeded: {error}")
        elif "timeout" in error_str or "timed_out" in error_str:
            raise TimeoutError(f"Request timed out: {error}")
        elif "invalid_api_key" in error_str or "401" in error_str:
            raise ProviderError(f"Invalid API key: {error}")
        elif "model_not_found" in error_str or "404" in error_str:
            raise ProviderError(f"Model not found: {error}")
        else:
            raise ProviderError(f"API error: {error}")
    
    def get_model_name(self) -> str:
        return self.config.model
    
    @property
    def provider_name(self) -> str:
        return self.config.name


class OpenAIProvider(OpenAICompatProvider):
    """OpenAI GPT provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        **kwargs
    ):
        config = ProviderConfig(
            name="openai",
            api_key=api_key,
            model=model,
            base_url=kwargs.get("base_url", "https://api.openai.com/v1"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
            timeout=kwargs.get("timeout", 60),
        )
        super().__init__(config)


class KimiProvider(OpenAICompatProvider):
    """Kimi (Moonshot AI) provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "moonshot-v1-8k",
        **kwargs
    ):
        config = ProviderConfig(
            name="kimi",
            api_key=api_key,
            model=model,
            base_url=kwargs.get("base_url", "https://api.moonshot.cn/v1"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
        )
        super().__init__(config)


class DeepSeekProvider(OpenAICompatProvider):
    """DeepSeek provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        **kwargs
    ):
        config = ProviderConfig(
            name="deepseek",
            api_key=api_key,
            model=model,
            base_url=kwargs.get("base_url", "https://api.deepseek.com/v1"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
        )
        super().__init__(config)


class QwenProvider(OpenAICompatProvider):
    """Qwen (Alibaba) provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-turbo",
        **kwargs
    ):
        config = ProviderConfig(
            name="qwen",
            api_key=api_key,
            model=model,
            base_url=kwargs.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
        )
        super().__init__(config)


class ZhipuProvider(OpenAICompatProvider):
    """Zhipu AI (智谱清言) provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "glm-4",
        **kwargs
    ):
        config = ProviderConfig(
            name="zhipu",
            api_key=api_key,
            model=model,
            base_url=kwargs.get("base_url", "https://open.bigmodel.cn/api/paas/v4"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
        )
        super().__init__(config)


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,  # None = auto-select latest
        **kwargs
    ):
        # Auto-select latest Claude model if not specified
        default_model = "claude-sonnet-4-20250514"
        
        config = ProviderConfig(
            name="claude",
            api_key=api_key,
            model=model or default_model,
            base_url=kwargs.get("base_url", "https://api.anthropic.com"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
            timeout=kwargs.get("timeout", 60),
        )
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """Initialize Anthropic client."""
        try:
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using Claude API."""
        try:
            # Extract system message
            system_message = None
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                    break
            
            user_messages = [m for m in messages if m["role"] != "system"]
            
            response = self._client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_message,
                messages=user_messages,
            )
            
            return response.content[0].text
        except Exception as e:
            self._handle_error(e)
    
    async def agenerate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(messages, **kwargs)
        )
    
    async def astream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate responses."""
        try:
            system_message = None
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                    break
            
            user_messages = [m for m in messages if m["role"] != "system"]
            
            with self._client.messages.stream(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_message,
                messages=user_messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            self._handle_error(e)
    
    def _handle_error(self, error: Exception) -> None:
        """Handle Claude-specific errors."""
        error_str = str(error).lower()
        
        if "rate_limit" in error_str or "429" in error_str:
            raise ProviderError(f"Claude rate limit exceeded: {error}")
        elif "authentication" in error_str or "401" in error_str:
            raise ProviderError(f"Invalid Claude API key: {error}")
        elif "not_found" in error_str or "404" in error_str:
            raise ProviderError(f"Claude model not found: {error}")
        elif "overloaded" in error_str or "529" in error_str:
            raise ProviderError(f"Claude service overloaded: {error}")
        else:
            raise ProviderError(f"Claude API error: {error}")
    
    def get_model_name(self) -> str:
        return self.config.model
    
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
        config = ProviderConfig(
            name="azure",
            api_key=api_key,
            model=deployment,  # Azure uses deployment name as model
            base_url=base_url,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
        )
        super().__init__(config)
        self._api_version = api_version
        self._deployment = deployment
        self._init_client()
    
    def _init_client(self):
        """Initialize Azure OpenAI client."""
        try:
            import openai
            self._client = openai.AzureOpenAI(
                api_key=self.config.api_key,
                api_version=self._api_version,
                azure_endpoint=self.config.base_url,
            )
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response using Azure OpenAI API."""
        try:
            response = self._client.chat.completions.create(
                deployment_id=self._deployment,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ProviderError(f"Azure API error: {e}")
    
    async def agenerate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(messages, **kwargs)
        )
    
    async def astream_generate(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate responses."""
        try:
            response = self._client.chat.completions.create(
                deployment_id=self._deployment,
                messages=messages,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise ProviderError(f"Azure API error: {e}")
    
    def get_model_name(self) -> str:
        return self._deployment
    
    @property
    def provider_name(self) -> str:
        return "azure"


class CustomProvider(OpenAICompatProvider):
    """
    Custom OpenAI-compatible provider for local servers.
    
    Supports Ollama, LM Studio, LocalAI, vLLM, etc.
    """
    
    def __init__(
        self,
        api_key: str = "not-needed",
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3",
        **kwargs
    ):
        config = ProviderConfig(
            name="custom",
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000),
            timeout=kwargs.get("timeout", 120),  # Longer timeout for local
        )
        super().__init__(config)
    
    def get_model_name(self) -> str:
        return self.config.model


# Provider presets for common services
PRESETS = {
    # Cloud providers
    "openai": {"class": OpenAIProvider, "default_model": "gpt-3.5-turbo"},
    "kimi": {"class": KimiProvider, "default_model": "moonshot-v1-8k"},
    "moonshot": {"class": KimiProvider, "default_model": "moonshot-v1-8k"},
    "claude": {"class": ClaudeProvider, "default_model": None},  # Auto-select
    "anthropic": {"class": ClaudeProvider, "default_model": None},
    "azure": {"class": AzureProvider, "default_model": None},
    
    # Chinese providers
    "deepseek": {"class": DeepSeekProvider, "default_model": "deepseek-chat"},
    "qwen": {"class": QwenProvider, "default_model": "qwen-turbo"},
    "zhipu": {"class": ZhipuProvider, "default_model": "glm-4"},
    "yi": {"class": OpenAIProvider, "default_model": "yi-34b-chat"},
    "minimax": {"class": OpenAIProvider, "default_model": "abab6.5s-chat"},
    
    # Local/Custom providers
    "ollama": {"class": CustomProvider, "default_model": "llama3"},
    "lmstudio": {"class": CustomProvider, "default_model": "llama-3-8b-instruct"},
    "localai": {"class": CustomProvider, "default_model": "llama-2-7b"},
    "vllm": {"class": CustomProvider, "default_model": "llama-2-7b"},
    "custom": {"class": CustomProvider, "default_model": "custom-model"},
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
        name: Provider name
        api_key: API key
        model: Optional model name override
        base_url: Optional base URL (required for custom providers)
        **kwargs: Additional arguments
    
    Returns:
        LLM provider instance
    
    Raises:
        ValueError: If provider is not supported
        ImportError: If required package not installed
    
    Examples:
        >>> create_provider("openai", "sk-xxx", model="gpt-4")
        >>> create_provider("ollama", model="llama3")
        >>> create_provider("claude", "sk-ant-xxx")  # Auto-select latest model
    """
    name = name.lower()
    
    if name not in PRESETS:
        # Check if it's a custom request
        if base_url:
            return CustomProvider(api_key=api_key or "not-needed", base_url=base_url, model=model or "custom-model", **kwargs)
        
        raise ValueError(
            f"Unsupported provider: '{name}'. Supported providers: {', '.join(PRESETS.keys())}"
        )
    
    preset = PRESETS[name]
    provider_class = preset["class"]
    
    # Get default model
    final_model = model or preset["default_model"]
    
    # Special handling for Azure (requires deployment name)
    if name == "azure":
        if not final_model:
            raise ValueError("Azure provider requires a deployment name")
        return provider_class(
            api_key=api_key or "",
            deployment=final_model,
            base_url=base_url,
            **kwargs
        )
    
    # Special handling for Claude (model is optional)
    if name in ["claude", "anthropic"]:
        return provider_class(api_key=api_key or "", model=model, **kwargs)
    
    # Standard provider creation
    return provider_class(
        api_key=api_key or "",
        model=final_model,
        base_url=base_url,
        **kwargs
    )


def get_provider_info(name: str) -> Dict[str, Any]:
    """Get information about a provider."""
    if name not in PRESETS:
        raise ValueError(f"Unknown provider: {name}")
    
    preset = PRESETS[name]
    return {
        "name": name,
        "class": preset["class"].__name__,
        "default_model": preset["default_model"],
        "is_cloud": name in ["openai", "kimi", "claude", "azure", "deepseek", "qwen", "zhipu", "yi", "minimax"],
        "requires_api_key": name not in ["ollama", "lmstudio", "localai", "vllm", "custom"],
    }


async def test_provider_async(
    name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    test_message: str = "Hello"
) -> Dict[str, Any]:
    """
    Test provider connection asynchronously.
    
    Returns:
        Dict with success status and details
    """
    try:
        provider = create_provider(
            name=name,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        
        messages = [{"role": "user", "content": test_message}]
        response = await provider.agenerate(messages, max_tokens=50)
        
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


def list_providers() -> Dict[str, Dict[str, Any]]:
    """List all available providers."""
    return {name: get_provider_info(name) for name in PRESETS}


if __name__ == "__main__":
    print("=" * 60)
    print("OpenThought Providers v3.0")
    print("=" * 60)
    
    print("\n📦 Cloud Providers:")
    for name in ["openai", "kimi", "claude", "azure", "deepseek", "qwen", "zhipu"]:
        info = get_provider_info(name)
        print(f"  • {name}: {info['default_model'] or 'dynamic'}")
    
    print("\n🏠 Local Providers:")
    for name in ["ollama", "lmstudio", "localai", "vllm"]:
        info = get_provider_info(name)
        print(f"  • {name}: {info['default_model']}")
    
    print("\n✨ New Features:")
    print("  • Async/await support (agenerate)")
    print("  • Streaming responses (astream_generate)")
    print("  • Automatic retry on failures")
    print("  • Unified provider interface")
    
    print("\n💡 Usage:")
    print("""
    # Sync
    provider = create_provider("openai", "sk-xxx")
    response = provider.generate(messages)
    
    # Async
    response = await provider.agenerate(messages)
    
    # Streaming
    async for chunk in provider.astream_generate(messages):
        print(chunk, end="", flush=True)
    """)
