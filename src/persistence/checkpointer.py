"""
Checkpointer Factory - State Persistence

This module provides a factory function to get the appropriate
checkpointer based on the environment (dev/test/prod).

=== What is a Checkpointer? ===

LangGraph's checkpointer saves the agent state after each node runs.
This enables:
1. Resume after server restart
2. Time travel to previous states
3. Multiple conversation threads

=== PHP Comparison ===

Like Laravel's Manager pattern for drivers:

    // config/session.php
    'driver' => env('SESSION_DRIVER', 'file'),
    
    // Usage
    Session::driver('redis');  // Switch driver

In our case:
    get_checkpointer()  // Returns MemorySaver or PostgresSaver

=== Go Comparison ===

Like a factory function returning an interface implementation:

    type Checkpointer interface {
        Save(threadID string, state State) error
        Load(threadID string) (State, error)
    }
    
    func NewCheckpointer(driver string) Checkpointer {
        switch driver {
        case "postgres":
            return &PostgresCheckpointer{}
        default:
            return &MemoryCheckpointer{}
        }
    }

Author: Gray
License: MIT
"""

import os
from typing import Union

# LangGraph checkpointer imports
from langgraph.checkpoint.memory import MemorySaver

# For production, uncomment and install:
# pip install langgraph-checkpoint-postgres
# from langgraph.checkpoint.postgres import PostgresSaver


# Type alias for checkpointer (will expand when adding PostgresSaver)
CheckpointerType = Union[MemorySaver]  # Add PostgresSaver when ready


def get_checkpointer(driver: str | None = None) -> CheckpointerType:
    """
    Factory function to get the appropriate checkpointer.
    
    Args:
        driver: Optional driver override. If None, reads from environment.
                Supported: "memory", "postgres" (future)
    
    Returns:
        A checkpointer instance ready to use with graph.compile()
    
    === Usage ===
    
        # Basic usage (reads from CHECKPOINTER_DRIVER env var)
        checkpointer = get_checkpointer()
        
        # Explicit driver selection
        checkpointer = get_checkpointer("memory")
        
        # Compile graph with persistence
        graph = builder.compile(checkpointer=checkpointer)
    
    === Thread ID Usage ===
    
    When invoking the graph, provide a thread_id to enable
    conversation tracking and resumption:
    
        config = {"configurable": {"thread_id": "user-123-conv-456"}}
        result = graph.invoke(input_state, config)
    
    === PHP Comparison ===
    
    This is like Laravel's Cache/Session manager:
    
        // config/cache.php
        'default' => env('CACHE_DRIVER', 'file'),
        
        // Runtime
        Cache::store('redis')->get('key');
    
    === Go Comparison ===
    
    Like dependency injection with environment-based selection:
    
        func NewCheckpointer() Checkpointer {
            driver := os.Getenv("CHECKPOINTER_DRIVER")
            if driver == "postgres" {
                return NewPostgresCheckpointer(os.Getenv("DATABASE_URL"))
            }
            return NewMemoryCheckpointer()
        }
    """
    # Determine which driver to use
    if driver is None:
        driver = os.getenv("CHECKPOINTER_DRIVER", "memory")
    
    driver = driver.lower()
    
    if driver == "memory":
        # MemorySaver: In-memory storage
        # - Fast, no setup required
        # - State lost on server restart
        # - Perfect for development and testing
        return MemorySaver()
    
    elif driver == "postgres":
        # PostgresSaver: Persistent database storage
        # - Survives server restarts
        # - Scales across multiple instances
        # - Required for production
        #
        # To enable:
        # 1. pip install langgraph-checkpoint-postgres
        # 2. Uncomment the import above
        # 3. Uncomment this block
        
        # connection_string = os.getenv("DATABASE_URL")
        # if not connection_string:
        #     raise ValueError(
        #         "DATABASE_URL environment variable required for postgres driver"
        #     )
        # return PostgresSaver.from_conn_string(connection_string)
        
        raise NotImplementedError(
            "PostgresSaver not yet configured. "
            "Install: pip install langgraph-checkpoint-postgres"
        )
    
    else:
        raise ValueError(
            f"Unknown checkpointer driver: '{driver}'. "
            f"Supported: 'memory', 'postgres'"
        )


# ============================================
# Singleton Pattern (Optional)
# ============================================
# If you want a global checkpointer instance, uncomment below.
# This is useful when you want to share state across requests.
#
# _checkpointer_instance: CheckpointerType | None = None
#
# def get_shared_checkpointer() -> CheckpointerType:
#     """Get a shared checkpointer instance (singleton)."""
#     global _checkpointer_instance
#     if _checkpointer_instance is None:
#         _checkpointer_instance = get_checkpointer()
#     return _checkpointer_instance
