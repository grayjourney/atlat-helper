from typing import Any, cast
import json
from functools import partial

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from src.agents.state import AgentState
from src.llm.factory import LLMFactory
from src.jira.client import JiraClient
from src.mcp.token_storage import TokenStorage

# Helper for Token Saving
def save_token_callback(data: dict):
    TokenStorage.save_token(data)

# --- Tools ---
@tool
async def list_tickets(query: str, config: RunnableConfig) -> str:
    """
    Search for Jira tickets using JQL or natural language keywords.
    Supported JQL fields: project, assignee, status, priority, text, created, updated.
    """
    conf = config.get("configurable", {})
    token = conf.get("token")
    refresh_token = conf.get("refresh_token")
    cloud_id = conf.get("cloud_id")
    
    if not token or not cloud_id:
        return "Error: Missing authentication or Cloud ID."

    try:
        async with JiraClient(token, refresh_token, cloud_id, on_refresh=save_token_callback) as client:
            issues = await client.search_issues(query)
            if not issues:
                return "No tickets found."
            
            # Format as compact JSON/Text for LLM
            # Just return key fields to save context
            results = []
            for issue in issues:
                fields = issue.get("fields", {})
                results.append({
                    "key": issue.get("key"),
                    "summary": fields.get("summary"),
                    "status": fields.get("status", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName", "Unassigned"),
                    "priority": fields.get("priority", {}).get("name")
                })
            return json.dumps(results)
    except Exception as e:
        return f"Error searching tickets: {str(e)}"

@tool
async def create_ticket(project_key: str, summary: str, issuetype: str, description: str = "", config: RunnableConfig = None) -> str:
    """
    Create a new Jira ticket.
    Args:
        project_key: The project key (e.g., "PROJ")
        summary: The ticket title
        issuetype: The issue type (e.g., "Task", "Bug")
        description: The ticket description body
    """
    if config is None:
        return "Error: Internal configuration missing."

    conf = config.get("configurable", {})
    token = conf.get("token")
    refresh_token = conf.get("refresh_token")
    cloud_id = conf.get("cloud_id")

    # TODO: Implement create_issue in JiraClient
    # For now, return generic error or stub
    return "Error: Create Ticket not fully implemented in Client yet." 


# --- Main Node ---
async def ticket_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Handle ticket operations using Jira REST Client.
    Manages Auth, Site Selection, and ReAct Loop.
    """
    # 1. Authentication Check
    token_data = TokenStorage.get_token()
    if not token_data or token_data.is_expired:
        # Note: Ideally we check expiry and refresh here too, but client handles basic refresh.
        # If deeply expired (refresh token dead), user must re-login.
        if not token_data:
             return {
                "messages": [
                    AIMessage(
                        content="⚠️ **Atlassian not connected**\n\nPlease click 'Connect to Atlassian' in the settings or chat actions."
                    )
                ]
            }

    # 2. Handle Cloud ID Selection (Multi-turn Interaction)
    if state.get("awaiting_input") == "cloud_id_selection":
        user_input = state["messages"][-1].content.strip()
        available_sites = state.get("available_sites", [])
        
        selected_site = None
        # Try index (1-based)
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(available_sites):
                selected_site = available_sites[idx]
        else:
            # Try name match
            for site in available_sites:
                if user_input.lower() in site["name"].lower():
                    selected_site = site
                    break
        
        if selected_site:
            return {
                "context": {**state.get("context", {}), "cloud_id": selected_site["id"]},
                "awaiting_input": None,
                "available_sites": None,
                "messages": [AIMessage(content=f"✅ Selected site: **{selected_site['name']}**. How can I help?")]
            }
        else:
            # Re-prompt (Interrupt again)
            return {
                 "messages": [AIMessage(content="❌ Invalid selection. Please try again (enter the number or name).")]
            }

    # 3. Resolve Cloud ID
    cloud_id = state.get("context", {}).get("cloud_id")
    if not cloud_id:
        # Fetch resources to find cloud_id
        try:
            async with JiraClient(token_data.access_token, token_data.refresh_token, on_refresh=save_token_callback) as client:
                sites = await client.get_accessible_resources()
                
            if len(sites) == 0:
                return {"messages": [AIMessage(content="⚠️ No Jira sites found for your account.")]}
            elif len(sites) == 1:
                cloud_id = sites[0]["id"]
                # Auto-select (Update context locally for this run and persist)
                # We continue execution with this cloud_id
            else:
                # Multiple sites -> Ask User
                site_list = "\n".join([f"{i+1}. **{s['name']}** ({s['url']})" for i, s in enumerate(sites)])
                return {
                    "awaiting_input": "cloud_id_selection",
                    "available_sites": sites,
                    "messages": [AIMessage(content=f"🔑 **Multiple Jira sites found.**\n\nPlease select one:\n{site_list}")]
                }
        except Exception as e:
             return {"messages": [AIMessage(content=f"❌ Error fetching Jira sites: {str(e)}")]}

    # 4. Agent Execution (ReAct)
    tools = [list_tickets, create_ticket]
    
    # Bind tools
    llm = LLMFactory.from_config(config.get("configurable", {}))
    llm_with_tools = llm.bind_tools(tools)
    
    # System Prompt
    system_msg = SystemMessage(content="""You are a Jira Task Assistant.
Use 'list_tickets' to search options. Use JQL if you know it, or keywords.
When displaying tickets, format them as a Markdown Table.
Columns: Key, Summary, Status, Assignee, Priority.
""")

    # Current context (messages)
    messages = [system_msg] + state["messages"]
    
    # Invoke LLM
    response = await llm_with_tools.ainvoke(messages)
    
    # Handle Tool Calls
    if response.tool_calls:
        tool_results = []
        messages.append(response)
        
        # Helper config for tools
        tool_config = config.copy()
        if "configurable" not in tool_config: tool_config["configurable"] = {}
        tool_config["configurable"].update({
            "token": token_data.access_token,
            "refresh_token": token_data.refresh_token,
            "cloud_id": cloud_id
        })
        
        for tool_call in response.tool_calls:
            selected_tool = next((t for t in tools if t.name == tool_call["name"]), None)
            if selected_tool:
                try:
                    # Execute with injected config
                    output = await selected_tool.ainvoke(tool_call, config=tool_config)
                    tool_results.append(ToolMessage(tool_call_id=tool_call["id"], name=tool_call["name"], content=str(output)))
                except Exception as e:
                    tool_results.append(ToolMessage(tool_call_id=tool_call["id"], name=tool_call["name"], content=f"Error: {str(e)}"))
        
        messages.extend(tool_results)
        # Final response
        final_response = await llm.ainvoke(messages)
        
        # Return state update
        # If we auto-selected cloud_id, we should persist it in context
        new_context = state.get("context", {}).copy()
        if cloud_id and new_context.get("cloud_id") != cloud_id:
            new_context["cloud_id"] = cloud_id
            
        return {
            "messages": [response] + tool_results + [final_response],
            "context": new_context
        }

    return {"messages": [response]}
