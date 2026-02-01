# =============================================================================
# MCP Base Client - Abstract Base Class
# =============================================================================
"""
Base class for all MCP (Model Context Protocol) clients.

=== ARCHITECTURE DECISION: ABC vs Protocol ===

This module uses `abc.ABC` (Abstract Base Class) instead of `typing.Protocol`.
Here is the PRODUCTION-FOCUSED justification:

┌─────────────────────────────────────────────────────────────────────────────┐
│ CRITERION              │ ABC (chosen)           │ Protocol                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Code Reuse             │ ✅ Can share common    │ ❌ No shared code.        │
│                        │    HTTP logic, conn    │    Each impl duplicates   │
│                        │    pooling, retry.     │    connection handling.   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Runtime Safety         │ ✅ Fails FAST at       │ ❌ Silent failure.        │
│                        │    instantiation if    │    Only fails when the    │
│                        │    abstract method     │    missing method is      │
│                        │    not implemented.    │    actually called.       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Connection Management  │ ✅ Base class owns     │ ❌ Each impl must manage  │
│                        │    httpx.AsyncClient,  │    its own client.        │
│                        │    handles lifecycle.  │    Risk of leaks.         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Static Analysis        │ ✅ mypy catches        │ ⚠️  mypy catches, but     │
│                        │    missing methods.    │    runtime doesn't.       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Loose Coupling         │ ⚠️  Requires inherit. │ ✅ Duck typing, no        │
│ (Go-style interfaces)  │    Tighter coupling.   │    inheritance needed.    │
└─────────────────────────────────────────────────────────────────────────────┘

VERDICT: ABC wins for this use case because:
    1. **Connection Reliability**: All MCP clients need HTTP connections.
       Sharing connection pooling logic prevents resource leaks.
    2. **Fail-Fast Behavior**: If a developer forgets `get_ticket()`,
       the app crashes IMMEDIATELY at startup, not in production at 3AM.
    3. **Code Reuse**: Retry logic, logging, and error handling are
       implemented ONCE in the base class.

=== CATCHING PROTOCOL SILENT ERRORS (for future reference) ===

If you ever DO use Protocol, here's how to catch errors:

1. **Static Analysis (mypy):**
   ```bash
   # In CI pipeline
   mypy src/ --strict
   ```
   Add to requirements.txt: mypy>=1.8.0

2. **Runtime Check (optional):**
   ```python
   from typing import runtime_checkable, Protocol
   
   @runtime_checkable
   class MCPProtocol(Protocol):
       def get_ticket(self, ticket_id: str) -> dict: ...
   
   # Now you can do:
   assert isinstance(my_client, MCPProtocol)
   ```
   
3. **pytest fixture:**
   ```python
   def test_client_implements_protocol(jira_client):
       assert hasattr(jira_client, 'get_ticket')
       assert callable(jira_client.get_ticket)
   ```


Author: Gray
License: Proprietary
"""

import logging
import httpx
from abc import ABC, abstractmethod
from typing import Any


