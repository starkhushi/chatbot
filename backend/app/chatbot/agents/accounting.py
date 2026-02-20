from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage
from app.utils.config import OPENAI_API_KEY, CHAT_MODEL
from app.chatbot.prompts import ACCOUNTING_PROMPT
from app.chatbot.tools import ACCOUNTING_TOOLS
from app.chatbot.state import GraphState
from app.utils.custom_logging import custom_logger

log = custom_logger()

def get_llm():
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("No API key found. Set OPENAI_API_KEY in .env")
        return ChatOpenAI(api_key=OPENAI_API_KEY, model=CHAT_MODEL, temperature=0).bind_tools(ACCOUNTING_TOOLS)
    except Exception as e:
        log.error(f"Error creating LLM: {e}")
        raise

async def accounting_agent(state: GraphState):
    try:
        llm = get_llm()
        messages = state["messages"]
        last_user_message = messages[-1].content if messages else ""
        
        # Get LLM response - it should call the tool
        response = await llm.ainvoke([SystemMessage(content=ACCOUNTING_PROMPT)] + messages[-5:])
        
        tool_messages = []
        if response.tool_calls:
            # Tool was called - execute all tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "search_accounting")
                tool_args = tool_call.get("args", {})
                query = tool_args.get("query", last_user_message)
                log.info(f"Tool called: {tool_name} with query: {query}")
                
                if tool_name == "search_accounting":
                    tool_result = ACCOUNTING_TOOLS[0].invoke({"query": query})
                    tool_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
            
            # Get final response with tool results
            all_messages = messages + [response] + tool_messages
            final_response = await llm.ainvoke(all_messages)
            return {"messages": [final_response], "next": "end"}
        else:
            # No tool call made - force tool usage for data queries
            # Check if this looks like a data query
            data_query_keywords = ["salary", "asset", "transaction", "employee", "debt", "profit", "loss", "name", "department", "what", "who", "show", "find", "get"]
            if any(keyword in last_user_message.lower() for keyword in data_query_keywords):
                log.info(f"Force tool usage for query: {last_user_message}")
                # Manually call the tool with the user's query
                tool_result = ACCOUNTING_TOOLS[0].invoke({"query": last_user_message})
                # Create a tool message and get response from LLM
                tool_msg = ToolMessage(content=str(tool_result), tool_call_id="manual_call")
                final_response = await llm.ainvoke(messages + [SystemMessage(content="Use the following search results to answer the user's question:\n" + str(tool_result))])
                return {"messages": [final_response], "next": "end"}
        
        return {"messages": [response], "next": "end"}
    except Exception as e:
        log.error(f"Accounting agent error: {e}")
        import traceback
        log.error(traceback.format_exc())
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content="Error processing accounting query.")], "next": "end"}
