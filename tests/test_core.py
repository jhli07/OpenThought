"""
OpenThought Unit Tests.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from openthought.core import (
    OpenThought, 
    Session, 
    Message, 
    OpenThoughtError,
    BaseLLMProvider,
)
from openthought.providers import (
    create_provider,
    OpenAIProvider,
    KimiProvider,
    get_available_providers,
)
from openthought.config import (
    Config, 
    ConfigLoader, 
    load_config, 
    LLMConfig,
)
from openthought.storage import (
    JSONStorage, 
    SQLiteStorage, 
    SessionManager,
    create_storage,
)


# ============================================
# Core Tests
# ============================================

class TestMessage:
    """Tests for Message class."""
    
    def test_message_creation(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None
    
    def test_message_to_dict(self):
        msg = Message(role="assistant", content="Hi there")
        data = msg.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Hi there"
    
    def test_message_from_dict(self):
        data = {"role": "user", "content": "Test", "timestamp": "2026-01-01"}
        msg = Message.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "Test"


class TestSession:
    """Tests for Session class."""
    
    def test_session_creation(self):
        session = Session(initial_prompt="Test prompt")
        assert session.initial_prompt == "Test prompt"
        assert session.id is not None
        assert len(session.messages) == 0
    
    def test_add_message(self):
        session = Session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")
        assert len(session.messages) == 2
    
    def test_session_to_dict(self):
        session = Session(initial_prompt="My prompt")
        session.add_message("user", "Q1")
        session.add_message("assistant", "A1")
        
        data = session.to_dict()
        assert data["initial_prompt"] == "My prompt"
        assert len(data["messages"]) == 2
    
    def test_session_from_dict(self):
        data = {
            "id": "test-123",
            "initial_prompt": "Hello",
            "messages": [
                {"role": "user", "content": "Hi", "timestamp": "2026-01-01"}
            ],
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "metadata": {},
        }
        session = Session.from_dict(data)
        assert session.id == "test-123"
        assert session.initial_prompt == "Hello"


class TestOpenThought:
    """Tests for OpenThought class."""
    
    def test_basic_init(self):
        ot = OpenThought(prompt="Test", use_ai=False)
        assert ot.prompt == "Test"
        assert ot.use_ai is False
        assert len(ot.questions) == 0
    
    def test_think_without_ai(self):
        ot = OpenThought(prompt="我想创业", use_ai=False)
        q1 = ot.think()
        assert "什么" in q1
        
        q2 = ot.think()
        assert "具体" in q2 or "为什么" in q2
    
    def test_ark_without_answer(self):
        ot = OpenThought(prompt="Test", use_ai=False)
        with pytest.raises(OpenThoughtError):
            ot.ark("test")
    
    def test_ark_after_think(self):
        ot = OpenThought(prompt="Test", use_ai=False)
        ot.think()
        ot.ark("My answer")
        assert len(ot.answers) == 1
        assert ot.answers[0] == "My answer"
    
    def test_print_trace(self):
        ot = OpenThought(prompt="创业", use_ai=False)
        ot.think()
        ot.ark("赚钱")
        ot.think()
        # Should not raise
        ot.print_trace()
    
    def test_get_insights(self):
        ot = OpenThought(prompt="创业", use_ai=False)
        ot.think()
        ot.ark("赚钱")
        ot.think()
        ot.ark("自由")
        
        insights = ot.get_insights()
        assert len(insights) > 0
    
    def test_reset(self):
        ot = OpenThought(prompt="Test", use_ai=False)
        ot.think()
        ot.ark("Answer")
        ot.reset()
        assert len(ot.questions) == 0
    
    def test_export_session(self):
        ot = OpenThought(prompt="Test", use_ai=False)
        ot.think()
        ot.ark("Answer")
        data = ot.export_session()
        assert data["initial_prompt"] == "Test"
        assert len(data["messages"]) == 2


# ============================================
# Provider Tests
# ============================================

class TestProviders:
    """Tests for LLM providers."""
    
    def test_get_available_providers(self):
        providers = get_available_providers()
        assert "openai" in providers
        assert "kimi" in providers
        assert "claude" in providers
    
    def test_create_provider_invalid(self):
        with pytest.raises(ValueError):
            create_provider("invalid_provider", "test-key")
    
    def test_provider_names(self):
        provider = create_provider("openai", "test-key")
        assert provider.provider_name == "openai"
        
        provider = create_provider("kimi", "test-key")
        assert provider.provider_name == "kimi"
        
        provider = create_provider("claude", "test-key")
        assert provider.provider_name == "claude"


# ============================================
# Config Tests
# ============================================

class TestConfig:
    """Tests for configuration."""
    
    def test_default_config(self):
        config = Config()
        assert config.debug is False
        assert config.use_ai is True
        assert config.llm.provider == "openai"
    
    def test_config_from_dict(self):
        data = {
            "debug": True,
            "use_ai": False,
            "llm": {
                "provider": "kimi",
                "model": "test-model",
            }
        }
        config = Config.from_dict(data)
        assert config.debug is True
        assert config.use_ai is False
        assert config.llm.provider == "kimi"
    
    def test_config_to_dict(self):
        config = Config()
        data = config.to_dict()
        assert "debug" in data
        assert "llm" in data


class TestConfigLoader:
    """Tests for ConfigLoader."""
    
    def test_load_config_file_not_found(self):
        loader = ConfigLoader()
        config = loader.load()
        assert isinstance(config, Config)


# ============================================
# Storage Tests
# ============================================

class TestJSONStorage:
    """Tests for JSON storage backend."""
    
    @pytest.fixture
    def storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield JSONStorage(tmpdir)
    
    def test_save_and_load_session(self, storage):
        session = {"id": "test-1", "initial_prompt": "Hello", "messages": []}
        session_id = storage.save_session(session)
        assert session_id is not None
        
        loaded = storage.load_session(session_id)
        assert loaded is not None
        assert loaded["initial_prompt"] == "Hello"
    
    def test_list_sessions(self, storage):
        storage.save_session({"id": "s1", "initial_prompt": "A", "messages": []})
        storage.save_session({"id": "s2", "initial_prompt": "B", "messages": []})
        
        sessions = storage.list_sessions(10)
        assert len(sessions) == 2
    
    def test_delete_session(self, storage):
        session = {"id": "delete-me", "initial_prompt": "Test", "messages": []}
        storage.save_session(session)
        
        result = storage.delete_session("delete-me")
        assert result is True
        
        loaded = storage.load_session("delete-me")
        assert loaded is None
    
    def test_clear_all(self, storage):
        storage.save_session({"id": "s1", "initial_prompt": "A", "messages": []})
        storage.save_session({"id": "s2", "initial_prompt": "B", "messages": []})
        
        storage.clear_all()
        
        sessions = storage.list_sessions()
        assert len(sessions) == 0


class TestSQLiteStorage:
    """Tests for SQLite storage backend."""
    
    @pytest.fixture
    def storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield SQLiteStorage(f"{tmpdir}/test.db")
    
    def test_save_and_load(self, storage):
        session = {"id": "sqlite-1", "initial_prompt": "Hello", "messages": []}
        session_id = storage.save_session(session)
        
        loaded = storage.load_session(session_id)
        assert loaded is not None
        assert loaded["initial_prompt"] == "Hello"
    
    def test_list_and_delete(self, storage):
        storage.save_session({"id": "sq1", "initial_prompt": "A", "messages": []})
        storage.save_session({"id": "sq2", "initial_prompt": "B", "messages": []})
        
        sessions = storage.list_sessions(10)
        assert len(sessions) == 2
        
        storage.delete_session("sq1")
        sessions = storage.list_sessions(10)
        assert len(sessions) == 1


class TestStorageFactory:
    """Tests for storage factory."""
    
    def test_create_json_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = create_storage("json", storage_dir=tmpdir)
            assert isinstance(storage, JSONStorage)
    
    def test_create_sqlite_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = create_storage("sqlite", db_path=f"{tmpdir}/test.db")
            assert isinstance(storage, SQLiteStorage)


# ============================================
# Integration Tests
# ============================================

class TestIntegration:
    """Integration tests."""
    
    def test_full_workflow(self):
        """Test complete workflow without AI."""
        from openthought import OpenThought
        from openthought.storage import SessionManager, JSONStorage
        
        # Create storage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JSONStorage(tmpdir)
            manager = SessionManager(storage)
            
            # Start thinking session
            ot = OpenThought(prompt="我想换工作", use_ai=False)
            
            # Answer a few questions
            ot.think()
            ot.ark("因为现在的工作没挑战")
            
            ot.think()
            ot.ark("我想学新技术"
            ot.think()
            ot.ark("Python 和 AI")
            
            # Get insights
            insights = ot.get_insights()
            assert len(insights) > 0
            
            # Save session
            session_id = manager.save(ot)
            assert session_id is not None
            
            # Load it back
            loaded = manager.load(session_id)
            assert loaded is not None
            assert loaded["initial_prompt"] == "我想换工作"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
