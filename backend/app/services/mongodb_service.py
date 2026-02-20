# from typing import List, Dict, Optional
# from datetime import datetime
# from app.utils.custom_logging import custom_logger

# log = custom_logger()

# # MongoDB Service - Optional (for Docker/production with persistent storage)
# # For local testing without MongoDB, this service uses in-memory storage
# # MongoDB connection only attempted if pymongo is available and MongoDB is running
# class MongoDBService:
#     def __init__(self):
#         # Try to connect to MongoDB (optional for local testing)
#         self.client = None
#         self.db = None
#         self.chats = None
#         self.local_chats = {}  # In-memory storage for local testing
        
#         try:
#             # Only import/connect if MongoDB is needed (Docker/production)
#             from pymongo import MongoClient
#             from app.utils.config import MONGODB_URI, MONGODB_DB
            
#             self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
#             self.db = self.client[MONGODB_DB]
#             self.chats = self.db.chats
#             # Test connection
#             self.client.admin.command('ping')
#             log.info("MongoDB connected")
#         except Exception as e:
#             log.info(f"MongoDB not available - using in-memory storage for local testing: {e}")
#             self.client = None
#             self.db = None
#             self.chats = None
    
#     def save_chat(self, session_id: str, messages: List[Dict]):
#         try:
#             # MongoDB mode (Docker/production)
#             if self.chats:
#                 self.chats.update_one(
#                     {"session_id": session_id},
#                     {"$set": {"messages": messages, "updated_at": datetime.now()}},
#                     upsert=True
#                 )
#             else:
#                 # Local in-memory mode (for testing without MongoDB)
#                 self.local_chats[session_id] = messages
#         except Exception as e:
#             log.error(f"Error saving chat: {e}")
    
#     def get_chat_history(self, session_id: str) -> List[Dict]:
#         try:
#             # MongoDB mode (Docker/production)
#             if self.chats:
#                 doc = self.chats.find_one({"session_id": session_id})
#                 return doc.get("messages", []) if doc else []
#             else:
#                 # Local in-memory mode (for testing without MongoDB)
#                 return self.local_chats.get(session_id, [])
#         except Exception as e:
#             log.error(f"Error getting chat history: {e}")
#             return []
    
#     def close(self):
#         try:
#             if self.client:
#                 self.client.close()
#         except Exception:
#             pass

# mongodb_service = MongoDBService()

from typing import List, Dict
from datetime import datetime
from app.utils.custom_logging import custom_logger

log = custom_logger()

class MongoDBService:
    def __init__(self):
        self.client = None
        self.db = None
        self.chats = None
        self.local_chats = {}

        try:
            from pymongo import MongoClient
            from app.utils.config import MONGODB_URI, MONGODB_DB

            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
            self.db = self.client[MONGODB_DB]
            self.chats = self.db.chats
            self.client.admin.command("ping")
            log.info("MongoDB connected")
        except Exception as e:
            log.warning(f"MongoDB unavailable, using memory: {e}")
            self.client = None
            self.db = None
            self.chats = None

    def save_chat(self, session_id: str, messages: List[Dict]):
        try:
            if self.chats is not None:
                self.chats.update_one(
                    {"session_id": session_id},
                    {"$set": {"messages": messages, "updated_at": datetime.utcnow()}},
                    upsert=True,
                )
            else:
                self.local_chats[session_id] = messages
        except Exception as e:
            log.error(f"Error saving chat: {e}")

    def get_chat_history(self, session_id: str) -> List[Dict]:
        try:
            if self.chats is not None:
                doc = self.chats.find_one({"session_id": session_id})
                return doc.get("messages", []) if doc else []
            return self.local_chats.get(session_id, [])
        except Exception as e:
            log.error(f"Error getting chat history: {e}")
            return []

    def get_all_sessions(self) -> List[Dict]:
        """
        Get all sessions with their metadata (session_id, message_count, updated_at)
        """
        try:
            if self.chats is not None:
                sessions = []
                for doc in self.chats.find({}, {"session_id": 1, "messages": 1, "updated_at": 1}):
                    session_info = {
                        "session_id": doc.get("session_id", ""),
                        "message_count": len(doc.get("messages", [])),
                        "updated_at": doc.get("updated_at", "").isoformat() if doc.get("updated_at") else ""
                    }
                    sessions.append(session_info)
                return sessions
            else:
                # For in-memory storage
                sessions = []
                for session_id, messages in self.local_chats.items():
                    sessions.append({
                        "session_id": session_id,
                        "message_count": len(messages),
                        "updated_at": ""
                    })
                return sessions
        except Exception as e:
            log.error(f"Error getting all sessions: {e}")
            return []

mongodb_service = MongoDBService()


