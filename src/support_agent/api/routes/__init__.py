"""API routes package."""

from .admin import router as admin_router
from .email import router as email_router
from .health import router as health_router

__all__ = ["health_router", "email_router", "admin_router"]
