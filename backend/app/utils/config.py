import os

try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    # MongoDB config (optional - only needed for Docker/production with persistent chat history)
    # For local testing, MongoDB is optional - will use in-memory storage
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "chatbot_db")
except Exception:
    OPENAI_API_KEY = None
    CHAT_MODEL = "gpt-4o-mini"
    MONGODB_URI = "mongodb://localhost:27017"  # Not used in local testing mode
    MONGODB_DB = "chatbot_db"  # Not used in local testing mode

