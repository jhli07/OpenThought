"""
OpenThought - AI-Powered Chain-of-Thought Tool for Deep Reflection.

A sophisticated thinking assistant that uses LLMs to guide users through
deep, meaningful conversations using the Socratic method.

Author: Agent_Li
License: MIT
Repository: https://github.com/jhli07/OpenThought

Features:
- 🧠 AI-powered Socratic questioning
- 🔌 Support for 10+ LLM providers (OpenAI, Kimi, Claude, Ollama, Qwen, etc.)
- 💾 Session persistence (JSON/SQLite)
- 🎨 Beautiful CLI and Web interfaces
- 🎯 Fully customizable via config or API
"""

from .core import OpenThought, OpenThoughtError, Session
from .providers import (
    create_provider,
    BaseLLMProvider,
    CustomProvider,
    list_all_providers,
    test_provider_connection,
    CUSTOM_PROVIDER_PRESETS,
)
from .config import Config, load_config
from .storage import JSONStorage, SQLiteStorage, SessionManager

__version__ = "2.0.0"
__author__ = "Agent_Li"
__license__ = "MIT"

__all__ = [
    # Core
    "OpenThought",
    "OpenThoughtError",
    "Session",
    # Providers
    "create_provider",
    "BaseLLMProvider",
    "CustomProvider",
    "list_all_providers",
    "test_provider_connection",
    "CUSTOM_PROVIDER_PRESETS",
    # Config
    "Config",
    "load_config",
    # Storage
    "JSONStorage",
    "SQLiteStorage",
    "SessionManager",
]
