"""
Main FastAPI application.

Default: LangGraph pipeline (original behavior unchanged).
Optional (parallel): OpenAI Assistant pipeline, enabled via env/flag or dedicated endpoints.
Docker files and LangGraph logic remain untouched.
"""
import os
from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from dotenv import load_dotenv

from app.utils.custom_logging import custom_logger
from app.chatbot.graph import graph
from app.chatbot.state import GraphState
from app.services.mongodb_service import mongodb_service

# OpenAI Assistant (optional, parallel)
from app.services.openai_assistant_service import openai_assistant_service
from app.services.on_demand_tools import (
    search_accounting as assistant_search_accounting,
    search_support as assistant_search_support,
)
from app.services.thread_manager import thread_manager

load_dotenv(".env")
log = custom_logger()
app = FastAPI()

# Env flags for assistant usage
ASSISTANT_ENABLED = os.getenv("ENABLE_ASSISTANT", "false").lower() == "true"
ASSISTANT_DEFAULT = os.getenv("USE_ASSISTANT_DEFAULT", "false").lower() == "true"

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    user_text: str
    chat: Optional[List[Dict]] = None
    session_id: str = "default"


class SaveChatRequest(BaseModel):
    session_id: str
    messages: List[Dict]


def dict_to_messages(chat_history: List[Dict]) -> List[BaseMessage]:
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


def messages_to_dict(messages: List[BaseMessage]) -> List[Dict]:
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
    arch = "assistant" if ASSISTANT_ENABLED and ASSISTANT_DEFAULT else "langgraph"
    return {"status": "ok", "default_architecture": arch}


# --- LangGraph (original) ---
async def stream_chat_langgraph(
    user_text: str, session_id: str = "default", chat_history: Optional[List[Dict]] = None
):
    try:
        if not chat_history:
            chat_history = mongodb_service.get_chat_history(session_id)

        messages = dict_to_messages(chat_history)
        messages.append(HumanMessage(content=user_text))

        state: GraphState = {"messages": messages, "next": "supervisor"}

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
            for char in final_response:
                yield char
            updated_messages = messages + [AIMessage(content=final_response)]
            mongodb_service.save_chat(session_id, messages_to_dict(updated_messages))
        else:
            yield "No response generated."
    except Exception as e:
        log.error(f"Stream chat error: {e}")
        yield f"Error: {str(e)}"


# --- OpenAI Assistant (parallel/optional) ---
async def stream_chat_assistant(user_text: str, session_id: str = "default"):
    if not (ASSISTANT_ENABLED and openai_assistant_service):
        yield "Assistant mode disabled or not configured. Set ENABLE_ASSISTANT=true and OPENAI_API_KEY."
        return

    try:
        thread_id = await openai_assistant_service.get_or_create_thread(session_id)
        await openai_assistant_service.add_message(thread_id, user_text, role="user")

        tool_functions = {
            "search_accounting": assistant_search_accounting,
            "search_support": assistant_search_support,
        }

        async for chunk in openai_assistant_service.run_stream(thread_id, tool_functions):
            yield chunk
    except Exception as e:
        log.error(f"Assistant stream chat error: {e}")
        yield f"Error: {str(e)}"


# --- Routes (LangGraph default, Assistant opt-in) ---
@app.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        if ASSISTANT_ENABLED and ASSISTANT_DEFAULT:
            async for chunk in stream_chat_assistant(request.user_text, request.session_id):
                yield chunk
        else:
            async for chunk in stream_chat_langgraph(request.user_text, request.session_id, request.chat):
                yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")


@app.post("/get-chat-response")
async def get_chat_response(request: ChatRequest):
    try:
        response_text = ""
        if ASSISTANT_ENABLED and ASSISTANT_DEFAULT:
            async for chunk in stream_chat_assistant(request.user_text, request.session_id):
                response_text += chunk
        else:
            async for chunk in stream_chat_langgraph(request.user_text, request.session_id, request.chat):
                response_text += chunk
        return {"response": response_text, "session_id": request.session_id}
    except Exception as e:
        log.error(f"Get chat response error: {e}")
        return {"error": str(e), "session_id": request.session_id}