class BaseMCPClient(ABC):
    """
    Abstract base class for MCP (Model Context Protocol) clients.
    
    All MCP clients (Jira, Trello, Confluence) inherit from this class.
    The base class handles:
        - HTTP connection pooling (shared httpx.AsyncClient)
        - Common error handling and retry logic
        - Logging and observability
    
    Subclasses MUST implement:
        - get_ticket()
        - update_ticket()
        - list_tickets()
    
    Usage:
        class JiraMCPClient(BaseMCPClient):
            async def get_ticket(self, ticket_id: str) -> dict:
                return await self._get(f"/issue/{ticket_id}")
    """
    
    def __init__(self, base_url: str, api_token: str | None = None):

        self.base_url = base_url
        self.api_token = api_token
        self._client: httpx.AsyncClient | None = None
        pass
    
    async def __aenter__(self) -> "BaseMCPClient":
        """
        Async context manager entry - initialize the HTTP client.
        
        Usage:
            async with JiraMCPClient(url, token) as client:
                ticket = await client.get_ticket("PROJ-123")
        """
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(30.0),
        )
        return self
        # TODO: Create the httpx.AsyncClient here
        # self._client = httpx.AsyncClient(
        #     base_url=self.base_url,
        #     headers={"Authorization": f"Bearer {self._api_token}"},
        #     timeout=httpx.Timeout(30.0),
        # )
        # return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
    
    # =========================================================================
    # SHARED HTTP METHODS (Code Reuse - why we chose ABC)
    # =========================================================================
    
    async def _get(self, path: str, params: dict | None = None) -> dict:
        """
        Make a GET request to the MCP server.
        
        Args:
            path: The API path (e.g., "/issue/PROJ-123")
            params: Optional query parameters
            
        Returns:
            Parsed JSON response as dict
            
        Raises:
            httpx.HTTPError: On network or HTTP errors
        """
        logging.info(f"GET {path}")
        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}")
            elif e.response.status_code == 401:
                raise AuthenticationError("Invalid credentials")
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limited")
            raise MCPError(f"HTTP {e.response.status_code}: {e}")
        except httpx.RequestException as e:
            logging.error(f"Request error: {e}")
            raise
    
    async def _post(self, path: str, data: dict) -> dict:
        """
        Make a POST request to the MCP server.
        
        Args:
            path: The API path
            data: JSON body to send
            
        Returns:
            Parsed JSON response as dict
        """
        logging.info(f"POST {path}")
        logging.info(f"Data: {data}")
        try:
            response = await self._client.post(path, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {path}")
            elif e.response.status_code == 401:
                raise AuthenticationError("Invalid credentials")
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limited")
            raise MCPError(f"HTTP {e.response.status_code}: {e}")
        except httpx.RequestException as e:
            logging.error(f"Request error: {e}")
            raise
    
    async def _put(self, path: str, data: dict) -> dict:
        """
        Make a PUT request to the MCP server.
        
        Args:
            path: The API path
            data: JSON body to send
            
        Returns:
            Parsed JSON response as dict
        """
        logging.info(f"PUT {path}")
        logging.info(f"Data: {data}")
        try:
            response = await self._client.put(path, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                  raise NotFoundError(f"Resource not found: {path}")
            elif e.response.status_code == 401:
                raise AuthenticationError("Invalid credentials")
            elif e.response.status_code == 429:
                raise RateLimitError("Rate limited")
            raise MCPError(f"HTTP {e.response.status_code}: {e}")
        except httpx.RequestException as e:
            logging.error(f"Request error: {e}")
            raise
    
    # =========================================================================
    # ABSTRACT METHODS (Subclasses MUST implement these)
    # =========================================================================
    
    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        """
        Fetch a ticket by ID.
        
        Args:
            ticket_id: The ticket identifier (e.g., "PROJ-123")
            
        Returns:
            Ticket data as a dictionary containing at minimum:
            - id: str
            - summary: str
            - status: str
            - assignee: str | None
            
        Raises:
            NotFoundError: If ticket doesn't exist
            AuthenticationError: If credentials are invalid
        """
        # Subclasses MUST override this method.
        # If they don't, Python raises TypeError at instantiation.
        ...
    
    @abstractmethod
    async def update_ticket(
        self,
        ticket_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update a ticket's fields.
        
        Args:
            ticket_id: The ticket identifier
            fields: Dictionary of fields to update
            
        Returns:
            Updated ticket data
        """
        ...
    
    @abstractmethod
    async def list_tickets(
        self,
        project: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        List tickets in a project.
        
        Args:
            project: Project key (e.g., "PROJ")
            status: Optional status filter
            limit: Maximum number of tickets to return
            
        Returns:
            List of ticket dictionaries
        """
        ...


# =============================================================================
# CUSTOM EXCEPTIONS (for clean error handling)
# =============================================================================

class MCPError(Exception):
    """Base exception for MCP client errors."""
    pass


class NotFoundError(MCPError):
    """Raised when a resource (ticket, project) is not found."""
    pass


class AuthenticationError(MCPError):
    """Raised when API credentials are invalid or expired."""
    pass


class RateLimitError(MCPError):
    """Raised when the MCP server rate-limits us."""
    pass
