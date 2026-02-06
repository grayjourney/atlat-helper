import os
from typing import Literal
from langchain_core.language_models import BaseChatModel

LLMProvider = Literal["claude", "gemini", "ollama"]

DEFAULT_MODELS: dict[LLMProvider, str] = {
    "claude": "claude-3-5-sonnet-20241022",
    "gemini": "gemini-2.5-flash",
    "ollama": "llama3.1",
}


class LLMFactory:
    
    @staticmethod
    def create(
        provider: LLMProvider = "gemini",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ) -> BaseChatModel:
        if provider not in DEFAULT_MODELS:
            raise ValueError(f"Unknown provider: {provider}")
        model_name = model or DEFAULT_MODELS[provider]
        
        match provider:
            case "claude":
                from langchain_anthropic import ChatAnthropic
                key = api_key or os.getenv("ANTHROPIC_API_KEY")
                if not key:
                    raise ValueError("api_key required for Claude (set ANTHROPIC_API_KEY)")
                return ChatAnthropic(model=model_name, api_key=key, **kwargs)
            
            case "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if not key:
                    raise ValueError("api_key required for Gemini (set GEMINI_API_KEY)")
                return ChatGoogleGenerativeAI(model=model_name, google_api_key=key, **kwargs)
            
            case "ollama":
                from langchain_ollama import ChatOllama
                url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
                return ChatOllama(model=model_name, base_url=url, **kwargs)
            
            case _:
                raise ValueError(f"Unknown provider: {provider}")
    
    @staticmethod
    def from_config(config: dict) -> BaseChatModel:
        return LLMFactory.create(
            provider=config.get("model_provider", "gemini"),
            model=config.get("model_name"),
            api_key=config.get("api_key"),
            base_url=config.get("ollama_url"),
        )

