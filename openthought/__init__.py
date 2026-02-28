"""
OpenThought v3.0 - AI-Powered Chain-of-Thought Tool

A thinking tool that helps you explore ideas through AI-guided Socratic questioning.

New in v3.0:
- ✨ Streaming responses
- ⚡ Async/await support
- 🌿 Savepoints & branching
- 🎯 Multiple thinking styles
- 📤 Export to Markdown/HTML
- 🔧 Improved error handling
"""

__version__ = "3.0.0"
__author__ = "Agent_Li"

from openthought.core import (
    OpenThought,
    OpenThoughtError,
    ProviderError,
    ConfigurationError,
    Session,
    Message,
    Savepoint,
    ThinkingStyle,
    think,
)

from openthought.providers import (
    create_provider,
    list_providers,
    test_provider_async,
    BaseLLMProvider,
    OpenAIProvider,
    KimiProvider,
    ClaudeProvider,
    AzureProvider,
    CustomProvider,
    DeepSeekProvider,
    QwenProvider,
    ZhipuProvider,
)

from openthought.storage import (
    create_storage,
    SessionManager,
    JSONStorage,
    SQLiteStorage,
    ExportFormat,
)

__all__ = [
    # Version
    "__version__",
    
    # Core
    "OpenThought",
    "OpenThoughtError",
    "ProviderError",
    "ConfigurationError",
    "Session",
    "Message",
    "Savepoint",
    "ThinkingStyle",
    "think",
    
    # Providers
    "create_provider",
    "list_providers",
    "test_provider_async",
    "BaseLLMProvider",
    "OpenAIProvider",
    "KimiProvider",
    "ClaudeProvider",
    "AzureProvider",
    "CustomProvider",
    "DeepSeekProvider",
    "QwenProvider",
    "ZhipuProvider",
    
    # Storage
    "create_storage",
    "SessionManager",
    "JSONStorage",
    "SQLiteStorage",
    "ExportFormat",
]

# Convenience function for quick start
def chat(
    prompt: str,
    api_key: Optional[str] = None,
    provider: str = "openai",
    stream: bool = False,
    **kwargs
):
    """
    Quick chat interface for OpenThought.
    
    Args:
        prompt: The topic to discuss
        api_key: API key for the LLM
        provider: LLM provider name
        stream: Whether to stream response
        **kwargs: Additional arguments
    
    Returns:
        OpenThought instance
    """
    from openthought.providers import create_provider
    
    llm_provider = None
    use_ai = True
    
    if api_key:
        try:
            llm_provider = create_provider(provider, api_key)
        except Exception:
            use_ai = False
    else:
        use_ai = False
    
    return OpenThought(
        prompt=prompt,
        provider=llm_provider,
        use_ai=use_ai,
        stream=stream,
        **kwargs
    )
