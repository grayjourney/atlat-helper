import os
import base64
from typing import Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.mcp.token_storage import TokenStorage


class AtlassianMCPFactory:
    """Factory for creating Atlassian MCP tool connections."""
    
    ATLASSIAN_MCP_URL = "https://mcp.atlassian.com/v1/mcp"
    
    @classmethod
    async def create_client(cls, oauth_token: str | None = None) -> MultiServerMCPClient:
        """Create a MultiServerMCPClient for Atlassian services."""
        
        # 1. Check if token passed explicitly
        if oauth_token:
            pass # Use provided token
            
        # 2. Check TokenStorage (OAuth Flow)
        else:
            stored_token = TokenStorage.get_token()
            if stored_token and not stored_token.is_expired:
                oauth_token = stored_token.access_token
                
        # 3. Fallback to Basic Auth (Env Vars)
        if not oauth_token:
            email = os.getenv("ATLASSIAN_EMAIL")
            api_token = os.getenv("ATLASSIAN_API_TOKEN")
            if email and api_token:
                creds = f"{email}:{api_token}"
                b64_creds = base64.b64encode(creds.encode()).decode()
                oauth_token = f"Basic {b64_creds}"

        config = {
            "atlassian": {
                "transport": "sse",
                "url": cls.ATLASSIAN_MCP_URL,
            }
        }
        
        if oauth_token:
            # If token starts with "Basic ", use as is. Otherwise assume Bearer.
            if oauth_token.startswith("Basic "):
                auth_header = oauth_token
            else:
                auth_header = f"Bearer {oauth_token}"
                
            config["atlassian"]["headers"] = {
                "Authorization": auth_header
            }
        
        return MultiServerMCPClient(config)
    
    @classmethod
    async def get_tools(cls, oauth_token: str | None = None) -> list[Any]:
        """Get all Atlassian MCP tools."""
        # Use simple variable for context manager if needed, but MultiServerMCPClient 
        # usually needs to remain open or be used as context manager.
        # However, get_tools() in langchain-mcp-adapters might not need context?
        # Let's check the usage in previous code.
        # Actually MultiServerMCPClient is an async context manager.
        
        async with await cls.create_client(oauth_token) as client:
            return await client.get_tools()
