from typing import Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.llm.factory import LLMFactory


async def general_chat_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """Handle general conversational queries."""
    configurable = config.get("configurable", {})
    llm = LLMFactory.from_config(configurable)
    
    response = await llm.ainvoke(state["messages"])
    
    return {"messages": [response]}
