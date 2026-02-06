from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    message: str = Field(..., min_length=1, description="User message")
    thread_id: str | None = Field(None, description="Conversation thread ID")
    config: dict[str, Any] = Field(default_factory=dict, description="LLM configuration")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    response: str
    thread_id: str
    intent: str | None = None
