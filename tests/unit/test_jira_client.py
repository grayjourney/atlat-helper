import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock

from src.mcp.jira_client import JiraClient, TicketSchema, TicketSummary


class TestJiraClientInit:
    
    def test_init_creates_basic_auth_header(self):
        client = JiraClient(
            base_url="https://example.atlassian.net",
            email="user@example.com",
            api_token="test-token",
        )
        
        expected_auth = base64.b64encode(b"user@example.com:test-token").decode()
        assert client._auth_headers == {"Authorization": f"Basic {expected_auth}"}
        assert client.base_url == "https://example.atlassian.net"


class TestTicketSchemaFromRaw:
    
    def test_from_raw_with_full_data(self):
        raw = {
            "key": "PROJ-123",
            "fields": {
                "summary": "Test ticket",
                "description": "A description",
                "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate"}},
                "assignee": {"displayName": "John Doe"},
                "reporter": {"displayName": "Jane Doe"},
                "priority": {"name": "High"},
                "labels": ["bug", "urgent"],
                "created": "2026-01-01T10:00:00.000+0000",
                "updated": "2026-01-02T10:00:00.000+0000",
            }
        }
        
        ticket = TicketSchema.from_raw(raw)
        
        assert ticket.key == "PROJ-123"
        assert ticket.summary == "Test ticket"
        assert ticket.description == "A description"
        assert ticket.status == "In Progress"
        assert ticket.status_category == "indeterminate"
        assert ticket.assignee == "John Doe"
        assert ticket.reporter == "Jane Doe"
        assert ticket.priority == "High"
        assert ticket.labels == ["bug", "urgent"]
    
    def test_from_raw_with_missing_optional_fields(self):
        raw = {
            "key": "PROJ-456",
            "fields": {
                "summary": "Minimal ticket",
                "status": {"name": "Open"},
            }
        }
        
        ticket = TicketSchema.from_raw(raw)
        
        assert ticket.key == "PROJ-456"
        assert ticket.summary == "Minimal ticket"
        assert ticket.status == "Open"
        assert ticket.assignee is None
        assert ticket.reporter is None
        assert ticket.priority is None
        assert ticket.labels == []
    
    def test_from_raw_with_null_status(self):
        raw = {"key": "PROJ-789", "fields": {"summary": "No status", "status": None}}
        
        ticket = TicketSchema.from_raw(raw)
        
        assert ticket.status == "Unknown"


class TestTicketSummaryFromRaw:
    
    def test_from_raw_extracts_summary_fields(self):
        raw = {
            "key": "PROJ-100",
            "fields": {
                "summary": "Summary ticket",
                "status": {"name": "Done"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "Low"},
            }
        }
        
        summary = TicketSummary.from_raw(raw)
        
        assert summary.key == "PROJ-100"
        assert summary.summary == "Summary ticket"
        assert summary.status == "Done"
        assert summary.assignee == "Alice"
        assert summary.priority == "Low"


class TestJiraClientGetTicket:
    
    @pytest.mark.asyncio
    async def test_get_ticket_calls_get_with_correct_path(self):
        client = JiraClient("https://test.atlassian.net", "user@test.com", "token")
        
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"key": "TEST-1", "fields": {}}
            
            result = await client.get_ticket("TEST-1")
            
            mock_get.assert_called_once_with("/rest/api/3/issue/TEST-1", params=None)
            assert result == {"key": "TEST-1", "fields": {}}
    
    @pytest.mark.asyncio
    async def test_get_ticket_with_expand_param(self):
        client = JiraClient("https://test.atlassian.net", "user@test.com", "token")
        
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"key": "TEST-1", "fields": {}}
            
            await client.get_ticket("TEST-1", expand="changelog,names")
            
            mock_get.assert_called_once_with(
                "/rest/api/3/issue/TEST-1",
                params={"expand": "changelog,names"}
            )


class TestJiraClientListTickets:
    
    @pytest.mark.asyncio
    async def test_list_tickets_builds_correct_jql(self):
        client = JiraClient("https://test.atlassian.net", "user@test.com", "token")
        
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"issues": []}
            
            await client.list_tickets("PROJ")
            
            mock_get.assert_called_once_with(
                "/rest/api/3/search",
                params={"jql": "project = PROJ ORDER BY updated DESC", "maxResults": 50}
            )
    
    @pytest.mark.asyncio
    async def test_list_tickets_with_status_filter(self):
        client = JiraClient("https://test.atlassian.net", "user@test.com", "token")
        
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"issues": []}
            
            await client.list_tickets("PROJ", status="In Progress")
            
            mock_get.assert_called_once_with(
                "/rest/api/3/search",
                params={
                    "jql": 'project = PROJ AND status = "In Progress" ORDER BY updated DESC',
                    "maxResults": 50
                }
            )
    
    @pytest.mark.asyncio
    async def test_list_tickets_with_custom_order(self):
        client = JiraClient("https://test.atlassian.net", "user@test.com", "token")
        
        with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"issues": []}
            
            await client.list_tickets("PROJ", order_by="created DESC")
            
            mock_get.assert_called_once_with(
                "/rest/api/3/search",
                params={"jql": "project = PROJ ORDER BY created DESC", "maxResults": 50}
            )


class TestJiraClientTypedMethods:
    
    @pytest.mark.asyncio
    async def test_get_ticket_typed_returns_schema(self):
        client = JiraClient("https://test.atlassian.net", "user@test.com", "token")
        
        with patch.object(client, "get_ticket", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "key": "TEST-1",
                "fields": {"summary": "Test", "status": {"name": "Open"}}
            }
            
            result = await client.get_ticket_typed("TEST-1")
            
            assert isinstance(result, TicketSchema)
            assert result.key == "TEST-1"
            assert result.summary == "Test"
    
    @pytest.mark.asyncio
    async def test_list_tickets_typed_returns_list_of_schemas(self):
        client = JiraClient("https://test.atlassian.net", "user@test.com", "token")
        
        with patch.object(client, "list_tickets", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [
                {"key": "TEST-1", "fields": {"summary": "A", "status": {"name": "Open"}}},
                {"key": "TEST-2", "fields": {"summary": "B", "status": {"name": "Done"}}},
            ]
            
            result = await client.list_tickets_typed("PROJ")
            
            assert len(result) == 2
            assert all(isinstance(t, TicketSchema) for t in result)
            assert result[0].key == "TEST-1"
            assert result[1].key == "TEST-2"
