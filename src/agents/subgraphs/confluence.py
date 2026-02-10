from typing import Any
import json

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.llm.factory import LLMFactory
from src.mcp.mcp_factory import AtlassianMCPFactory
from src.mcp.token_storage import TokenStorage


async def confluence_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Handle Confluence operations using Atlassian MCP tools.
    """
    # 1. Check Authentication
    token = TokenStorage.get_token()
    if not token or token.is_expired:
        return {
            "messages": [
                AIMessage(
                    content="⚠️ **Atlassian not connected**\n\nPlease click 'Connect to Atlassian' in the settings to enable Confluence features."
                )
            ]
        }
    
    # 2. Get MCP Tools
    try:
        tools = await AtlassianMCPFactory.get_tools(token.access_token)
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"❌ **Connection Error**: Failed to connect to Atlassian MCP: {str(e)}")]
        }

    # 3. Bind Tools to LLM
    llm = LLMFactory.from_config(config.get("configurable", {}))
    llm_with_tools = llm.bind_tools(tools)
    
    # 4. Prepare System Prompt
    system_msg = SystemMessage(content="""You are a Confluence expert.
Use the provided tools to search and retrieve documentation from Confluence.

GUIDELINES:
- When searching, use broad terms if specific ones fail.
- Summarize long pages concisely.
- Always provide the URL to the Confluence page if available.
""")
    
    # 5. Invoke LLM
    messages = [system_msg] + state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    
    # 6. Handle Tool Calls (Simple ReAct Loop)
    if response.tool_calls:
        tool_results = []
        messages.append(response)
        
        for tool_call in response.tool_calls:
            selected_tool = next((t for t in tools if t.name == tool_call["name"]), None)
            
            if selected_tool:
                try:
                    tool_output = await selected_tool.ainvoke(tool_call)
                    
                    tool_results.append(
                        ToolMessage(
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"],
                            content=str(tool_output)
                        )
                    )
                except Exception as e:
                     tool_results.append(
                        ToolMessage(
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"],
                            content=f"Error executing tool: {str(e)}"
                        )
                    )
            else:
                tool_results.append(
                    ToolMessage(
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"],
                        content=f"Error: Tool '{tool_call['name']}' not found."
                    )
                )
        
        # Append tool results via messages.extend (not supported by +, usually)
        # Actually dict concatenation or just list + list works in Python
        messages.extend(tool_results)
        final_response = await llm.ainvoke(messages)
        return {"messages": [response] + tool_results + [final_response]}

    return {"messages": [response]}
