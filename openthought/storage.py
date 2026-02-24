"""
OpenThought Storage - Session persistence and history management.

Supports JSON and SQLite backends for storing thinking sessions.
"""

import json
import os
import sqlite3
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import threading


class BaseStorage(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save a session, return session ID."""
        pass
    
    @abstractmethod
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session by ID."""
        pass
    
    @abstractmethod
    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all sessions."""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """Clear all sessions."""
        pass


class JSONStorage(BaseStorage):
    """JSON file-based storage backend."""
    
    def __init__(self, storage_dir: str = "~/.cache/openthought"):
        """
        Initialize JSON storage.
        
        Args:
            storage_dir: Directory to store session files
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self.sessions_file = self.storage_dir / "sessions.json"
        self._ensure_storage_dir()
        self._lock = threading.Lock()
    
    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self) -> Dict[str, Any]:
        """Load session index."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"sessions": {}}
        return {"sessions": {}}
    
    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save session index."""
        with self._lock:
            with open(self.sessions_file, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
    
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save a session to JSON."""
        with self._lock:
            index = self._load_index()
            
            session_id = session_data.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
            session_data["saved_at"] = datetime.now().isoformat()
            
            index["sessions"][session_id] = session_data
            self._save_index(index)
            
            return session_id
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session by ID."""
        index = self._load_index()
        return index["sessions"].get(session_id)
    
    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all sessions."""
        index = self._load_index()
        sessions = list(index["sessions"].values())
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self._lock:
            index = self._load_index()
            
            if session_id in index["sessions"]:
                del index["sessions"][session_id]
                self._save_index(index)
                return True
            return False
    
    def clear_all(self) -> None:
        """Clear all sessions."""
        with self._lock:
            self._save_index({"sessions": {}})
    
    def get_storage_dir(self) -> Path:
        """Get the storage directory path."""
        return self.storage_dir


class SQLiteStorage(BaseStorage):
    """SQLite database storage backend."""
    
    def __init__(self, db_path: str = "~/.cache/openthought/sessions.db"):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path).expanduser()
        self._ensure_storage_dir()
        self._init_db()
        self._lock = threading.Lock()
    
    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        initial_prompt TEXT,
                        messages TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        metadata TEXT,
                        saved_at TEXT
                    )
                """)
                conn.commit()
    
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save a session to SQLite."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                session_id = session_data.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
                saved_at = datetime.now().isoformat()
                
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (id, initial_prompt, messages, created_at, updated_at, metadata, saved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    session_data.get("initial_prompt", ""),
                    json.dumps(session_data.get("messages", []), ensure_ascii=False),
                    session_data.get("created_at", datetime.now().isoformat()),
                    session_data.get("updated_at", datetime.now().isoformat()),
                    json.dumps(session_data.get("metadata", {}), ensure_ascii=False),
                    saved_at,
                ))
                conn.commit()
            
            return session_id
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session by ID."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM sessions WHERE id = ?", (session_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return {
                    "id": row[0],
                    "initial_prompt": row[1],
                    "messages": json.loads(row[2]),
                    "created_at": row[3],
                    "updated_at": row[4],
                    "metadata": json.loads(row[5]),
                    "saved_at": row[6],
                }
    
    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all sessions."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                )
                
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    sessions.append({
                        "id": row[0],
                        "initial_prompt": row[1],
                        "messages": json.loads(row[2]),
                        "created_at": row[3],
                        "updated_at": row[4],
                        "metadata": json.loads(row[5]),
                        "saved_at": row[6],
                    })
                
                return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE id = ?", (session_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
    
    def clear_all(self) -> None:
        """Clear all sessions."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM sessions")
                conn.commit()
    
    def get_db_path(self) -> Path:
        """Get the database file path."""
        return self.db_path


# Storage factory
def create_storage(storage_type: str = "json", **kwargs) -> BaseStorage:
    """
    Create a storage backend.
    
    Args:
        storage_type: Storage type ("json" or "sqlite")
        **kwargs: Additional storage arguments
    
    Returns:
        Storage backend instance
    
    Raises:
        ValueError: If storage type is not supported
    
    Example:
        >>> from openthought.storage import create_storage
        >>> storage = create_storage("sqlite", db_path="./data/sessions.db")
    """
    if storage_type == "json":
        return JSONStorage(kwargs.get("storage_dir", "~/.cache/openthought"))
    elif storage_type == "sqlite":
        return SQLiteStorage(kwargs.get("db_path", "~/.cache/openthought/sessions.db"))
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


class SessionManager:
    """
    High-level session management with OpenThought integration.
    """
    
    def __init__(self, storage: Optional[BaseStorage] = None):
        """
        Initialize session manager.
        
        Args:
            storage: Storage backend (default: JSONStorage)
        """
        self.storage = storage or JSONStorage()
    
    def save(self, ot: "OpenThought") -> str:
        """
        Save an OpenThought session.
        
        Args:
            ot: OpenThought instance
        
        Returns:
            Session ID
        """
        session_data = ot.export_session()
        return self.storage.save_session(session_data)
    
    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            Session data dict or None
        """
        return self.storage.load_session(session_id)
    
    def list_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all saved sessions."""
        return self.storage.list_sessions(limit)
    
    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        return self.storage.delete_session(session_id)
    
    def clear(self) -> None:
        """Clear all sessions."""
        self.storage.clear_all()


if __name__ == "__main__":
    # Demo
    print("🗄️ OpenThought Storage Demo")
    print("=" * 50)
    
    # Test JSON storage
    storage = JSONStorage("/tmp/openthought_test")
    manager = SessionManager(storage)
    
    # Save a dummy session
    dummy_session = {
        "id": "test-001",
        "initial_prompt": "测试思考",
        "messages": [
            {"role": "assistant", "content": "什么问题？", "timestamp": "2026-02-24T10:00:00"},
            {"role": "user", "content": "我想创业", "timestamp": "2026-02-24T10:00:01"},
        ],
        "created_at": "2026-02-24T10:00:00",
        "updated_at": "2026-02-24T10:00:01",
        "metadata": {},
    }
    
    session_id = storage.save_session(dummy_session)
    print(f"✅ Saved session: {session_id}")
    
    # Load it back
    loaded = storage.load_session(session_id)
    print(f"✅ Loaded session: {loaded['initial_prompt']}")
    
    # List all
    all_sessions = storage.list_sessions()
    print(f"✅ Total sessions: {len(all_sessions)}")
    
    # Clean up
    storage.clear_all()
    print("✅ Cleared all sessions")
    
    print("\n📁 Storage location:", storage.get_storage_dir())
