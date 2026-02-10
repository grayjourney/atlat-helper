from typing import TypedDict, Literal, Annotated
from operator import add
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """
    Shared state passed between all nodes in the graph.
    """
    intent: Literal["ticket", "confluence", "board", "general_chat"] | None
    current_agent: str | None
    context: dict
    # Persistence for multi-turn flows (e.g., site selection)
    awaiting_input: str | None  # e.g., "cloud_id_selection"
    available_sites: list[dict] | None  # Cache sites during selection
