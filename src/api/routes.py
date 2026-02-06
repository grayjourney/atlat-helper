import uuid
import json
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from src.api.schemas import ChatRequest, ChatResponse
from src.agents.supervisor import build_supervisor_graph


_checkpointer = MemorySaver()
_graph = build_supervisor_graph(checkpointer=_checkpointer)


def register_routes(app: FastAPI) -> None:
    """Register all API routes on the FastAPI app."""
    
    @app.get("/", tags=["System"])
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "Atlassian Helper Agent",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    
    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint for container orchestration."""
        return {"status": "healthy", "service": "atlat-api"}
    
    @app.post("/agent/chat", tags=["Agent"])
    async def chat(request: ChatRequest) -> ChatResponse:
        """Invoke the agent supervisor graph (non-streaming)."""
        thread_id = request.thread_id or str(uuid.uuid4())
        
        config = {
            "configurable": {
                "thread_id": thread_id,
                **request.config,
            }
        }
        
        result = await _graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )
        
        last_message = result["messages"][-1]
        response_text = last_message.content if isinstance(last_message, AIMessage) else str(last_message)
        
        return ChatResponse(
            response=response_text,
            thread_id=thread_id,
            intent=result.get("intent"),
        )
    
    @app.post("/agent/chat/stream", tags=["Agent"])
    async def chat_stream(request: ChatRequest) -> StreamingResponse:
        """Invoke the agent supervisor graph with SSE streaming."""
        thread_id = request.thread_id or str(uuid.uuid4())
        
        config = {
            "configurable": {
                "thread_id": thread_id,
                **request.config,
            }
        }
        
        async def event_generator() -> AsyncGenerator[str, None]:
            yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id})}\n\n"
            
            final_content = ""
            
            async for event in _graph.astream_events(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
                version="v2",
            ):
                event_type = event.get("event")
                
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                        final_content += chunk.content
                
                elif event_type == "on_chain_end":
                    node_name = event.get("name")
                    
                    if node_name == "classify_intent":
                        output = event.get("data", {}).get("output", {})
                        intent = output.get("intent")
                        if intent:
                            yield f"data: {json.dumps({'type': 'intent', 'intent': intent})}\n\n"
                    
                    elif node_name in ["ticket_subgraph", "general_chat_node", "confluence_subgraph", "board_subgraph"]:
                        output = event.get("data", {}).get("output", {})
                        messages = output.get("messages", [])
                        if messages and not final_content:
                            last_msg = messages[-1]
                            if hasattr(last_msg, "content") and last_msg.content:
                                yield f"data: {json.dumps({'type': 'message', 'content': last_msg.content})}\n\n"
            
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
