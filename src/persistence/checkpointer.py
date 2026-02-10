"""Checkpointer Factory - State Persistence with SQLite."""

import os
import sys
from pathlib import Path
from typing import Union

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver


CheckpointerType = Union[MemorySaver, SqliteSaver]


def get_app_data_dir() -> Path:
    app_name = "atlat-helper"
    
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    app_dir = base / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_checkpointer(driver: str | None = None) -> CheckpointerType:
    if driver is None:
        driver = os.getenv("CHECKPOINTER_DRIVER", "sqlite")
    
    driver = driver.lower()
    
    if driver == "memory":
        return MemorySaver()
    
    elif driver == "sqlite":
        db_path = get_app_data_dir() / "chat_history.db"
        conn = SqliteSaver.from_conn_string(str(db_path))
        return conn
    
    else:
        raise ValueError(
            f"Unknown checkpointer driver: '{driver}'. "
            f"Supported: 'memory', 'sqlite'"
        )
