from typing import Any, List
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

class MockLLM:
    """
    A mock LLM that simulates tool calling behavior for testing.
    """
    def __init__(self):
        self.tools = []

    def bind_tools(self, tools: List[Any]):
        """Simulate binding tools to the LLM."""
        self.tools = tools
        return self

    async def ainvoke(self, messages: List[BaseMessage]) -> AIMessage:
        """
        Simulate LLM generation.
        
        Simple logic:
        1. If strict "status of TEST-1" request -> Call read_issue
        2. If last message is ToolMessage -> Return success text
        """
        last_msg = messages[-1]
        
        # Scenario 3: After tool execution (Check this FIRST to avoid loops)
        if isinstance(last_msg, ToolMessage):
             return AIMessage(content="Based on the tool output, the status is In Progress.")
        
        content = ""
        # Handle string content or list of content parts
        if isinstance(last_msg.content, str):
            content = last_msg.content
        elif isinstance(last_msg.content, list):
             # Handle list content (e.g. from previous steps)
             content = str(last_msg.content)

        # Scenario 1: User asks for ticket status
        if "TEST-1" in content and "status" in content.lower():
            return AIMessage(
                content="",
                tool_calls=[{
                    "name": "read_issue",
                    "args": {"issue_key": "TEST-1"},
                    "id": "call_test_1"
                }]
            )

        # Scenario 2: Search docs
        if "docs" in content.lower() or "search" in content.lower():
             return AIMessage(
                content="",
                tool_calls=[{
                    "name": "search_confluence",
                    "args": {"query": "auth"},
                    "id": "call_test_2"
                }]
            )
        
        return AIMessage(content="I am a mock LLM.")
