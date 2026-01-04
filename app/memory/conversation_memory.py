"""
Conversation memory for multi-turn context.
Integrates with LangChain memory and session persistence.
"""

from typing import List, Dict, Any
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from app.memory.session_manager import SessionManager


class ConversationMemory:
    """Manages multi-turn conversation context."""
    
    def __init__(self, session_id: str, session_manager: SessionManager):
        """
        Initialize conversation memory.
        
        Args:
            session_id: Session identifier
            session_manager: SessionManager instance
        """
        self.session_id = session_id
        self.session_manager = session_manager
        
        # Initialize chat history
        self.chat_history = ChatMessageHistory()
        
        # Load existing history
        self._load_history()
    
    def add_user_message(self, message: str):
        """
        Add user message to history.
        
        Args:
            message: User message text
        """
        self.chat_history.add_user_message(message)
        self._persist_history()
    
    def add_ai_message(self, message: str):
        """
        Add AI response to history.
        
        Args:
            message: AI message text
        """
        self.chat_history.add_ai_message(message)
        self._persist_history()
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        messages = self.chat_history.messages
        
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history
    
    def get_context_string(self) -> str:
        """
        Get conversation history as a formatted string.
        
        Returns:
            Formatted history string
        """
        history = self.get_history()
        
        if not history:
            return "No previous conversation."
        
        context_parts = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def clear_history(self):
        """Clear all conversation history."""
        self.chat_history.clear()
        self.session_manager.clear_session_history(self.session_id)
    
    def _load_history(self):
        """Load conversation history from session store."""
        session_data = self.session_manager.get_session(self.session_id)
        
        if not session_data or not session_data.get("history"):
            return
        
        # Reconstruct chat history from stored messages
        for msg in session_data["history"]:
            if msg["role"] == "user":
                self.chat_history.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                self.chat_history.add_ai_message(msg["content"])
    
    def _persist_history(self):
        """Save conversation history to session store."""
        history = self.get_history()
        self.session_manager.update_session(
            session_id=self.session_id,
            history=history,
            increment_count=False  # We'll increment separately on actual queries
        )
