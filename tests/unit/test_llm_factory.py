import pytest
from unittest.mock import patch, MagicMock

from src.llm.factory import LLMFactory, LLMProvider, DEFAULT_MODELS


class TestLLMFactoryCreate:
    
    def test_create_gemini_with_api_key(self):
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            
            result = LLMFactory.create("gemini", api_key="test-key")
            
            mock_cls.assert_called_once_with(
                model=DEFAULT_MODELS["gemini"],
                google_api_key="test-key",
            )
            assert result == mock_instance
    
    def test_create_gemini_without_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="api_key required for Gemini"):
                LLMFactory.create("gemini")
    
    def test_create_claude_with_api_key(self):
        with patch("langchain_anthropic.ChatAnthropic") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            
            result = LLMFactory.create("claude", api_key="test-key")
            
            mock_cls.assert_called_once_with(
                model=DEFAULT_MODELS["claude"],
                api_key="test-key",
            )
            assert result == mock_instance
    
    def test_create_claude_without_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="api_key required for Claude"):
                LLMFactory.create("claude")
    
    def test_create_ollama_with_default_url(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("langchain_ollama.ChatOllama") as mock_cls:
                mock_instance = MagicMock()
                mock_cls.return_value = mock_instance
                
                result = LLMFactory.create("ollama")
                
                mock_cls.assert_called_once_with(
                    model=DEFAULT_MODELS["ollama"],
                    base_url="http://localhost:11434",
                )
                assert result == mock_instance
    
    def test_create_ollama_with_custom_url(self):
        with patch("langchain_ollama.ChatOllama") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            
            result = LLMFactory.create("ollama", base_url="http://custom:11434")
            
            mock_cls.assert_called_once_with(
                model=DEFAULT_MODELS["ollama"],
                base_url="http://custom:11434",
            )
            assert result == mock_instance
    
    def test_create_with_custom_model(self):
        with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
            LLMFactory.create("gemini", model="gemini-2.0-pro", api_key="test-key")
            
            mock_cls.assert_called_once_with(
                model="gemini-2.0-pro",
                google_api_key="test-key",
            )
    
    def test_create_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            LLMFactory.create("unknown")


class TestLLMFactoryFromConfig:
    
    def test_from_config_with_full_config(self):
        with patch.object(LLMFactory, "create") as mock_create:
            config = {
                "model_provider": "claude",
                "model_name": "claude-3-opus",
                "api_key": "secret-key",
                "ollama_url": None,
            }
            
            LLMFactory.from_config(config)
            
            mock_create.assert_called_once_with(
                provider="claude",
                model="claude-3-opus",
                api_key="secret-key",
                base_url=None,
            )
    
    def test_from_config_with_empty_config_uses_gemini_default(self):
        with patch.object(LLMFactory, "create") as mock_create:
            LLMFactory.from_config({})
            
            mock_create.assert_called_once_with(
                provider="gemini",
                model=None,
                api_key=None,
                base_url=None,
            )
