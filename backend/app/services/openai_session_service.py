from typing import List, Dict, Optional
from datetime import datetime
import json
import os
from openai import OpenAI
from app.utils.custom_logging import custom_logger
from app.utils.config import OPENAI_API_KEY

log = custom_logger()

class OpenAISessionService:
    """Service using OpenAI Conversations API for state management"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not found")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.metadata_file = os.path.join(os.path.dirname(__file__), "../../sessions/_metadata.json")
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_metadata(self):
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            log.error(f"Error saving metadata: {e}")
    
    def create_session(self, session_id: str, initial_message: Optional[str] = None) -> str:
        """Create conversation using OpenAI Conversations API"""
        try:
            conversation = self.client.conversations.create()
            conv_id = conversation.id
            
            self.metadata[session_id] = {
                "conversation_id": conv_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "title": (initial_message[:50] + "...") if initial_message and len(initial_message) > 50 else (initial_message or "New Chat")
            }
            self._save_metadata()
            log.info(f"Created conversation {conv_id} for session {session_id}")
            return conv_id
        except Exception as e:
            log.warning(f"Conversations API not available, using local storage: {e}")
            # Fallback to local storage
            self.metadata[session_id] = {
                "conversation_id": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "title": (initial_message[:50] + "...") if initial_message and len(initial_message) > 50 else (initial_message or "New Chat"),
                "messages": []
            }
            self._save_metadata()
            return session_id
    
    def get_conversation_id(self, session_id: str) -> Optional[str]:
        """Get conversation ID for session"""
        return self.metadata.get(session_id, {}).get("conversation_id")
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """Retrieve messages from local storage (primary source)"""
        try:
            # Primary source: local storage (always reliable)
            local_messages = self.metadata.get(session_id, {}).get("messages", [])
            
            # If we have local messages, return them
            if local_messages:
                return local_messages
            
            # If no local messages, try to get from OpenAI Conversation (optional sync)
            conv_id = self.get_conversation_id(session_id)
            if conv_id:
                try:
                    conversation = self.client.conversations.retrieve(conv_id)
                    messages = []
                    
                    # Access items from conversation object
                    if hasattr(conversation, 'items') and conversation.items:
                        for item in conversation.items:
                            role = getattr(item, 'role', 'user')
                            content = ""
                            
                            # Handle different content formats
                            if hasattr(item, 'content'):
                                if isinstance(item.content, list):
                                    # Content is a list of content blocks
                                    content_parts = []
                                    for c in item.content:
                                        if hasattr(c, 'text'):
                                            content_parts.append(c.text)
                                        elif isinstance(c, str):
                                            content_parts.append(c)
                                        elif isinstance(c, dict) and 'text' in c:
                                            content_parts.append(c['text'])
                                    content = "".join(content_parts)
                                elif isinstance(item.content, str):
                                    content = item.content
                                elif hasattr(item.content, 'text'):
                                    content = item.content.text
                            
                            messages.append({"role": role, "content": str(content)})
                    
                    # If we got messages from OpenAI, save them locally
                    if messages:
                        if session_id not in self.metadata:
                            self.metadata[session_id] = {}
                        self.metadata[session_id]["messages"] = messages
                        self._save_metadata()
                    
                    return messages
                except Exception as e:
                    log.warning(f"Could not retrieve from conversation: {e}")

            # Return empty if nothing found
            return []

        except Exception as e:
            log.error(f"Error getting chat history: {e}")
            return self.metadata.get(session_id, {}).get("messages", [])

    
    def save_chat(self, session_id: str, messages: List[Dict]):
        """Save chat to conversation or local storage"""
        try:
            if session_id not in self.metadata:
                self.create_session(session_id)
            
            # Always store messages locally as backup
            self.metadata[session_id]["messages"] = messages
            self.metadata[session_id]["updated_at"] = datetime.utcnow().isoformat()
            
            # Try to save to OpenAI conversation using Responses API
            conv_id = self.get_conversation_id(session_id)
            if conv_id:
                try:
                    # Get last user and assistant messages
                    user_msg = next((m for m in reversed(messages) if m.get("role") == "user"), None)
                    assistant_msg = next((m for m in reversed(messages) if m.get("role") == "assistant"), None)
                    
                    if user_msg and assistant_msg:
                        # Use Responses API to add to conversation
                        self.client.responses.create(
                            model="gpt-4o-mini",
                            input=[
                                {"role": "user", "content": user_msg.get("content", "")},
                                {"role": "assistant", "content": assistant_msg.get("content", "")}
                            ],
                            conversation=conv_id,
                            store=True
                        )
                except Exception as e:
                    log.warning(f"Could not save to OpenAI conversation (using local storage): {e}")
            
            # Update title
            first_user = next((m for m in messages if m.get("role") == "user"), None)
            if first_user and (not self.metadata[session_id].get("title") or self.metadata[session_id].get("title") == "New Chat"):
                content = first_user.get("content", "")
                self.metadata[session_id]["title"] = content[:50] + "..." if len(content) > 50 else content
            
            self._save_metadata()
        except Exception as e:
            log.error(f"Error saving chat: {e}")
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all session metadata"""
        sessions = [{
            "session_id": sid,
            "title": meta.get("title", "New Chat"),
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at")
        } for sid, meta in self.metadata.items()]
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions
    
    def delete_session(self, session_id: str):
        """Delete conversation and metadata"""
        try:
            conv_id = self.get_conversation_id(session_id)
            if conv_id:
                try:
                    self.client.conversations.delete(conv_id)
                except:
                    pass
            
            if session_id in self.metadata:
                del self.metadata[session_id]
                self._save_metadata()
            log.info(f"Deleted session {session_id}")
        except Exception as e:
            log.error(f"Error deleting session: {e}")

openai_session_service = OpenAISessionService()
