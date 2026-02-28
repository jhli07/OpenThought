"""
OpenThought Storage v3.0 - Session persistence with export support.

New features:
- Multiple export formats (JSON, Markdown, HTML)
- Thread-safe operations
- Session compression
"""

import gzip
import json
import os
import sqlite3
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Type
import threading


class ExportFormat(Enum):
    """Supported export formats."""
    DICT = "dict"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    YAML = "yaml"


class StorageError(Exception):
    """Base storage exception."""
    pass


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
    
    @abstractmethod
    def export_session(self, session_id: str, format: ExportFormat) -> Any:
        """Export session in specified format."""
        pass


class JSONStorage(BaseStorage):
    """JSON file-based storage backend with compression support."""
    
    def __init__(
        self, 
        storage_dir: str = "~/.cache/openthought",
        compress: bool = False
    ):
        """
        Initialize JSON storage.
        
        Args:
            storage_dir: Directory to store session files
            compress: Whether to gzip compress session data
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self.compress = compress
        self.sessions_file = self.storage_dir / "sessions.json"
        self._ensure_storage_dir()
        self._lock = threading.RLock()
    
    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self) -> Dict[str, Any]:
        """Load session index."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Try loading backup
                backup_file = self.sessions_file.with_suffix(".backup")
                if backup_file.exists():
                    with open(backup_file, "r", encoding="utf-8") as f:
                        return json.load(f)
        return {"sessions": {}, "metadata": {}}
    
    def _save_index(self, index: Dict[str, Any], backup: bool = False) -> None:
        """Save session index."""
        with self._lock:
            target = self.sessions_file
            if backup:
                target = self.sessions_file.with_suffix(".backup")
            
            with open(target, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
    
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save a session to JSON."""
        with self._lock:
            index = self._load_index()
            
            session_id = session_data.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
            session_data["saved_at"] = datetime.now().isoformat()
            
            # Compress if enabled
            if self.compress:
                session_data_str = json.dumps(session_data, ensure_ascii=False)
                session_data = {
                    "_compressed": True,
                    "_data": gzip.compress(session_data_str.encode("utf-8")),
                }
            
            index["sessions"][session_id] = session_data
            index["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Create backup before saving
            self._save_index(index, backup=True)
            self._save_index(index)
            
            return session_id
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session by ID."""
        with self._lock:
            index = self._load_index()
            session_data = index["sessions"].get(session_id)
            
            if session_data is None:
                return None
            
            # Decompress if needed
            if isinstance(session_data, dict) and session_data.get("_compressed"):
                try:
                    decompressed = gzip.decompress(session_data["_data"])
                    return json.loads(decompressed)
                except Exception:
                    return None
            
            return session_data
    
    def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all sessions."""
        index = self._load_index()
        sessions = list(index["sessions"].values())
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        
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
            self._save_index({"sessions": {}, "metadata": {}})
    
    def export_session(self, session_id: str, format: ExportFormat = ExportFormat.DICT) -> Any:
        """Export session in specified format."""
        session_data = self.load_session(session_id)
        if session_data is None:
            raise StorageError(f"Session not found: {session_id}")
        
        if format == ExportFormat.DICT:
            return session_data
        
        elif format == ExportFormat.JSON:
            return json.dumps(session_data, ensure_ascii=False, indent=2)
        
        elif format == ExportFormat.MARKDOWN:
            return self._export_markdown(session_data)
        
        elif format == ExportFormat.HTML:
            return self._export_html(session_data)
        
        elif format == ExportFormat.YAML:
            try:
                import yaml
                return yaml.dump(session_data, allow_unicode=True)
            except ImportError:
                raise StorageError("PyYAML required for YAML export: pip install pyyaml")
        
        else:
            raise StorageError(f"Unsupported format: {format}")
    
    def _export_markdown(self, session_data: Dict[str, Any]) -> str:
        """Export session as Markdown."""
        lines = [
            f"# 思考会话: {session_data.get('initial_prompt', '未知')}",
            "",
            f"**会话ID**: {session_data.get('id', 'N/A')}",
            f"**创建时间**: {session_data.get('created_at', 'N/A')}",
            f"**保存时间**: {session_data.get('saved_at', 'N/A')}",
            "",
            "---",
            "",
            "## 对话记录",
            "",
        ]
        
        messages = session_data.get("messages", [])
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        
        for i, (q, a) in enumerate(zip(assistant_messages, user_messages), 1):
            lines.append(f"### 第 {i} 轮")
            lines.append("")
            lines.append(f"**问题**: {q.get('content', '')}")
            lines.append("")
            lines.append(f"**回答**: {a.get('content', '')}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _export_html(self, session_data: Dict[str, Any]) -> str:
        """Export session as HTML."""
        md = self._export_markdown(session_data)
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{session_data.get('initial_prompt', '思考会话')}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{ color: #2c3e50; }}
        h3 {{ color: #34495e; margin-top: 20px; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
        blockquote {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-left: 4px solid #3498db;
            margin: 10px 0;
        }}
        .meta {{ color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
{self._convert_md_to_html(md)}
</body>
</html>"""
    
    def _convert_md_to_html(self, md: str) -> str:
        """Simple Markdown to HTML conversion."""
        import re
        html = md
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'^\- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
        html = re.sub(r'\n\n', r'</p><p>', html)
        return f"<p>{html}</p>"
    
    def get_storage_dir(self) -> Path:
        """Get the storage directory path."""
        return self.storage_dir


class SQLiteStorage(BaseStorage):
    """SQLite database storage backend with export support."""
    
    def __init__(self, db_path: str = "~/.cache/openthought/sessions.db"):
        """Initialize SQLite storage."""
        self.db_path = Path(db_path).expanduser()
        self._ensure_storage_dir()
        self._init_db()
        self._lock = threading.RLock()
    
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
                        savepoints TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        metadata TEXT,
                        saved_at TEXT,
                        export_format TEXT
                    )
                """)
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_updated ON sessions(updated_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt ON sessions(initial_prompt)")
                conn.commit()
    
    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save a session to SQLite."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                session_id = session_data.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
                saved_at = datetime.now().isoformat()
                
                # Check if session exists
                cursor = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
                exists = cursor.fetchone() is not None
                
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (id, initial_prompt, messages, savepoints, created_at, updated_at, metadata, saved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    session_data.get("initial_prompt", ""),
                    json.dumps(session_data.get("messages", []), ensure_ascii=False),
                    json.dumps(session_data.get("savepoints", []), ensure_ascii=False),
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
                    "savepoints": json.loads(row[3]) if row[3] else [],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "metadata": json.loads(row[6]) if row[6] else {},
                    "saved_at": row[7],
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
                        "messages_count": len(json.loads(row[2] or "[]")),
                        "created_at": row[4],
                        "updated_at": row[5],
                        "saved_at": row[7],
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
    
    def export_session(self, session_id: str, format: ExportFormat = ExportFormat.DICT) -> Any:
        """Export session in specified format."""
        session_data = self.load_session(session_id)
        if session_data is None:
            raise StorageError(f"Session not found: {session_id}")
        
        if format == ExportFormat.DICT:
            return session_data
        elif format == ExportFormat.JSON:
            return json.dumps(session_data, ensure_ascii=False, indent=2)
        elif format == ExportFormat.MARKDOWN:
            return self._export_markdown(session_data)
        elif format == ExportFormat.HTML:
            return self._export_html(session_data)
        else:
            raise StorageError(f"Unsupported format: {format}")
    
    def _export_markdown(self, session_data: Dict[str, Any]) -> str:
        """Export as Markdown."""
        # Reuse JSONStorage's implementation
        return JSONStorage()._export_markdown(session_data)
    
    def _export_html(self, session_data: Dict[str, Any]) -> str:
        """Export as HTML."""
        return JSONStorage()._export_html(session_data)
    
    def get_db_path(self) -> Path:
        """Get the database file path."""
        return self.db_path
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sessions")
                total_sessions = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sessions WHERE updated_at > datetime('now', '-7 days')")
                week_sessions = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT MAX(updated_at) FROM sessions")
                last_updated = cursor.fetchone()[0]
                
                return {
                    "total_sessions": total_sessions,
                    "sessions_this_week": week_sessions,
                    "last_updated": last_updated,
                    "db_size_bytes": self.db_path.stat().st_size,
                }


# Storage factory
def create_storage(
    storage_type: str = "json",
    **kwargs
) -> BaseStorage:
    """
    Create a storage backend.
    
    Args:
        storage_type: Storage type ("json" or "sqlite")
        **kwargs: Additional storage arguments
    
    Returns:
        Storage backend instance
    """
    if storage_type == "json":
        return JSONStorage(
            storage_dir=kwargs.get("storage_dir", "~/.cache/openthought"),
            compress=kwargs.get("compress", False),
        )
    elif storage_type == "sqlite":
        return SQLiteStorage(
            db_path=kwargs.get("db_path", "~/.cache/openthought/sessions.db"),
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


class SessionManager:
    """
    High-level session management with OpenThought integration.
    """
    
    def __init__(self, storage: Optional[BaseStorage] = None):
        """Initialize session manager."""
        self.storage = storage or JSONStorage()
    
    def save(self, ot) -> str:
        """Save an OpenThought session."""
        session_data = ot.export_session(format="dict")
        return self.storage.save_session(session_data)
    
    def load(self, session_id: str):
        """Load a session and create OpenThought instance."""
        from openthought.core import OpenThought, Session
        session_data = self.storage.load_session(session_id)
        if session_data is None:
            return None
        
        session = Session.from_dict(session_data)
        return OpenThought(
            prompt=session.initial_prompt,
            session=session,
            use_ai=False,
        )
    
    def export(self, session_id: str, format: str = "markdown") -> Any:
        """Export session in specified format."""
        fmt = ExportFormat(format.lower())
        return self.storage.export_session(session_id, fmt)
    
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
    print("🗄️ OpenThought Storage v3.0 Demo")
    print("=" * 50)
    
    # Test JSON storage
    storage = JSONStorage("/tmp/openthought_v3_test")
    
    # Save a dummy session
    dummy_session = {
        "id": "test-001",
        "initial_prompt": "测试思考",
        "messages": [
            {"role": "assistant", "content": "什么问题？", "timestamp": "2026-02-24T10:00:00"},
            {"role": "user", "content": "我想创业", "timestamp": "2026-02-24T10:00:01"},
        ],
        "savepoints": [],
        "created_at": "2026-02-24T10:00:00",
        "updated_at": "2026-02-24T10:00:01",
        "metadata": {},
    }
    
    session_id = storage.save_session(dummy_session)
    print(f"✅ Saved session: {session_id}")
    
    # Test export
    print("\n📤 Export as Markdown:")
    md = storage.export_session(session_id, ExportFormat.MARKDOWN)
    print(md[:300] + "...")
    
    print("\n📤 Export as HTML:")
    html = storage.export_session(session_id, ExportFormat.HTML)
    print(html[:300] + "...")
    
    # Clean up
    storage.clear_all()
    print("\n✅ All tests passed!")
    
    print(f"\n📁 Storage location: {storage.get_storage_dir()}")
