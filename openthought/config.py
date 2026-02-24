"""
OpenThought Configuration - YAML-based configuration management.

Supports global config, user config, and per-session overrides.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import yaml


class ConfigSource(Enum):
    """Configuration source priority."""
    SYSTEM = "system"      # /etc/openthought/config.yaml
    USER = "user"          # ~/.config/openthought/config.yaml
    LOCAL = "local"        # ./openthought.yaml
    ENV = "env"            # Environment variables
    ARG = "arg"            # Command line arguments


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "openai"
    model: str = ""
    api_key: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass
class StorageConfig:
    """Storage configuration."""
    type: str = "json"  # json, sqlite
    path: str = "~/.cache/openthought"
    max_sessions: int = 100


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None


@dataclass
class Config:
    """Main configuration class."""
    # Core settings
    debug: bool = False
    show_thought: bool = True
    
    # LLM settings
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Storage settings
    storage: StorageConfig = field(default_factory=StorageConfig)
    
    # Logging settings
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Features
    use_ai: bool = True
    auto_save: bool = True
    max_questions: int = 20
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()
        
        if "debug" in data:
            config.debug = data["debug"]
        if "show_thought" in data:
            config.show_thought = data["show_thought"]
        if "use_ai" in data:
            config.use_ai = data["use_ai"]
        if "auto_save" in data:
            config.auto_save = data["auto_save"]
        if "max_questions" in data:
            config.max_questions = data["max_questions"]
        
        # LLM config
        if "llm" in data:
            llm_data = data["llm"]
            config.llm = LLMConfig(
                provider=llm_data.get("provider", "openai"),
                model=llm_data.get("model", ""),
                api_key=llm_data.get("api_key", ""),
                base_url=llm_data.get("base_url"),
                temperature=llm_data.get("temperature", 0.7),
                max_tokens=llm_data.get("max_tokens", 1000),
            )
        
        # Storage config
        if "storage" in data:
            storage_data = data["storage"]
            config.storage = StorageConfig(
                type=storage_data.get("type", "json"),
                path=storage_data.get("path", "~/.cache/openthought"),
                max_sessions=storage_data.get("max_sessions", 100),
            )
        
        # Logging config
        if "logging" in data:
            logging_data = data["logging"]
            config.logging = LoggingConfig(
                level=logging_data.get("level", "INFO"),
                format=logging_data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                file=logging_data.get("file"),
            )
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "debug": self.debug,
            "show_thought": self.show_thought,
            "use_ai": self.use_ai,
            "auto_save": self.auto_save,
            "max_questions": self.max_questions,
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "api_key": self.llm.api_key,
                "base_url": self.llm.base_url,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
            },
            "storage": {
                "type": self.storage.type,
                "path": self.storage.path,
                "max_sessions": self.storage.max_sessions,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file": self.logging.file,
            },
        }


class ConfigLoader:
    """Load and merge configurations from multiple sources."""
    
    def __init__(self):
        self.config_paths = [
            ("/etc/openthought/config.yaml", ConfigSource.SYSTEM),
            (Path.home() / ".config" / "openthought" / "config.yaml", ConfigSource.USER),
            (Path("openthought.yaml"), ConfigSource.LOCAL),
        ]
    
    def find_config_files(self) -> List[Path]:
        """Find all existing config files."""
        paths = []
        for path, _ in self.config_paths:
            path = Path(path)
            if path.exists():
                paths.append(path)
        return paths
    
    def load_file(self, path: Path) -> Dict[str, Any]:
        """Load a YAML config file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Warning: Error parsing {path}: {e}")
            return {}
        except FileNotFoundError:
            return {}
    
    def load(self, additional_config: Optional[Dict[str, Any]] = None) -> Config:
        """
        Load configuration from all sources.
        
        Priority (low to high):
        1. System config
        2. User config
        3. Local config
        4. Environment variables
        5. Additional config dict
        """
        config = Config()
        
        # Load from files in priority order
        for path, source in self.config_paths:
            path = Path(path)
            if path.exists():
                data = self.load_file(path)
                if data:
                    file_config = Config.from_dict(data)
                    # Merge into main config
                    config = self._merge(config, file_config)
        
        # Environment variables override
        config = self._apply_env(config)
        
        # Additional config (highest priority)
        if additional_config:
            add_config = Config.from_dict(additional_config)
            config = self._merge(config, add_config)
        
        return config
    
    def _merge(self, base: Config, override: Config) -> Config:
        """Merge two configs, override takes precedence."""
        if override.debug:
            base.debug = override.debug
        if not base.show_thought or override.show_thought != True:  # Keep default unless explicitly set
            base.show_thought = override.show_thought
        if not override.use_ai:  # Only override if explicitly False
            base.use_ai = override.use_ai
        if override.auto_save:
            base.auto_save = override.auto_save
        if override.max_questions != 10:  # Keep default unless changed
            base.max_questions = override.max_questions
        
        # Merge LLM config
        if override.llm.provider != "openai":
            base.llm.provider = override.llm.provider
        if override.llm.model:
            base.llm.model = override.llm.model
        if override.llm.api_key:
            base.llm.api_key = override.llm.api_key
        if override.llm.base_url:
            base.llm.base_url = override.llm.base_url
        if override.llm.temperature != 0.7:
            base.llm.temperature = override.llm.temperature
        if override.llm.max_tokens != 1000:
            base.llm.max_tokens = override.llm.max_tokens
        
        # Merge storage config
        if override.storage.type != "json":
            base.storage.type = override.storage.type
        if override.storage.path != "~/.cache/openthought":
            base.storage.path = override.storage.path
        if override.storage.max_sessions != 100:
            base.storage.max_sessions = override.storage.max_sessions
        
        # Merge logging config
        if override.logging.level != "INFO":
            base.logging.level = override.logging.level
        if override.logging.file:
            base.logging.file = override.logging.file
        
        return base
    
    def _apply_env(self, config: Config) -> Config:
        """Apply environment variable overrides."""
        # API keys
        if "OPENAI_API_KEY" in os.environ:
            config.llm.api_key = os.environ["OPENAI_API_KEY"]
        if "KIMI_API_KEY" in os.environ:
            config.llm.api_key = os.environ["KIMI_API_KEY"]
        if "ANTHROPIC_API_KEY" in os.environ:
            config.llm.api_key = os.environ["ANTHROPIC_API_KEY"]
        
        # Other settings
        if "OPENTHOUGHT_DEBUG" in os.environ:
            config.debug = os.environ["OPENTHOUGHT_DEBUG"].lower() == "true"
        if "OPENTHOUGHT_USE_AI" in os.environ:
            config.use_ai = os.environ["OPENTHOUGHT_USE_AI"].lower() == "true"
        
        return config


# Convenience functions
_config_loader = ConfigLoader()

def load_config(config_dict: Optional[Dict[str, Any]] = None) -> Config:
    """
    Load OpenThought configuration.
    
    Args:
        config_dict: Optional additional config dict
    
    Returns:
        Config instance
    
    Example:
        >>> config = load_config()
        >>> print(f"Using provider: {config.llm.provider}")
    """
    return _config_loader.load(config_dict)


def save_config(config: Config, path: Union[str, Path] = "openthought.yaml") -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Config to save
        path: Output file path
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)


if __name__ == "__main__":
    # Demo
    config = load_config()
    print("Current config:")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Debug: {config.debug}")
    print(f"  Show thought: {config.show_thought}")
    print(f"  Use AI: {config.use_ai}")
