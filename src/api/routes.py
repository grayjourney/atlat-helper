# =============================================================================
# API Routes - All endpoints registered here
# =============================================================================
"""
Routes are separated from server.py for:
    1. Readability: server.py stays focused on app setup
    2. Testability: Can test routes independently
    3. Organization: Group related endpoints together

=== Future Structure ===
As the app grows, you might split this into:
    routes/
    ├── __init__.py      # register_routes() orchestrator
    ├── health.py        # Health/system endpoints
    ├── agent.py         # Agent workflow endpoints
    └── config.py        # Runtime configuration endpoints

For now, we keep it simple with one routes.py file.

=== Go Comparison ===
Like handlers/handlers.go that groups all HTTP handlers,
then registers them with router.GET("/path", handler).

=== PHP Comparison ===
Like routes/api.php containing Route::get() definitions,
but here we receive the app and attach routes to it.
"""

from fastapi import FastAPI


def register_routes(app: FastAPI) -> None:
    """
    Register all API routes on the FastAPI app.
    
    This function is called by create_app() in server.py.
    It attaches all endpoints to the provided app instance.
    
    Args:
        app: The FastAPI application instance to register routes on.
    """
    
    # =========================================
    # SYSTEM ENDPOINTS
    # =========================================
    
    @app.get("/", tags=["System"])
    async def root():
        """
        Root endpoint with API information.
        
        Returns:
            API metadata and useful links.
        """
        return {
            "service": "Atlassian Helper Agent",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    
    @app.get("/health", tags=["System"])
    async def health_check():
        """
        Health check endpoint for container orchestration.
        
        This endpoint is called by:
            - Docker HEALTHCHECK (see docker-compose.yml)
            - Kubernetes liveness/readiness probes
            - Load balancer health checks
        
        MUST return 200 OK for the container to be considered healthy.
        
        Returns:
            Simple status response indicating the service is running.
        """
        return {"status": "healthy", "service": "atlat-api"}
    
    # =========================================
    # AGENT ENDPOINTS (Phase 3)
    # =========================================
    # These will be implemented in Phase 3:
    #
    # @app.post("/agent/run", tags=["Agent"])
    # async def run_agent(request: AgentRequest):
    #     """Invoke the agent supervisor graph."""
    #     pass
    #
    # @app.get("/agent/status/{thread_id}", tags=["Agent"])
    # async def get_status(thread_id: str):
    #     """Get the status of an agent conversation."""
    #     pass
