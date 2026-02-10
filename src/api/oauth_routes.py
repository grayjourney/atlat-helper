import os
import httpx
import uuid
from urllib.parse import urlencode
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from src.mcp.token_storage import TokenStorage


router = APIRouter(prefix="/auth/atlassian", tags=["Auth"])


@router.get("/login")
async def login():
    """Redirect user to Auth Proxy for Login."""
    # We use a central proxy to handle the OAuth Secret
    auth_proxy_url = os.getenv("AUTH_PROXY_URL", "http://localhost:8001")
    # This is where the Proxy should redirect the User back to (Our Local App)
    # The user's browser will hit this URL with tokens in query params
    # We use PUBLIC_API_URL to ensure it's accessible from browser (localhost)
    public_api_url = os.getenv("PUBLIC_API_URL", "http://localhost:8000")
    callback_url = f"{public_api_url}/auth/atlassian/callback"
    
    params = {
        "redirect_to": callback_url,
        "state": str(uuid.uuid4()) # Client state
    }
    
    # Redirect to Proxy Login
    proxy_login_url = f"{auth_proxy_url}/login?{urlencode(params)}"
    return RedirectResponse(proxy_login_url)


@router.get("/callback")
async def callback(
    access_token: str | None = None, 
    refresh_token: str | None = None, 
    expires_in: int | None = None,
    error: str | None = None
):
    """
    Handle callback from Auth Proxy.
    The Proxy redirects here with tokens in query params.
    """
    if error:
        return HTMLResponse(f"<h1>OAuth Error</h1><p>{error}</p>", status_code=400)
    
    if not access_token:
        # If no access_token found directly, check if we received 'code' (Legacy/Direct flow mismatch)
        # But in Proxy flow, we expect access_token.
        return HTMLResponse("<h1>Error</h1><p>No access token received from Proxy.</p>", status_code=400)
        
    try:
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in or 3600
        }
        
        # Save token
        TokenStorage.save_token(token_data)
        
        return HTMLResponse(
            """
            <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Connected!</h1>
                    <p>You have successfully authenticated via Atlat Helper Proxy.</p>
                    <p>You can close this window and verify the status in the chat.</p>
                    <script>window.opener.postMessage("auth_success", "*");</script>
                </body>
            </html>
            """
        )
            
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


@router.get("/status")
async def status():
    """Check authentication status."""
    # Check for Basic Auth via Environment Variables
    if os.getenv("ATLASSIAN_EMAIL") and os.getenv("ATLASSIAN_API_TOKEN"):
        return {
            "authenticated": True,
            "method": "env_vars", 
            "token_expires_at": None
        }

    token = TokenStorage.get_token()
    is_authenticated = token is not None and not token.is_expired
    
    return {
        "authenticated": is_authenticated,
        "token_expires_at": token.expires_at if token else None
    }
