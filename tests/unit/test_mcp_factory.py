import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.mcp_factory import AtlassianMCPFactory


@pytest.mark.asyncio
async def test_create_client_without_token():
    with patch("src.mcp.mcp_factory.MultiServerMCPClient") as MockClient:
        await AtlassianMCPFactory.create_client()
        
        MockClient.assert_called_once()
        call_args = MockClient.call_args[0][0]
        assert "atlassian" in call_args
        assert call_args["atlassian"]["url"] == AtlassianMCPFactory.ATLASSIAN_MCP_URL
        assert "headers" not in call_args["atlassian"]


@pytest.mark.asyncio
async def test_create_client_with_token():
    with patch("src.mcp.mcp_factory.MultiServerMCPClient") as MockClient:
        token = "test_token"
        await AtlassianMCPFactory.create_client(token)
        
        MockClient.assert_called_once()
        call_args = MockClient.call_args[0][0]
        assert "atlassian" in call_args
        assert call_args["atlassian"]["headers"]["Authorization"] == f"Bearer {token}"


@pytest.mark.asyncio
async def test_get_tools():
    mock_client_instance = AsyncMock()
    mock_client_instance.get_tools.return_value = ["tool1", "tool2"]
    
    # Mock context manager
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    
    with patch("src.mcp.mcp_factory.AtlassianMCPFactory.create_client", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_client_instance
        
        tools = await AtlassianMCPFactory.get_tools("token")
        
        assert tools == ["tool1", "tool2"]
        mock_create.assert_called_once_with("token")
        mock_client_instance.get_tools.assert_called_once()
