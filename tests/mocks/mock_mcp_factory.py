from langchain_core.tools import tool
from typing import Any

class MockJiraTools:
    """Mock tools for Jira operations."""
    
    @staticmethod
    @tool
    def search_issues(jql: str) -> str:
        """Search for Jira issues using JQL."""
        # Simple mock logic based on input
        if "TEST-1" in jql:
             return '{"issues": [{"key": "TEST-1", "fields": {"summary": "Test Ticket", "status": {"name": "In Progress"}, "description": "This is a test ticket", "assignee": {"displayName": "Test User"}, "priority": {"name": "High"}}}]}'
        return '{"issues": []}'

    @staticmethod
    @tool
    def read_issue(issue_key: str) -> str:
        """Read a Jira issue by key."""
        if issue_key == "TEST-1":
            return '{"key": "TEST-1", "fields": {"summary": "Test Ticket", "status": {"name": "In Progress"}, "description": "This is a test ticket", "assignee": {"displayName": "Test User"}, "priority": {"name": "High"}}}'
        return '{"error": "Issue not found"}'

class MockConfluenceTools:
    """Mock tools for Confluence operations."""
    
    @staticmethod
    @tool
    def search_confluence(query: str) -> str:
        """Search Confluence pages."""
        if "auth" in query.lower():
            return '{"results": [{"title": "Authentication Guide", "url": "https://confluence.example.com/auth", "excerpt": "How to authenticate..."}]}'
        return '{"results": []}'
        
    @staticmethod
    @tool
    def read_confluence_page(page_id: str) -> str:
        """Read a Confluence page by ID."""
        return '{"title": "Test Page", "body": "Page content"}'

class MockMCPFactory:
    """Mock factory that returns local fake tools."""
    
    @classmethod
    async def get_tools(cls, oauth_token: str | None = None) -> list[Any]:
        # Return a list of the decorated tool functions
        return [
            MockJiraTools.search_issues,
            MockJiraTools.read_issue,
            MockConfluenceTools.search_confluence,
            MockConfluenceTools.read_confluence_page
        ]
