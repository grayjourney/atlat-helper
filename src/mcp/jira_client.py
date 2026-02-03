import base64
from typing import Any

from src.mcp.base_client import BaseMCPClient


class JiraClient(BaseMCPClient):
    """Jira Cloud REST API v3 client."""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        auth_string = f"{email}:{api_token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        super().__init__(
            base_url=base_url,
            auth_headers={"Authorization": f"Basic {auth_bytes}"}
        )
    
    async def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        # Use self._get() inherited from BaseMCPClient
        # Endpoint: /rest/api/3/issue/{ticket_id}
        return await self._get(f"/rest/api/3/issue/{ticket_id}")
    
    async def update_ticket(self, ticket_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        # Use self._put() inherited from BaseMCPClient
        # Endpoint: /rest/api/3/issue/{ticket_id}
        return await self._put(f"/rest/api/3/issue/{ticket_id}", data=fields)
    
    async def list_tickets(
        self,
        project: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        # Build JQL query
        jql = f"project = {project}"
        if status:
            jql += f" AND status = \"{status}\""
        
        # Use self._get() inherited from BaseMCPClient
        # Endpoint: /rest/api/3/search?jql=...
        response = await self._get("/rest/api/3/search", params={
            "jql": jql,
            "maxResults": limit,
        })
        return response.get("issues", [])
