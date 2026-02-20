from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from app.utils.config import OPENAI_API_KEY, CHAT_MODEL
from app.chatbot.prompts import SUPERVISOR_PROMPT
from app.chatbot.state import GraphState
from app.utils.custom_logging import custom_logger

log = custom_logger()

def get_llm():
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("No API key found. Set OPENAI_API_KEY in .env")
        return ChatOpenAI(api_key=OPENAI_API_KEY, model=CHAT_MODEL, temperature=0)
    except Exception as e:
        log.error(f"Error creating LLM: {e}")
        raise

async def supervisor_agent(state: GraphState):
    try:
        llm = get_llm()
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        response = await llm.ainvoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            messages[-1] if messages else SystemMessage(content=last_message)
        ])
        
        next_agent = response.content.strip().lower()
        if "accounting" in next_agent:
            return {"next": "accounting"}
        return {"next": "support"}
    except Exception as e:
        log.error(f"Supervisor error: {e}")
        return {"next": "support"}

