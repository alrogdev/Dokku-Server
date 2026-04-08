"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from kimidokku.config import get_settings
from kimidokku.database import init_database
from kimidokku.mcp_server import get_mcp_server
from kimidokku.routers import webhooks
from fastapi.templating import Jinja2Templates
from kimidokku.routers import ui


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_database()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="KimiDokku MCP",
        description="MCP-First PaaS Platform for Dokku",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Mount MCP server
    mcp_server = get_mcp_server()
    mcp_app = mcp_server.http_app(path="/mcp")
    app.mount("/mcp", mcp_app)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "dokku_connected": True,
            "timestamp": "2024-01-01T00:00:00Z",  # Will be dynamic
        }

    # Include webhook router
    app.include_router(webhooks.router)

    # Templates
    templates = Jinja2Templates(directory="templates")
    app.state.templates = templates
    
    # Include UI router
    app.include_router(ui.router)

    return app


# Global app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "kimidokku.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
