from typing import Any
from langchain_core.messages import AIMessage

from src.agents.state import AgentState


async def confluence_node(state: AgentState) -> dict[str, Any]:
    """Handle Confluence documentation operations (placeholder)."""
    return {"messages": [AIMessage(content="Confluence integration coming soon.")]}
