from typing import Dict, List, Optional
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime
from app.utils.custom_logging import custom_logger
from app.chatbot.graph import graph
from app.chatbot.state import GraphState
from app.services.openai_session_service import openai_session_service

load_dotenv('.env')
log = custom_logger()
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):         #Define what frontend sends
    user_text: str
    chat: Optional[List[Dict]] = None
    session_id: str = "default"

class SessionRequest(BaseModel):                 # used when creating a new session
    session_id: Optional[str] = None

def dict_to_messages(chat_history: List[Dict]) -> List[BaseMessage]:   #converst json chat to langchain format
    messages = []
    try:
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    except Exception as e:
        log.error(f"Error converting dict to messages: {e}")
    return messages

def messages_to_dict(messages: List[BaseMessage]) -> List[Dict]:       #used before saving chat history
    result = []
    try:
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
    except Exception as e:
        log.error(f"Error converting messages to dict: {e}")
    return result

@app.get("/health")
def health():
    return {"status": "ok"}

async def stream_chat(user_text: str, session_id: str = "default", chat_history: Optional[List[Dict]] = None):
    try:
        # Get or create session
        if not chat_history:
            chat_history = openai_session_service.get_chat_history(session_id)
            # If no history exists, create new session
            if not chat_history:
                openai_session_service.create_session(session_id, user_text)
        
        messages = dict_to_messages(chat_history)                #convert history to langchain messgae
        messages.append(HumanMessage(content=user_text))
        
        state: GraphState = {             #tells langgraph conversation , Start from supervisor
            "messages": messages,
            "next": "supervisor"
        }
        
        final_state = None
        async for chunk in graph.astream(state):
            final_state = chunk
        
        final_response = ""
        if final_state:
            for node_name, node_state in final_state.items():
                if "messages" in node_state and node_state["messages"]:
                    for msg in node_state["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            final_response = msg.content
                            break
        
        if final_response:
            for char in final_response:   #send response charcater by character
                yield char
            updated_messages = messages + [AIMessage(content=final_response)]
            openai_session_service.save_chat(session_id, messages_to_dict(updated_messages)) # save chat history
        else:
            yield "No response generated."
    except Exception as e:
        log.error(f"Stream chat error: {e}")
        yield f"Error: {str(e)}"

@app.post("/chat-stream")        # used  for live typing
async def chat_stream(request: ChatRequest):
    async def event_generator():
        async for chunk in stream_chat(request.user_text, request.session_id, request.chat):
            yield chunk
    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/get-chat-response")       # full response at once no streaming
async def get_chat_response(request: ChatRequest):
    try:
        response_text = ""
        async for chunk in stream_chat(request.user_text, request.session_id, request.chat):
            response_text += chunk
        return response_text
    except Exception as e:
        log.error(f"Get chat response error: {e}")
        return f"Error: {str(e)}"

@app.get("/sessions")                                     #list alll sessions
async def get_sessions():
    """Get all chat sessions"""
    try:
        sessions = openai_session_service.get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        log.error(f"Error getting sessions: {e}")
        return {"sessions": [], "error": str(e)}

@app.post("/sessions/new")                              #create new sessions
async def create_session(request: SessionRequest):
    """Create a new chat session"""
    try:
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        openai_session_service.create_session(session_id)
        return {"session_id": session_id, "message": "Session created successfully"}
    except Exception as e:
        log.error(f"Error creating session: {e}")
        return {"error": str(e)}

@app.get("/sessions/{session_id}/messages")                                 #get chat history
async def get_session_messages(session_id: str):
    """Get all messages for a specific session"""
    try:
        messages = openai_session_service.get_chat_history(session_id)
        return {"messages": messages}
    except Exception as e:
        log.error(f"Error getting session messages: {e}")
        return {"messages": [], "error": str(e)}

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    try:
        openai_session_service.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        log.error(f"Error deleting session: {e}")
        return {"error": str(e)}

