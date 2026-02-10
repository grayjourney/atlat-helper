import os
import httpx
import base64
import json
from urllib.parse import urlencode
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Atlat Helper Auth Proxy")

# Configuration
CLIENT_ID = os.getenv("ATLASSIAN_CLIENT_ID")
CLIENT_SECRET = os.getenv("ATLASSIAN_CLIENT_SECRET")
# The public URL of THIS proxy service (e.g. https://api.atlat-helper.com)
PROXY_BASE_URL = os.getenv("PROXY_BASE_URL", "http://localhost:8001")
TEMP_REDIRECT_URI = f"{PROXY_BASE_URL}/callback"

if not CLIENT_ID or not CLIENT_SECRET:
    print("WARNING: ATLASSIAN_CLIENT_ID or ATLASSIAN_CLIENT_SECRET not set.")

@app.get("/")
async def root():
    return {"status": "ok", "service": "atlat-helper-auth-proxy"}

@app.get("/login")
async def login(redirect_to: str, state: str = "no_state"):
    """
    Initiate OAuth flow.
    redirect_to: The URL to redirect back to (e.g., http://localhost:8000/auth/callback)
    state: Random state from client
    """
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="Server config error: Missing Client ID")

    # Encode user state + redirect_to into Atlassian state parameter
    # Format: "v1|redirect_to|original_state"
    # base64 encode to be safe
    custom_state_data = json.dumps({"redirect_to": redirect_to, "client_state": state})
    encoded_state = base64.urlsafe_b64encode(custom_state_data.encode()).decode()

    # 3LO Scopes via Code
    # Note: 'offline_access' is critical for refresh tokens
    scopes = [
        "read:jira-work",
        "write:jira-work",
        "read:confluence-content.all",
        "write:confluence-content",
        "offline_access"
    ]

    params = {
        "audience": "api.atlassian.com",
        "client_id": CLIENT_ID,
        "scope": " ".join(scopes),
        "redirect_uri": TEMP_REDIRECT_URI,
        "state": encoded_state,
        "response_type": "code",
        "prompt": "consent",
    }
    
    auth_url = f"https://auth.atlassian.com/authorize?{urlencode(params)}"
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(code: str, state: str):
    """
    Handle callback from Atlassian.
    Exchange code for tokens, then redirect to the client's local server.
    """
    try:
        decoded_state = json.loads(base64.urlsafe_b64decode(state).decode())
        redirect_to = decoded_state.get("redirect_to")
        client_state = decoded_state.get("client_state")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if not redirect_to:
        raise HTTPException(status_code=400, detail="Missing redirect_to in state")

    if not CLIENT_ID or not CLIENT_SECRET:
         raise HTTPException(status_code=500, detail="Server config error")

    # Exchange code for token
    token_url = "https://auth.atlassian.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": TEMP_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(token_url, json=payload)
            resp.raise_for_status()
            token_data = resp.json()
        except httpx.HTTPStatusError as e:
            return JSONResponse(status_code=e.response.status_code, content=e.response.json())

    # Construct redirect to client
    # We pass tokens as query parameters
    # WARNING: Access tokens in URL is visible in history/logs locally. 
    # For a localhost redirect this is acceptable standard practice for CLI OAuth.
    # Alternatively, we could serve a page that postsMessage, but that requires Client browser logic.
    
    redirect_params = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
        "state": client_state
    }
    
    final_url = f"{redirect_to}?{urlencode(redirect_params)}"
    return RedirectResponse(final_url)

@app.post("/refresh")
async def refresh_token(request: Request):
    """
    Proxy token refresh request.
    Client sends refresh_token, Proxy adds Client Secret and calls Atlassian.
    """
    body = await request.json()
    refresh_token = body.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh_token")

    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token
    }

    token_url = "https://auth.atlassian.com/oauth/token"
    
    async with httpx.AsyncClient() as client:
         resp = await client.post(token_url, json=payload)
         # Pass through response
         return JSONResponse(content=resp.json(), status_code=resp.status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
