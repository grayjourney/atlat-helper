"""
Pytest Configuration and Fixtures

This file is automatically loaded by pytest.
It provides shared fixtures (setup/teardown) for all tests.

Think of it like:
- Go: TestMain() or helper functions in *_test.go files
- PHP: TestCase base class or setUp/tearDown methods

Key concepts:
- @pytest.fixture: A decorator that marks a function as a fixture
- Fixtures provide reusable test dependencies
- They can be scoped: function, class, module, or session
"""

import pytest
from typing import Generator


# ============================================
# Fixture Examples (to be expanded)
# ============================================

@pytest.fixture
def sample_ticket_id() -> str:
    """
    A simple fixture that provides a test ticket ID.
    
    Usage in tests:
        def test_something(sample_ticket_id):
            assert sample_ticket_id == "TEST-123"
    
    PHP equivalent:
        protected function setUp(): void {
            $this->ticketId = "TEST-123";
        }
    
    Go equivalent:
        func setupTest(t *testing.T) string {
            return "TEST-123"
        }
    """
    return "TEST-123"


@pytest.fixture
def sample_ticket_data() -> dict:
    """
    Provides sample ticket data for testing.
    
    Returns a dictionary (like PHP associative array or Go map).
    """
    return {
        "id": "TEST-123",
        "title": "Fix login bug",
        "status": "In Progress",
        "blockers": ["Waiting for API access", "Need design review"],
        "assignee": "gray",
        "priority": "high",
    }


# ============================================
# Async Fixtures (for async tests)
# ============================================

@pytest.fixture
def anyio_backend() -> str:
    """
    Required fixture for pytest-asyncio.
    Specifies which async backend to use.
    """
    return "asyncio"


# ============================================
# Future fixtures (to be implemented)
# ============================================

# @pytest.fixture
# async def mock_mcp_client():
#     """Provides a mock MCP client for testing."""
#     pass

# @pytest.fixture
# async def mock_llm():
#     """Provides a mock LLM for testing."""
#     pass

# @pytest.fixture
# async def agent_graph():
#     """Provides a compiled agent graph for testing."""
#     pass
