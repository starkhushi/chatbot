from typing import Literal
from langgraph.graph import StateGraph, END
from app.chatbot.state import GraphState
from app.chatbot.agents.supervisor import supervisor_agent
from app.chatbot.agents.accounting import accounting_agent
from app.chatbot.agents.support import support_agent

def should_continue(state: GraphState) -> Literal["accounting", "support", END]:
    next_step = state.get("next", "end")
    if next_step == "end" or next_step == END:
        return END
    return next_step       # Conditional edge function that determines next node

def create_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("accounting", accounting_agent)
    workflow.add_node("support", support_agent)
    
    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges("supervisor", should_continue)
    workflow.add_edge("accounting", END)
    workflow.add_edge("support", END)
    
    return workflow.compile()

graph = create_graph()

