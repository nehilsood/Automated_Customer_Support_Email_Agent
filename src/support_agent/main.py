"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from support_agent.api.routes import admin_router, email_router, health_router
from support_agent.config import get_settings
from support_agent.integrations.database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    settings = get_settings()
    print(f"Starting Support Agent API ({settings.environment.value})...")

    # Initialize database tables (for development)
    if settings.debug:
        await init_db()
        print("Database initialized")

    yield

    # Shutdown
    print("Shutting down Support Agent API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Customer Support Email Agent",
        description="Automated customer support email agent with RAG and tool-based AI",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(email_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Customer Support Email Agent API",
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


# Create app instance
app = create_app()
