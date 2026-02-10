import os
import json
import httpx
import chainlit as cl
from chainlit.input_widget import Select, TextInput


API_URL = os.getenv("API_URL", "http://localhost:8000")
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:8000")

JIRA_TOKEN_URL = "https://id.atlassian.com/manage-profile/security/api-tokens"


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat and show configuration settings."""
    cl.user_session.set("thread_id", None)
    cl.user_session.set("config", {})
    cl.user_session.set("configured", False)
    
    settings = await cl.ChatSettings(
        [
            Select(
                id="model_provider",
                label="🤖 AI Model",
                description="Select which AI model to use",
                values=["gemini", "claude"],
                initial_value="gemini",
            ),
            TextInput(
                id="api_key",
                label="🔑 AI API Key",
                description="Enter your API key (Gemini or Anthropic)",
                placeholder="Enter your API key here...",
                initial=os.getenv("GEMINI_API_KEY", ""),
            ),
        ]
    ).send()
    
    # Check Atlassian Auth Status
    auth_status = "❌ Not Connected"
    is_authenticated = False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/auth/atlassian/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("authenticated"):
                    auth_status = "✅ Connected"
                    is_authenticated = True
    except Exception:
        pass
    
    actions = []
    if not is_authenticated:
        actions.append(
            cl.Action(
                name="connect_atlassian",
                value="connect",
                label="Connect to Atlassian",
                description="Login via OAuth",
                payload={"value": "connect"}
            )
        )
    
    await cl.Message(
        content=f"""# 👋 Welcome to Atlassian Helper!

Please configure your **AI API Key** in settings.

---

## 🏛️ Atlassian Connection
Status: **{auth_status}**

{ "Click the button below to connect:" if not is_authenticated else "You are connected and ready to go!" }
""",
        actions=actions
    ).send()


@cl.action_callback("connect_atlassian")
async def on_connect_atlassian(action: cl.Action):
    """Handle connection action."""
    login_url = f"{PUBLIC_API_URL}/auth/atlassian/login"
    
    await cl.Message(
        content=f"🔗 **[Click here to Login to Atlassian]({login_url})**\n\nAfter logging in, please restart the chat or type 'check status'.",
        author="system"
    ).send()


@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Handle settings update - validate and save configuration."""
    model_provider = settings.get("model_provider", "gemini")
    api_key = settings.get("api_key", "").strip()
    
    if not api_key:
        await cl.Message(
            content="⚠️ **AI API Key Required**\n\nPlease enter your AI API key in the settings panel.",
            author="system",
        ).send()
        return
    
    config = {
        "model_provider": model_provider,
        "api_key": api_key,
        "jira": {"auth_type": "oauth"} # Marker for backend
    }
    
    cl.user_session.set("config", config)
    cl.user_session.set("configured", True)
    
    provider_name = "Google Gemini" if model_provider == "gemini" else "Anthropic Claude"
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    
    await cl.Message(
        content=f"""✅ **Configuration Saved!**

| Setting | Value |
|---------|-------|
| **AI Model** | {provider_name} |
| **AI API Key** | `{masked_key}` |

---

🎉 **You're all set!**
""",
        author="system",
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming chat messages."""
    config = cl.user_session.get("config", {})
    configured = cl.user_session.get("configured", False)
    
    if not configured or not config.get("api_key"):
        await cl.Message(
            content="⚠️ **Please configure your API key first!**\n\nClick the ⚙️ **Settings** button to enter your credentials.",
            author="system",
        ).send()
        return
    
    thread_id = cl.user_session.get("thread_id")
    
    msg = cl.Message(content="")
    await msg.send()
    
    payload = {
        "message": message.content,
        "thread_id": thread_id,
        "config": config,
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{API_URL}/agent/chat/stream",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    msg.content = f"❌ **API Error** ({response.status_code})\n\n```\n{error_text.decode()[:500]}\n```"
                    await msg.update()
                    return
                
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    
                    event_type = data.get("type")
                    
                    if event_type == "start":
                        cl.user_session.set("thread_id", data.get("thread_id"))
                    
                    elif event_type == "token":
                        await msg.stream_token(data.get("content", ""))
                    
                    elif event_type == "intent":
                        intent = data.get("intent")
                        if intent and intent != "general_chat":
                            intent_emoji = {
                                "ticket": "🎫",
                                "confluence": "📝",
                                "board": "📊",
                            }.get(intent, "🎯")
                            await cl.Message(
                                content=f"{intent_emoji} *Detected intent: **{intent}***",
                                author="system",
                            ).send()
                    
                    elif event_type == "message":
                        content = data.get("content", "")
                        if content:
                            msg.content = content
                            await msg.update()
                    
                    elif event_type == "end":
                        if not msg.content:
                            msg.content = "🤔 No response generated. Please try again."
                        await msg.update()
                        
    except httpx.ConnectError:
        msg.content = "❌ **Connection Error**\n\nCould not connect to the API server. Please make sure the backend is running."
        await msg.update()
    except httpx.TimeoutException:
        msg.content = "⏱️ **Timeout**\n\nThe request took too long. Please try again."
        await msg.update()
    except Exception as e:
        msg.content = f"❌ **Error**\n\n```\n{str(e)}\n```"
        await msg.update()
