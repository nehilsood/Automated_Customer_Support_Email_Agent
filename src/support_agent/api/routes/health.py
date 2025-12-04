"""Health check endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.config import get_settings
from support_agent.integrations.database.connection import get_db

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str
    database: str


class RAGTestRequest(BaseModel):
    """Request model for RAG search test."""

    query: str
    category: str | None = None
    limit: int = 3


class RAGTestResponse(BaseModel):
    """Response model for RAG search test."""

    query: str
    results: list[dict]
    count: int


@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check application health including database connectivity."""
    settings = get_settings()

    # Test database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="0.1.0",
        environment=settings.environment.value,
        database=db_status,
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Kubernetes-style readiness probe."""
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get("/live")
async def liveness_check() -> dict:
    """Kubernetes-style liveness probe."""
    return {"alive": True}


@router.post("/test-rag", response_model=RAGTestResponse)
async def test_rag_search(
    request: RAGTestRequest,
    db: AsyncSession = Depends(get_db),
) -> RAGTestResponse:
    """Test RAG search functionality.

    This endpoint allows you to test the knowledge base search
    without going through the full agent pipeline.
    """
    from support_agent.services.rag import RAGService

    rag_service = RAGService(db)
    results = await rag_service.search(
        query=request.query,
        category=request.category,
        limit=request.limit,
    )

    return RAGTestResponse(
        query=request.query,
        results=[
            {
                "id": r.id,
                "title": r.title,
                "category": r.category,
                "score": round(r.score, 4),
                "content_preview": r.content[:200] + "..." if len(r.content) > 200 else r.content,
            }
            for r in results
        ],
        count=len(results),
    )
