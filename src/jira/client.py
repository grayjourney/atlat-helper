import os
import httpx
from typing import Any, Optional, Callable

class JiraClient:
    def __init__(self, token: str, refresh_token: str = None, cloud_id: str = None, on_refresh: Callable[[dict], None] = None):
        self.token = token
        self.refresh_token = refresh_token
        self.cloud_id = cloud_id  # Pre-selected cloud_id
        self.on_refresh = on_refresh
        self.http = httpx.AsyncClient(
            base_url="https://api.atlassian.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        )

    async def _refresh_access_token(self):
        """
        Calls Auth Proxy to refresh token. Updates self.token.
        CRITICAL: Must call Proxy because we don't have client_secret.
        """
        proxy_url = os.environ.get("AUTH_PROXY_URL")
        if not proxy_url:
            raise ValueError("AUTH_PROXY_URL environment variable not set")
            
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{proxy_url}/refresh", json={"refresh_token": self.refresh_token})
            resp.raise_for_status()
            data = resp.json()
            self.token = data["access_token"]
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            
            # Notify callback to save token
            if self.on_refresh:
                self.on_refresh(data)

            # Update headers
            self.http.headers["Authorization"] = f"Bearer {self.token}"

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Wrapper around http.request with 401 retry logic."""
        response = await self.http.request(method, url, **kwargs)
        if response.status_code == 401 and self.refresh_token:
            await self._refresh_access_token()
            # Retry
            return await self.http.request(method, url, **kwargs)
        return response

    async def get_accessible_resources(self) -> list[dict]:
        """Returns list of accessible resources (Cloud IDs)."""
        resp = await self._request("GET", "https://api.atlassian.com/oauth/token/accessible-resources")
        resp.raise_for_status()
        return resp.json()

    async def search_issues(self, jql: str, fields: list[str] = None) -> list[dict]:
        """Executes JQL search. Requires self.cloud_id to be set."""
        if not self.cloud_id:
            raise ValueError("Cloud ID not selected")
        
        path = f"/ex/jira/{self.cloud_id}/rest/api/3/search"
        params = {"jql": jql}
        if fields:
            params["fields"] = ",".join(fields)
            
        resp = await self._request("GET", path, params=params)
        resp.raise_for_status()
        return resp.json().get("issues", [])

    async def close(self):
        await self.http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
