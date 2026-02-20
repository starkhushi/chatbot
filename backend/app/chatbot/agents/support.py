from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage
from app.utils.config import OPENAI_API_KEY, CHAT_MODEL
from app.chatbot.prompts import SUPPORT_PROMPT
from app.chatbot.tools import SUPPORT_TOOLS
from app.chatbot.state import GraphState
from app.utils.custom_logging import custom_logger

log = custom_logger()

def get_llm():
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("No API key found. Set OPENAI_API_KEY in .env")
        return ChatOpenAI(api_key=OPENAI_API_KEY, model=CHAT_MODEL, temperature=0).bind_tools(SUPPORT_TOOLS)
    except Exception as e:
        log.error(f"Error creating LLM: {e}")
        raise

async def support_agent(state: GraphState):
    try:
        llm = get_llm()
        messages = state["messages"]
        
        response = await llm.ainvoke([SystemMessage(content=SUPPORT_PROMPT)] + messages[-5:])
        
        tool_messages = []
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_result = SUPPORT_TOOLS[0].invoke(tool_call["args"])
                tool_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
            
            final_response = await llm.ainvoke(messages + [response] + tool_messages)
            return {"messages": [final_response], "next": "end"}
        
        return {"messages": [response], "next": "end"}
    except Exception as e:
        log.error(f"Support agent error: {e}")
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content="Error processing support query.")], "next": "end"}

