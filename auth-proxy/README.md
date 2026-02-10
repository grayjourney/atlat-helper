# Atlat Helper Auth Proxy

This service acts as the OAuth 2.0 Backend for the Atlat Helper desktop application. It secures the Atlassian `CLIENT_SECRET` and handles the token exchange, allowing the desktop app to remain a "Public Client" (safe for distribution).

## Setup

1.  **Environment Variables**:
    Create a `.env` file in this directory (or set env vars in your deployment provider):
    ```env
    ATLASSIAN_CLIENT_ID=your_client_id
    ATLASSIAN_CLIENT_SECRET=your_client_secret
    PROXY_BASE_URL=https://your-deployed-proxy.com
    ```

    *   `ATLASSIAN_CLIENT_ID`: From Atlassian Developer Console.
    *   `ATLASSIAN_CLIENT_SECRET`: From Atlassian Developer Console.
    *   `PROXY_BASE_URL`: The public URL where this proxy is deployed.

2.  **Atlassian Console Configuration**:
    *   Go to your App in Atlassian Console.
    *   Set **Callback URL** to: `https://your-deployed-proxy.com/callback` (e.g., `http://localhost:8001/callback` for testing).

## Local Development
```bash
pip install -r requirements.txt
export ATLASSIAN_CLIENT_ID=...
export ATLASSIAN_CLIENT_SECRET=...
uvicorn main:app --port 8001 --reload
```

## Deployment
Deploy this folder to any Python hosting provider (Render, Railway, Vercel, AWS App Runner).
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
