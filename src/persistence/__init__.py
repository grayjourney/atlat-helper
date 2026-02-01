"""
Persistence Module - State Persistence Layer

Contains:
- checkpointer.py: Checkpointer factory for dev/prod environments
- memory.py: MemorySaver wrapper (development)

This module handles saving agent state between node executions,
enabling conversation resumption after server restarts.

Think of it like:
- Go: A StateStore interface with Redis/Postgres implementations
- PHP: Laravel's Session/Cache with multiple drivers

=== Why Persistence Matters ===

In a "Cursor-like" app, if the server restarts, you don't want
to lose the agent's context. The checkpointer saves state after
each node, so you can resume from any point.

=== Usage ===

    from src.persistence.checkpointer import get_checkpointer
    
    checkpointer = get_checkpointer()  # Returns appropriate saver
    graph = builder.compile(checkpointer=checkpointer)
"""

from .checkpointer import get_checkpointer

__all__ = ["get_checkpointer"]
