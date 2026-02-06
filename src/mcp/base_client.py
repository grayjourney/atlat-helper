import logging
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Any


class BaseMCPClient(ABC):
    """Abstract base class for MCP clients (Jira, Trello, Confluence)."""
    
    def __init__(self, base_url: str, auth_headers: dict[str, str] | None = None):
        self.base_url = base_url
        self._auth_headers = auth_headers or {}
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> "BaseMCPClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._auth_headers,
            timeout=httpx.Timeout(30.0)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
    
    async def _get(self, path: str, params: dict | None = None) -> dict:
        logging.info(f"GET {path} with params {params}")
        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource {path} not found")
            elif e.response.status_code == 401:
                raise AuthenticationError(f"Invalid credentials for {path}")
            elif e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {path}")
            else:
                raise MCPError(f"Error {e.response.status_code} for {path}")
    
    async def _post(self, path: str, data: dict) -> dict:
        logging.info(f"POST {path} with data {data}")
        try:
            response = await self._client.post(path, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource {path} not found")
            elif e.response.status_code == 401:
                raise AuthenticationError(f"Invalid credentials for {path}")
            elif e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {path}")
            else:
                raise MCPError(f"Error {e.response.status_code} for {path}")
    
    async def _put(self, path: str, data: dict) -> dict:    
        logging.info(f"PUT {path} with data {data}")
        try:
            response = await self._client.put(path, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource {path} not found")
            elif e.response.status_code == 401:
                raise AuthenticationError(f"Invalid credentials for {path}")
            elif e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {path}")
            else:
                raise MCPError(f"Error {e.response.status_code} for {path}")
    
    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        """Fetch a ticket by ID. Subclasses MUST implement."""
        ...
    
    @abstractmethod
    async def update_ticket(self, ticket_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """Update a ticket's fields. Subclasses MUST implement."""
        ...
    
    @abstractmethod
    async def list_tickets(self, project: str, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """List tickets in a project. Subclasses MUST implement."""
        ...


class MCPError(Exception):
    """Base exception for MCP client errors."""
    pass


class NotFoundError(MCPError):
    """Resource not found (404)."""
    pass


class AuthenticationError(MCPError):
    """Invalid credentials (401)."""
    pass


class RateLimitError(MCPError):
    """Rate limited (429)."""
    pass
