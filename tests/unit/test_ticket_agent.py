import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.subgraphs.ticket import ticket_node
from src.agents.state import AgentState

@pytest.mark.asyncio
async def test_auth_fail():
    with patch("src.agents.subgraphs.ticket.TokenStorage.get_token", return_value=None):
        state = {"messages": [HumanMessage("hi")], "context": {}}
        result = await ticket_node(state, {})
        assert "Atlassian not connected" in result["messages"][0].content

@pytest.mark.asyncio
async def test_cloud_id_prompt():
    # Mock Token
    token = MagicMock()
    token.access_token = "access"
    token.refresh_token = "refresh"
    token.is_expired = False
    
    # Mock Jira Client context manager
    mock_client = AsyncMock()
    mock_client.get_accessible_resources.return_value = [
        {"id": "cloud-1", "name": "Site A", "url": "url1"},
        {"id": "cloud-2", "name": "Site B", "url": "url2"}
    ]
    
    # Mock JiraClient constructor
    with patch("src.agents.subgraphs.ticket.TokenStorage.get_token", return_value=token), \
         patch("src.agents.subgraphs.ticket.JiraClient") as MockJiraClient:
        
        MockJiraClient.return_value.__aenter__.return_value = mock_client
        
        state = {"messages": [HumanMessage("show tickets")], "context": {}, "awaiting_input": None}
        result = await ticket_node(state, {})
        
        # Verify it prompts user
        assert result.get("awaiting_input") == "cloud_id_selection"
        assert len(result.get("available_sites")) == 2
        assert "Multiple Jira sites found" in result["messages"][0].content

@pytest.mark.asyncio
async def test_cloud_id_selection_success():
    # Setup State waiting for input
    sites = [
        {"id": "cloud-1", "name": "Site A", "url": "url1"},
        {"id": "cloud-2", "name": "Site B", "url": "url2"}
    ]
    state = {
        "messages": [HumanMessage("1")], # User selects 1
        "context": {},
        "awaiting_input": "cloud_id_selection",
        "available_sites": sites
    }

    with patch("src.agents.subgraphs.ticket.TokenStorage.get_token", return_value=MagicMock()):
        result = await ticket_node(state, {})
        
        # Verify Context Update
        assert result["context"]["cloud_id"] == "cloud-1"
        assert result["awaiting_input"] is None
        assert "Selected site: **Site A**" in result["messages"][0].content