@app.post("/assistant/chat-stream")
async def assistant_chat_stream(request: ChatRequest):
    async def event_generator():
        async for chunk in stream_chat_assistant(request.user_text, request.session_id):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")


@app.post("/assistant/get-chat-response")
async def assistant_get_chat_response(request: ChatRequest):
    try:
        response_text = ""
        async for chunk in stream_chat_assistant(request.user_text, request.session_id):
            response_text += chunk
        return {"response": response_text, "session_id": request.session_id}
    except Exception as e:
        log.error(f"Assistant get chat response error: {e}")
        return {"error": str(e), "session_id": request.session_id}


@app.post("/save-chat")
async def save_chat(request: SaveChatRequest):
    """
    Save chat history to MongoDB with session_id (LangGraph path)
    """
    try:
        mongodb_service.save_chat(request.session_id, request.messages)
        log.info(f"Chat history saved for session_id: {request.session_id}")
        return {
            "status": "success",
            "message": f"Chat history saved for session_id: {request.session_id}",
            "session_id": request.session_id,
            "message_count": len(request.messages),
        }
    except Exception as e:
        log.error(f"Error saving chat history: {e}")
        return {"status": "error", "message": f"Error saving chat history: {str(e)}"}


@app.get("/get-chat-history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get chat history from MongoDB by session_id (LangGraph path)
    """
    try:
        chat_history = mongodb_service.get_chat_history(session_id)
        log.info(
            f"Retrieved chat history for session_id: {session_id}, messages: {len(chat_history)}"
        )
        return {
            "status": "success",
            "session_id": session_id,
            "messages": chat_history,
            "message_count": len(chat_history),
        }
    except Exception as e:
        log.error(f"Error getting chat history: {e}")
        return {
            "status": "error",
            "message": f"Error getting chat history: {str(e)}",
            "session_id": session_id,
            "messages": [],
        }


@app.get("/assistant/get-chat-history/{session_id}")
async def assistant_get_chat_history(session_id: str):
    """
    Get chat history from OpenAI thread (Assistant path)
    """
    try:
        if not (ASSISTANT_ENABLED and openai_assistant_service):
            return {
                "status": "error",
                "message": "Assistant mode disabled or not configured. Set ENABLE_ASSISTANT=true and OPENAI_API_KEY.",
                "session_id": session_id,
                "messages": [],
            }

        thread_id = thread_manager.get_thread_id(session_id)
        if not thread_id:
            return {
                "status": "success",
                "session_id": session_id,
                "messages": [],
                "message_count": 0,
                "note": "No conversation history found for this session",
            }

        messages = await openai_assistant_service.get_thread_messages(thread_id)
        log.info(
            f"Retrieved assistant chat history for session_id: {session_id}, messages: {len(messages)}"
        )
        return {
            "status": "success",
            "session_id": session_id,
            "thread_id": thread_id,
            "messages": messages,
            "message_count": len(messages),
        }
    except Exception as e:
        log.error(f"Error getting assistant chat history: {e}")
        return {
            "status": "error",
            "message": f"Error getting chat history: {str(e)}",
            "session_id": session_id,
            "messages": [],
        }


@app.get("/list-all-sessions")
async def list_all_sessions():
    """
    List all chat sessions with their session_id, message_count, and updated_at (LangGraph path)
    """
    try:
        sessions = mongodb_service.get_all_sessions()
        log.info(f"Retrieved {len(sessions)} sessions")
        return {"status": "success", "sessions": sessions, "total_sessions": len(sessions)}
    except Exception as e:
        log.error(f"Error listing sessions: {e}")
        return {
            "status": "error",
            "message": f"Error listing sessions: {str(e)}",
            "sessions": [],
            "total_sessions": 0,
        }


@app.get("/assistant/list-all-sessions")
async def assistant_list_all_sessions():
    """
    List all sessions (Assistant path) - currently provides guidance
    """
    try:
        return {
            "status": "success",
            "message": "Assistant sessions are stored in OpenAI threads via thread_manager. Use /assistant/get-chat-history/{session_id}.",
        }
    except Exception as e:
        log.error(f"Error listing assistant sessions: {e}")
        return {"status": "error", "message": f"Error listing sessions: {str(e)}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
