import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass
import time

TOKEN_FILE = Path("token_storage.json")


@dataclass
class OAuthToken:
    """OAuth 2.1 Token Data."""
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class TokenStorage:
    """Persistent token storage using local JSON file."""
    
    _token: OAuthToken | None = None
    
    @classmethod
    def save_token(cls, token_data: dict[str, Any]) -> None:
        """Save token data from OAuth response to file."""
        # Handle expires_in (seconds from now)
        expires_in = token_data.get("expires_in", 3600)
        expires_at = time.time() + float(expires_in)
        
        cls._token = OAuthToken(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at
        )
        
        # Persist to disk
        try:
            with open(TOKEN_FILE, "w") as f:
                data = {
                    "access_token": cls._token.access_token,
                    "refresh_token": cls._token.refresh_token,
                    "expires_at": cls._token.expires_at
                }
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save token to file: {e}")
    
    @classmethod
    def get_token(cls) -> OAuthToken | None:
        """Get the current token, loading from file if not in memory."""
        if cls._token:
            return cls._token
            
        if not TOKEN_FILE.exists():
            return None
            
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                cls._token = OAuthToken(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    expires_at=data.get("expires_at")
                )
            return cls._token
        except Exception as e:
            print(f"Failed to load token from file: {e}")
            return None
    
    @classmethod
    def clear_token(cls) -> None:
        """Clear the current token from memory and disk."""
        cls._token = None
        if TOKEN_FILE.exists():
            try:
                TOKEN_FILE.unlink()
            except Exception as e:
                print(f"Failed to delete token file: {e}")
