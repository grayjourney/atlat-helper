import pytest
import respx
from httpx import Response
from src.jira.client import JiraClient
import os

@pytest.fixture
def proxy_url():
    os.environ["AUTH_PROXY_URL"] = "http://localhost:8001"
    yield "http://localhost:8001"
    del os.environ["AUTH_PROXY_URL"]

@pytest.mark.asyncio
async def test_get_accessible_resources(proxy_url):
    client = JiraClient(token="valid_token")
    
    async with respx.mock(base_url="https://api.atlassian.com") as respx_mock:
        respx_mock.get("/oauth/token/accessible-resources").mock(
            return_value=Response(200, json=[
                {"id": "cloud-1", "name": "Site A", "url": "https://site-a.atlassian.net"},
                {"id": "cloud-2", "name": "Site B", "url": "https://site-b.atlassian.net"}
            ])
        )
        
        resources = await client.get_accessible_resources()
        assert len(resources) == 2
        assert resources[0]["id"] == "cloud-1"

@pytest.mark.asyncio
async def test_refresh_token_on_401(proxy_url):
    """
    Simulates:
    1. Search -> 401 Unauthorized
    2. Client calls Proxy /refresh -> Returns new token
    3. Client Retries Search -> 200 OK
    """
    client = JiraClient(token="expired_token", refresh_token="valid_refresh", cloud_id="cloud-1")
    
    async with respx.mock() as respx_mock:
        # 1. Mock Jira Search (First attempt fails)
        jira_search = respx_mock.get("https://api.atlassian.com/ex/jira/cloud-1/rest/api/3/search").mock(
            side_effect=[
                Response(401),            # First call
                Response(200, json={"issues": []}) # Second call (retry)
            ]
        )
        
        # 2. Mock Proxy Refresh (Must be called)
        proxy_refresh = respx_mock.post("http://localhost:8001/refresh").mock(
            return_value=Response(200, json={
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token"
            })
        )
        
        # Execute
        results = await client.search_issues(jql="pk=TEST-1")
        
        # Verify
        assert proxy_refresh.called
        assert jira_search.call_count == 2
        assert client.token == "new_access_token"
        assert client.refresh_token == "new_refresh_token"
        assert results == []

@pytest.mark.asyncio
async def test_search_issues_without_cloud_id():
    client = JiraClient(token="valid")
    with pytest.raises(ValueError, match="Cloud ID not selected"):
        await client.search_issues("jql")
