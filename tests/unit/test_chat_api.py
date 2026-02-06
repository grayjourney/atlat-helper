import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from src.api.server import create_app
from src.api.schemas import ChatRequest, ChatResponse


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    
    def test_health_returns_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "atlat-api"}


class TestRootEndpoint:
    
    def test_root_returns_api_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Atlassian Helper Agent"
        assert "docs" in data


class TestChatEndpoint:
    
    def test_chat_returns_response_with_thread_id(self, client):
        with patch("src.api.routes._graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock(return_value={
                "messages": [AIMessage(content="Hello! How can I help?")],
                "intent": "general_chat",
            })
            
            response = client.post("/agent/chat", json={
                "message": "Hello",
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "thread_id" in data
            assert data["response"] == "Hello! How can I help?"
    
    def test_chat_uses_provided_thread_id(self, client):
        with patch("src.api.routes._graph") as mock_graph:
            mock_graph.ainvoke = AsyncMock(return_value={
                "messages": [AIMessage(content="Test response")],
                "intent": "ticket",
            })
            
            response = client.post("/agent/chat", json={
                "message": "Get ticket PROJ-123",
                "thread_id": "existing-thread-id",
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "existing-thread-id"
            assert data["intent"] == "ticket"


class TestChatRequestSchema:
    
    def test_message_required(self):
        with pytest.raises(Exception):
            ChatRequest(thread_id="test")
    
    def test_config_defaults_to_empty_dict(self):
        request = ChatRequest(message="Hello")
        assert request.config == {}
    
    def test_thread_id_optional(self):
        request = ChatRequest(message="Hello")
        assert request.thread_id is None


class TestChatResponseSchema:
    
    def test_creates_response_with_all_fields(self):
        response = ChatResponse(
            response="Test",
            thread_id="abc-123",
            intent="ticket",
        )
        assert response.response == "Test"
        assert response.thread_id == "abc-123"
        assert response.intent == "ticket"


class TestChatStreamEndpoint:
    
    def test_stream_returns_sse_content_type(self, client):
        with patch("src.api.routes._graph") as mock_graph:
            async def mock_stream(*args, **kwargs):
                return
                yield
            mock_graph.astream_events = mock_stream
            
            response = client.post("/agent/chat/stream", json={
                "message": "Hello",
            })
            
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
    
    def test_stream_emits_start_event_with_thread_id(self, client):
        with patch("src.api.routes._graph") as mock_graph:
            async def mock_stream(*args, **kwargs):
                return
                yield
            mock_graph.astream_events = mock_stream
            
            response = client.post("/agent/chat/stream", json={
                "message": "Hello",
            })
            
            lines = response.text.strip().split("\n\n")
            assert len(lines) >= 1
            
            import json
            first_event = json.loads(lines[0].replace("data: ", ""))
            assert first_event["type"] == "start"
            assert "thread_id" in first_event
    
    def test_stream_uses_provided_thread_id(self, client):
        with patch("src.api.routes._graph") as mock_graph:
            async def mock_stream(*args, **kwargs):
                return
                yield
            mock_graph.astream_events = mock_stream
            
            response = client.post("/agent/chat/stream", json={
                "message": "Hello",
                "thread_id": "custom-thread-123",
            })
            
            import json
            lines = response.text.strip().split("\n\n")
            first_event = json.loads(lines[0].replace("data: ", ""))
            assert first_event["thread_id"] == "custom-thread-123"

