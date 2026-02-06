import os
import json
import httpx
import chainlit as cl
from chainlit.input_widget import Select, TextInput


API_URL = os.getenv("API_URL", "http://localhost:8000")


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
                label="🔑 API Key",
                description="Enter your API key (Gemini or Anthropic)",
                placeholder="Enter your API key here...",
                initial="",
            ),
        ]
    ).send()
    
    await cl.Message(
        content="""# 👋 Welcome to Atlassian Helper!

Before we start, please configure your AI settings:

1. **Select your AI model** (Gemini or Claude)
2. **Enter your API key** in the settings panel above ⬆️
3. Click the **⚙️ Settings** button to update

---

### 🔑 Get Your API Key

| Provider | Get Key |
|----------|---------|
| **Gemini** | [Google AI Studio](https://aistudio.google.com/apikey) |
| **Claude** | [Anthropic Console](https://console.anthropic.com/settings/keys) |

---

Once configured, ask me about:
- 📋 **Jira tickets**: "What's the status of PROJ-123?"
- 📝 **Confluence**: "Find docs about authentication"
- 📊 **Sprint boards**: "Show me the current sprint"
"""
    ).send()


@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Handle settings update - validate and save configuration."""
    model_provider = settings.get("model_provider", "gemini")
    api_key = settings.get("api_key", "").strip()
    
    if not api_key:
        await cl.Message(
            content="⚠️ **API Key Required**\n\nPlease enter your API key in the settings panel above.",
            author="system",
        ).send()
        return
    
    config = {
        "model_provider": model_provider,
        "api_key": api_key,
    }
    cl.user_session.set("config", config)
    cl.user_session.set("configured", True)
    
    provider_name = "Google Gemini" if model_provider == "gemini" else "Anthropic Claude"
    masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    
    await cl.Message(
        content=f"""✅ **Configuration Saved!**

| Setting | Value |
|---------|-------|
| **Model** | {provider_name} |
| **API Key** | `{masked_key}` |

---

🎉 **You're all set!** Start chatting by typing a message below.

Try: *"Hello, what can you help me with?"*
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
            content="⚠️ **Please configure your API key first!**\n\nClick the ⚙️ **Settings** button in the chat bar above to enter your API key.",
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
