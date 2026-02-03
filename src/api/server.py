from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import register_routes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages application startup and shutdown events.
    
    STARTUP (before yield):
        - Initialize database connections
        - Warm up LLM clients
        - Start background tasks
        
    SHUTDOWN (after yield):
        - Close database connections
        - Cancel background tasks
        - Flush logs/metrics
    
    Usage:
        The `yield` statement is like a pause point.
        Everything ABOVE yield runs at startup.
        Everything BELOW yield runs at shutdown.
    """
    # =========================================
    # STARTUP PHASE
    # =========================================
    print("🚀 Starting Atlassian Helper API...")
    
    # TODO: Initialize database connection pool
    # from src.persistence.checkpointer import get_async_checkpointer
    # app.state.checkpointer = await get_async_checkpointer()
    
    # TODO: Warm up LLM factory (optional - for faster first request)
    # from src.llm.factory import warm_up_providers
    # await warm_up_providers()
    
    print("✅ Startup complete. Ready to serve requests.")
    
    # -----------------------------------------
    # The yield passes control to the app.
    # App runs here, serving requests...
    # When shutdown is triggered, execution resumes below.
    # -----------------------------------------
    yield
    
    # =========================================
    # SHUTDOWN PHASE
    # =========================================
    print("🛑 Shutting down Atlassian Helper API...")
    
    # TODO: Close database connections
    # await app.state.checkpointer.close()
    
    # TODO: Cancel any background tasks
    # for task in app.state.background_tasks:
    #     task.cancel()
    
    print("👋 Shutdown complete. Goodbye!")


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    This is the "App Factory Pattern" - a function that creates
    and returns a fully configured FastAPI instance.
    
    Benefits:
        - Testing: Create fresh app instances per test
        - Config: Pass different settings for dev/test/prod
        - Modularity: Routes registered in separate modules
    
    Returns:
        Configured FastAPI instance ready to serve requests.
    """
    
    # -----------------------------------------
    # 1. Create the FastAPI app with lifespan manager
    # -----------------------------------------
    app = FastAPI(
        title="Atlassian Helper Agent",
        description="An Endpoint of AI agent for Jira/Trello/Confluence",
        version="0.1.0",
        docs_url="/docs",           # Swagger UI  (localhost:8000/docs)
        redoc_url="/redoc",         # ReDoc       (localhost:8000/redoc)
        openapi_url="/openapi.json",
        lifespan=lifespan,          # 👈 THIS registers our startup/shutdown
    )
    
    # -----------------------------------------
    # 2. Add Middleware (executes for EVERY request)
    # -----------------------------------------
    # CORS: Allow cross-origin requests (needed for Chainlit UI)
    #
    # === Security Note ===
    # In production, replace allow_origins=["*"] with:
    #   allow_origins=["https://your-ui-domain.com"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],        # ⚠️ Configure properly in production!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # -----------------------------------------
    # 3. Register Routes from separate module
    # -----------------------------------------
    # === MENTOR NOTE: Why separate routes? ===
    #
    # As your app grows, you'll have many endpoints:
    #   /agent/run, /agent/status, /health, /config, etc.
    #
    # Putting ALL routes in server.py makes it:
    #   - Hard to read (1000+ line file)
    #   - Hard to test (can't import routes without app)
    #   - Hard to organize (related routes scattered)
    #
    # Solution: Group routes in routes.py (or routes/ folder)
    # and register them here.
    #
    # === Go Comparison ===
    # Like splitting routes into handlers/ package:
    #   handlers.RegisterRoutes(router)
    #
    # === PHP Comparison ===
    # Like routes/api.php being loaded by RouteServiceProvider
    
    register_routes(app)
    
    return app


# =============================================================================
# APPLICATION INSTANCE
# =============================================================================
# This is the ASGI application that Uvicorn runs.
# Named 'app' by convention so uvicorn can find it:
#   uvicorn src.api.server:app

app = create_app()


# =============================================================================
# DEVELOPMENT ENTRY POINT
# =============================================================================
# Allows running directly with: python -m src.api.server

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only!)
    )
