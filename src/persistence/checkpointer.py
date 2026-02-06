"""Checkpointer Factory - State Persistence."""

import os
from typing import Union

from langgraph.checkpoint.memory import MemorySaver


CheckpointerType = Union[MemorySaver]


def get_checkpointer(driver: str | None = None) -> CheckpointerType:
    """Factory function to get the appropriate checkpointer."""
    if driver is None:
        driver = os.getenv("CHECKPOINTER_DRIVER", "memory")
    
    driver = driver.lower()
    
    if driver == "memory":
        return MemorySaver()
    
    elif driver == "postgres":
        raise NotImplementedError(
            "PostgresSaver not yet configured. "
            "Install: pip install langgraph-checkpoint-postgres"
        )
    
    else:
        raise ValueError(
            f"Unknown checkpointer driver: '{driver}'. "
            f"Supported: 'memory', 'postgres'"
        )
