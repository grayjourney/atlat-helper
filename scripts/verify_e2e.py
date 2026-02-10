"""
verify_e2e.py

Automated E2E Verification Script for Atlassian MCP Integration.

Prerequisites:
1. `token_storage.json` must be present (OAuth).
   OR
2. `ATLASSIAN_EMAIL` and `ATLASSIAN_API_TOKEN` environment variables set (Basic Auth).

Usage:
    python scripts/verify_e2e.py
"""

import asyncio
import sys
import logging
import os
import base64
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.mcp.mcp_factory import AtlassianMCPFactory
from src.mcp.token_storage import TokenStorage

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_auth_token():
    """Get auth token from storage or env."""
    # 1. Try TokenStorage (OAuth)
    token = TokenStorage.get_token()
    if token and not token.is_expired:
        logger.info("✅ Found valid OAuth token in storage.")
        return token.access_token
        
    if token and token.is_expired:
        logger.warning("⚠️ OAuth token expired. Refreshing not implemented in script (re-login via UI).")
        # Fallthrough to try Basic Auth
        
    # 2. Try Basic Auth (Env)
    email = os.getenv("ATLASSIAN_EMAIL")
    api_token = os.getenv("ATLASSIAN_API_TOKEN")
    
    if email and api_token:
        logger.info("✅ Found Basic Auth credentials in env.")
        creds = f"{email}:{api_token}"
        b64_creds = base64.b64encode(creds.encode()).decode()
        return f"Basic {b64_creds}"
        
    return None

async def verify_e2e():
    logger.info("🚀 Starting E2E Verification...")
    
    auth_token = get_auth_token()
    if not auth_token:
        logger.error("❌ No valid credentials found (OAuth or Basic Auth).")
        logger.error("Please log in via UI first OR set ATLASSIAN_EMAIL/ATLASSIAN_API_TOKEN.")
        sys.exit(1)
    
    # Initialize MCP Factory
    try:
        logger.info("🔌 Connecting to Atlassian MCP...")
        # Note: We create client first to ensure context manager handles cleanup
        async with await AtlassianMCPFactory.create_client(auth_token) as client:
            logger.info("✅ Connected to MCP Server.")
            
            # Fetch Tools
            logger.info("🛠️ Fetching available tools...")
            tools = await client.get_tools()
            logger.info("✅ Found %d tools.", len(tools))
            
            tool_names = [t.name for t in tools]
            logger.info("Tools: %s", tool_names)
            
            # Identify Key Tools
            jira_search = next((t for t in tools if "search" in t.name and "issue" in t.name), None)
            confluence_search = next((t for t in tools if "search" in t.name and "confluence" in t.name), None)
            
            # Verify Jira
            if jira_search:
                logger.info("🔎 Verifying Jira Search (%s)...", jira_search.name)
                try:
                    # Search for any issue created recently
                    result = await jira_search.ainvoke({"jql": "order by created DESC"})
                    # Result is likely a string or JSON string
                    snippet = str(result)[:200].replace("\n", " ")
                    logger.info("✅ Jira Result: %s...", snippet)
                except Exception as e:
                    logger.error("❌ Jira Search Failed: %s", str(e))
            else:
                logger.warning("⚠️ No Jira search tool found.")

            # Verify Confluence
            if confluence_search:
                logger.info("🔎 Verifying Confluence Search (%s)...", confluence_search.name)
                try:
                    result = await confluence_search.ainvoke({"query": "meeting"})
                    snippet = str(result)[:200].replace("\n", " ")
                    logger.info("✅ Confluence Result: %s...", snippet)
                except Exception as e:
                    logger.error("❌ Confluence Search Failed: %s", str(e))
            else:
                logger.warning("⚠️ No Confluence search tool found.")
                
    except Exception as e:
        logger.error("❌ MCP Connection Failed: %s", str(e))
        sys.exit(1)

    logger.info("🎉 E2E Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_e2e())
