"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from kimidokku.config import get_settings
from kimidokku.database import init_database
from kimidokku.mcp_server import get_mcp_server
from kimidokku.middleware.rate_limiter import limiter
from kimidokku.routers import ui, webhooks
from fastapi.templating import Jinja2Templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_database()
    yield
    # Shutdown
    pass


async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "retry_after": exc.headers.get("Retry-After")},
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="KimiDokku MCP",
        description="MCP-First PaaS Platform for Dokku",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add rate limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
