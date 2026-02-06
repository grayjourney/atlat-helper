import base64
from typing import Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from src.mcp.base_client import BaseMCPClient


class TicketSummary(BaseModel):
    """Lightweight view of a Jira ticket."""
    model_config = ConfigDict(extra="ignore")
    
    key: str
    summary: str
    status: str
    assignee: str | None = None
    priority: str | None = None
    
    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "TicketSummary":
        fields = raw.get("fields", {})
        return cls(
            key=raw.get("key", ""),
            summary=fields.get("summary", ""),
            status=fields.get("status", {}).get("name", "Unknown") if fields.get("status") else "Unknown",
            assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            priority=fields.get("priority", {}).get("name") if fields.get("priority") else None,
        )


class TicketSchema(BaseModel):
    """Full Jira ticket with commonly used fields."""
    model_config = ConfigDict(extra="ignore")
    
    key: str
    summary: str
    description: str | None = None
    status: str
    status_category: str | None = None
    assignee: str | None = None
    reporter: str | None = None
    priority: str | None = None
    labels: list[str] = []
    created: datetime | None = None
    updated: datetime | None = None
    
    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "TicketSchema":
        fields = raw.get("fields", {})
        status_obj = fields.get("status", {})
        return cls(
            key=raw.get("key", ""),
            summary=fields.get("summary", ""),
            description=fields.get("description"),
            status=status_obj.get("name", "Unknown") if status_obj else "Unknown",
            status_category=status_obj.get("statusCategory", {}).get("key") if status_obj else None,
            assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            reporter=fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
            priority=fields.get("priority", {}).get("name") if fields.get("priority") else None,
            labels=fields.get("labels", []),
            created=fields.get("created"),
            updated=fields.get("updated"),
        )


class JiraClient(BaseMCPClient):
    """Jira Cloud REST API v3 client."""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        auth_string = f"{email}:{api_token}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        auth_headers = {"Authorization": f"Basic {auth_bytes}"}
        super().__init__(base_url, auth_headers=auth_headers)
    
    async def get_ticket(self, ticket_id: str, expand: str | None = None) -> dict[str, Any]:
        """Fetch a Jira ticket by ID (raw response)."""
        params = {"expand": expand} if expand else None
        return await self._get(f"/rest/api/3/issue/{ticket_id}", params=params)
    
    async def get_ticket_typed(self, ticket_id: str) -> TicketSchema:
        """Fetch a Jira ticket by ID (typed model)."""
        raw = await self.get_ticket(ticket_id)
        return TicketSchema.from_raw(raw)
    
    async def get_ticket_summary(self, ticket_id: str) -> TicketSummary:
        """Fetch a ticket and return a lightweight summary."""
        raw = await self.get_ticket(ticket_id)
        return TicketSummary.from_raw(raw)
    
    async def update_ticket(self, ticket_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update a Jira ticket's fields."""
        return await self._put(f"/rest/api/3/issue/{ticket_id}", data={"fields": fields})
    
    async def list_tickets(
        self,
        project: str,
        status: str | None = None,
        limit: int = 50,
        order_by: str = "updated DESC",
    ) -> list[dict[str, Any]]:
        """Search for tickets using JQL (raw response)."""
        jql = f"project = {project}"
        if status:
            jql += f' AND status = "{status}"'
        jql += f" ORDER BY {order_by}"
        
        response = await self._get(
            "/rest/api/3/search",
            params={"jql": jql, "maxResults": limit}
        )
        return response.get("issues", [])
    
    async def list_tickets_typed(
        self,
        project: str,
        status: str | None = None,
        limit: int = 50,
        order_by: str = "updated DESC",
    ) -> list[TicketSchema]:
        """Search for tickets using JQL (typed models)."""
        raw_tickets = await self.list_tickets(project, status, limit, order_by)
        return [TicketSchema.from_raw(t) for t in raw_tickets]
