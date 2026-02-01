"""
Chainlit UI Application
=======================

A simple chat interface for interacting with the Project Management Agent.

Run with:
    chainlit run ui/app.py

Or via Docker:
    docker compose up ui

Author: Gray
License: MIT
"""

import chainlit as cl


@cl.on_chat_start
async def on_chat_start():
    """
    Called when a new chat session starts.
    
    This is where we set up the initial state for the conversation.
    """
    await cl.Message(
        content="👋 Welcome to the **Project Management Agent**!\n\n"
                "I can help you manage your Jira/Trello tickets. Try asking:\n"
                "- *What's the status of PROJ-123?*\n"
                "- *Are there any blockers on my current sprint?*\n"
                "- *Update the priority of TASK-456 to high*"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Called when the user sends a message.
    
    For now, this is a placeholder that echoes the message.
    Will be connected to the FastAPI backend in Phase 4.
    """
    # TODO: Connect to FastAPI agent endpoint
    # response = await httpx.post("http://api:8000/api/v1/agent/run", json={...})
    
    await cl.Message(
        content=f"🤖 Received your message: *{message.content}*\n\n"
                "_Agent integration coming in Phase 4!_"
    ).send()
