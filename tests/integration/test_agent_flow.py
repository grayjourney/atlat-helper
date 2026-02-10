import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from src.agents.subgraphs.ticket import ticket_node
from src.agents.state import AgentState
from tests.mocks.mock_mcp_factory import MockMCPFactory
from tests.mocks.mock_llm import MockLLM

@pytest.mark.asyncio
async def test_ticket_node_flow_with_mocks():
    """
    Test the ticket_node integrated flow:
    1. User asks for ticket status
    2. Node uses MockMCPFactory to get fake tools
    3. Node uses MockLLM to decide on tool call
    4. Node executes tool (MockJiraTools)
    5. Node returns final answer
    """
    
    # Setup State
    state: AgentState = {
        "messages": [HumanMessage(content="What is the status of TEST-1?")],
        "user_message": "What is the status of TEST-1?",
        "ticket_id": None,
        "ticket_data": None,
        "analysis": None,
        "proposal": None,
        "intent": "ticket_management" # Router would set this
    }
    
    config = RunnableConfig(configurable={"model_provider": "mock"}) # Provider doesn't matter since we patch factory

    # Mock TokenStorage to return a valid-looking token
    mock_token = MagicMock()
    mock_token.is_expired = False
    mock_token.access_token = "fake-token"

    # Patch Dependencies
    with patch("src.agents.subgraphs.ticket.TokenStorage.get_token", return_value=mock_token), \
         patch("src.agents.subgraphs.ticket.AtlassianMCPFactory", MockMCPFactory), \
         patch("src.agents.subgraphs.ticket.LLMFactory.from_config", return_value=MockLLM()):
         
        # Execute Node
        result = await ticket_node(state, config)
        
        # Assertions
        messages = result["messages"]
        
        # We expect:
        # 1. AIMessage with tool_calls (from MockLLM)
        # 2. ToolMessage with result (from ticket_node executing tool)
        # 3. AIMessage final answer (from MockLLM)
        
        # The node returns [response] + [tool_results] + [final_response] + original messages?
        # ticket_node returns {"messages": [response] ... }
        # Let's inspect the returned messages list
        
        assert len(messages) >= 3
        
        # 1. Tool Call Message
        tool_call_msg = messages[0]
        assert isinstance(tool_call_msg, AIMessage)
        assert len(tool_call_msg.tool_calls) > 0
        assert tool_call_msg.tool_calls[0]["name"] == "read_issue"
        assert tool_call_msg.tool_calls[0]["args"]["issue_key"] == "TEST-1"
        
        # 2. Tool Output Message
        tool_output_msg = messages[1]
        assert isinstance(tool_output_msg, ToolMessage)
        assert "In Progress" in tool_output_msg.content
        assert "Test Ticket" in tool_output_msg.content
        
        # 3. Final Answer
        final_msg = messages[2]
        assert isinstance(final_msg, AIMessage)
        assert "In Progress" in final_msg.content

@pytest.mark.asyncio
async def test_ticket_node_confluence_search():
    """Test Confluence search flow via ticket_node (if available) or generic reasoning."""
    # Note: ticket_node currently only gets Jira/Confluence tools from factory.
    # If LLM decides to search docs, it should work too.
    
    state: AgentState = {
        "messages": [HumanMessage(content="Search docs for auth")],
        "user_message": "Search docs for auth",
        "ticket_id": None,
        "ticket_data": None,
        "analysis": None,
        "proposal": None,
        "intent": "confluence_search"
    }
    
    config = RunnableConfig(configurable={"model_provider": "mock"})
    
    mock_token = MagicMock()
    mock_token.is_expired = False
    mock_token.access_token = "fake-token"

    with patch("src.agents.subgraphs.ticket.TokenStorage.get_token", return_value=mock_token), \
         patch("src.agents.subgraphs.ticket.AtlassianMCPFactory", MockMCPFactory), \
         patch("src.agents.subgraphs.ticket.LLMFactory.from_config", return_value=MockLLM()):
         
        result = await ticket_node(state, config)
        messages = result["messages"]
        
        # Assertions
        assert len(messages) >= 2
        tool_call_msg = messages[0]
        assert tool_call_msg.tool_calls[0]["name"] == "search_confluence"
        
        tool_output_msg = messages[1]
        assert "Authentication Guide" in tool_output_msg.content
