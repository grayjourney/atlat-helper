import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage

from src.agents.router import classify_intent, route_by_intent, IntentClassification


class TestRouteByIntent:
    
    def test_routes_ticket_intent(self):
        state = {"intent": "ticket", "messages": []}
        assert route_by_intent(state) == "ticket_subgraph"
    
    def test_routes_confluence_intent(self):
        state = {"intent": "confluence", "messages": []}
        assert route_by_intent(state) == "confluence_subgraph"
    
    def test_routes_board_intent(self):
        state = {"intent": "board", "messages": []}
        assert route_by_intent(state) == "board_subgraph"
    
    def test_routes_general_chat_intent(self):
        state = {"intent": "general_chat", "messages": []}
        assert route_by_intent(state) == "general_chat_node"
    
    def test_routes_unknown_intent_to_general_chat(self):
        state = {"intent": "unknown_intent", "messages": []}
        assert route_by_intent(state) == "general_chat_node"
    
    def test_routes_none_intent_to_general_chat(self):
        state = {"intent": None, "messages": []}
        assert route_by_intent(state) == "general_chat_node"


class TestClassifyIntent:
    
    @pytest.mark.asyncio
    async def test_classify_intent_extracts_last_message(self):
        state = {
            "messages": [
                HumanMessage(content="Hello"),
                HumanMessage(content="Get ticket PROJ-123"),
            ],
            "intent": None,
        }
        config = {"configurable": {"model_provider": "gemini", "api_key": "test"}}
        
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.ainvoke = AsyncMock(
            return_value=IntentClassification(intent="ticket")
        )
        
        with patch("src.agents.router.LLMFactory.from_config", return_value=mock_llm):
            result = await classify_intent(state, config)
        
        assert result == {"intent": "ticket"}
        mock_llm.with_structured_output.assert_called_once_with(IntentClassification)
    
    @pytest.mark.asyncio
    async def test_classify_intent_returns_general_chat(self):
        state = {
            "messages": [HumanMessage(content="How are you?")],
            "intent": None,
        }
        config = {"configurable": {}}
        
        mock_llm = MagicMock()
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.ainvoke = AsyncMock(
            return_value=IntentClassification(intent="general_chat")
        )
        
        with patch("src.agents.router.LLMFactory.from_config", return_value=mock_llm):
            result = await classify_intent(state, config)
        
        assert result == {"intent": "general_chat"}


class TestIntentClassification:
    
    def test_valid_ticket_intent(self):
        intent = IntentClassification(intent="ticket")
        assert intent.intent == "ticket"
    
    def test_valid_confluence_intent(self):
        intent = IntentClassification(intent="confluence")
        assert intent.intent == "confluence"
    
    def test_valid_board_intent(self):
        intent = IntentClassification(intent="board")
        assert intent.intent == "board"
    
    def test_valid_general_chat_intent(self):
        intent = IntentClassification(intent="general_chat")
        assert intent.intent == "general_chat"
    
    def test_invalid_intent_raises_validation_error(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            IntentClassification(intent="invalid")
