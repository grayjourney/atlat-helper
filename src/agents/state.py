from typing import TypedDict, Literal, Annotated
from operator import add
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """
    Shared state passed between all nodes in the graph.
    
    Extends MessagesState (which provides 'messages' list).
    
    Hints:
        # intent: Classified by router, used by supervisor for routing
        # current_agent: Tracks which subgraph is active (for debugging)
        # context: Shared data between nodes (e.g., fetched ticket data)
    """
    intent: Literal["ticket", "confluence", "board", "general_chat"] | None
    current_agent: str | None
    context: dict
