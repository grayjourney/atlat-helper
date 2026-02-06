from typing import Any
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.llm.factory import LLMFactory
from src.mcp.jira_client import JiraClient


async def ticket_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """Handle Jira ticket operations."""
    configurable = config.get("configurable", {})
    llm = LLMFactory.from_config(configurable)
    
    jira_config = configurable.get("jira", {})
    if not jira_config:
        return {"messages": [AIMessage(content="Jira configuration not provided.")]}
    
    async with JiraClient(
        base_url=jira_config.get("base_url"),
        email=jira_config.get("email"),
        api_token=jira_config.get("api_token"),
    ) as client:
        last_message = state["messages"][-1].content
        
        prompt = f"""Analyze this ticket request and extract the ticket ID if present.
User message: {last_message}
Respond with only the ticket ID (e.g., PROJ-123) or 'NONE' if not found."""
        
        ticket_id_response = await llm.ainvoke(prompt)
        ticket_id = ticket_id_response.content.strip()
        
        if ticket_id == "NONE":
            return {"messages": [AIMessage(content="Please provide a ticket ID.")]}
        
        ticket = await client.get_ticket_typed(ticket_id)
        
        response = f"""**{ticket.key}**: {ticket.summary}
**Status**: {ticket.status}
**Assignee**: {ticket.assignee or 'Unassigned'}
**Priority**: {ticket.priority or 'None'}"""
        
        return {
            "messages": [AIMessage(content=response)],
            "context": {"ticket": ticket.model_dump()},
        }
