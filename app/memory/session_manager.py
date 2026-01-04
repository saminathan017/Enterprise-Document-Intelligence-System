"""
Session manager for persistent conversation state.
Handles session lifecycle and storage.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.config import settings


class SessionManager:
    """Manages session lifecycle and persistence."""
    
    def __init__(self, persist_dir: Path = None):
        """
        Initialize session manager.
        
        Args:
            persist_dir: Directory for session storage
        """
        self.persist_dir = persist_dir or settings.session_persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timedelta(minutes=settings.session_timeout_minutes)
    
    def create_session(self) -> str:
        """
        Create a new session.
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "message_count": 0,
            "history": []
        }
        
        self._save_session(session_id, session_data)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dict or None if not found/expired
        """
        session_file = self.persist_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file, "r") as f:
            session_data = json.load(f)
        
        # Check if session has expired
        last_activity = datetime.fromisoformat(session_data["last_activity"])
        if datetime.utcnow() - last_activity > self.timeout:
            # Session expired
            self.delete_session(session_id)
            return None
        
        return session_data
    
    def update_session(
        self,
        session_id: str,
        history: list = None,
        increment_count: bool = True
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            history: Updated conversation history
            increment_count: Whether to increment message count
            
        Returns:
            True if updated successfully
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Update last activity
        session_data["last_activity"] = datetime.utcnow().isoformat()
        
        # Update history
        if history is not None:
            session_data["history"] = history
        
        # Increment message count
        if increment_count:
            session_data["message_count"] += 1
        
        self._save_session(session_id, session_data)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        session_file = self.persist_dir / f"{session_id}.json"
        
        if session_file.exists():
            session_file.unlink()
            return True
        return False
    
    def clear_session_history(self, session_id: str) -> bool:
        """
        Clear conversation history but keep session active.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleared successfully
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data["history"] = []
        session_data["message_count"] = 0
        session_data["last_activity"] = datetime.utcnow().isoformat()
        
        self._save_session(session_id, session_data)
        return True
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save session data to disk."""
        session_file = self.persist_dir / f"{session_id}.json"
        
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
    
    def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions.
        
        Returns:
            Number of sessions deleted
        """
        deleted_count = 0
        
        for session_file in self.persist_dir.glob("*.json"):
            session_id = session_file.stem
            
            with open(session_file, "r") as f:
                session_data = json.load(f)
            
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            if datetime.utcnow() - last_activity > self.timeout:
                session_file.unlink()
                deleted_count += 1
        
        return deleted_count


# Global singleton instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
