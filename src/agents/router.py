from typing import Any, Literal
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.llm.factory import LLMFactory


class IntentClassification(BaseModel):
    """Structured output schema for intent classification."""
    intent: Literal["ticket", "confluence", "board", "general_chat"]


async def classify_intent(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """Classify user intent from the latest message."""
    # check for awaiting input
    if state.get("awaiting_input"):
        if state["awaiting_input"] == "cloud_id_selection":
            return {"intent": "ticket"}

    last_message = state["messages"][-1].content
    
    configurable = config.get("configurable", {})
    llm = LLMFactory.from_config(configurable)
    llm_with_schema = llm.with_structured_output(IntentClassification)
    
    prompt = f"""Classify the user's intent into one of:
- ticket: Jira/Trello ticket operations
- confluence: Documentation/wiki search
- board: Sprint/board operations
- general_chat: General conversation

User message: {last_message}"""
    
    result = await llm_with_schema.ainvoke(prompt)
    return {"intent": result.intent}


def route_by_intent(state: AgentState) -> str:
    """Route to appropriate subgraph based on classified intent."""
    intent_to_node = {
        "ticket": "ticket_subgraph",
        "confluence": "confluence_subgraph",
        "board": "board_subgraph",
        "general_chat": "general_chat_node",
    }
    return intent_to_node.get(state["intent"], "general_chat_node")
