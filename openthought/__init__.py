"""
OpenThought - AI-Powered Chain-of-Thought Tool for Deep Reflection.

A sophisticated thinking assistant that uses LLMs to guide users through
deep, meaningful conversations using the Socratic method.

Author: Agent_Li
License: MIT
Repository: https://github.com/jhli07/OpenThought
"""

from .core import OpenThought, OpenThoughtError, Session
from .providers import create_provider, BaseLLMProvider
from .config import Config, load_config
from .storage import JSONStorage

__version__ = "2.0.0"
__author__ = "Agent_Li"
__license__ = "MIT"

__all__ = [
    "OpenThought",
    "OpenThoughtError", 
    "Session",
    "create_provider",
    "BaseLLMProvider",
    "Config",
    "load_config",
    "JSONStorage",
]
