from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.agents.state import AgentState
from src.agents.router import classify_intent, route_by_intent
from src.agents.subgraphs.ticket import ticket_node
from src.agents.subgraphs.general import general_chat_node
from src.agents.subgraphs.confluence import confluence_node
from src.agents.subgraphs.board import board_node


def build_supervisor_graph(checkpointer: BaseCheckpointSaver | None = None) -> StateGraph:
    """Build the main supervisor graph with conditional routing."""
    graph = StateGraph(AgentState)
    
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("ticket_subgraph", ticket_node)
    graph.add_node("general_chat_node", general_chat_node)
    graph.add_node("confluence_subgraph", confluence_node)
    graph.add_node("board_subgraph", board_node)
    
    graph.add_edge(START, "classify_intent")
    
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "ticket_subgraph": "ticket_subgraph",
            "general_chat_node": "general_chat_node",
            "confluence_subgraph": "confluence_subgraph",
            "board_subgraph": "board_subgraph",
        }
    )
    
    graph.add_edge("ticket_subgraph", END)
    graph.add_edge("general_chat_node", END)
    graph.add_edge("confluence_subgraph", END)
    graph.add_edge("board_subgraph", END)
    
    return graph.compile(checkpointer=checkpointer)
