"""RAG (Retrieval Augmented Generation) service for knowledge base search."""

from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.config import get_settings
from support_agent.integrations.database.models import KnowledgeBase
from support_agent.services.embedding import EmbeddingService

settings = get_settings()


@dataclass
class RAGResult:
    """Result from RAG knowledge base search."""

    id: str
    content: str
    category: str
    title: str | None
    score: float
    metadata: dict


class RAGService:
    """Service for RAG-based knowledge base retrieval."""

    def __init__(self, db: AsyncSession):
        """Initialize RAG service.

        Args:
            db: Database session.
        """
        self.db = db
        self.embedding_service = EmbeddingService()

    async def search(
        self,
        query: str,
        category: str | None = None,
        limit: int | None = None,
    ) -> list[RAGResult]:
        """Search knowledge base using vector similarity.

        Args:
            query: Search query text.
            category: Optional category filter (faq, policy, product, shipping).
            limit: Maximum number of results (defaults to settings.rag_top_k).

        Returns:
            List of RAGResult objects sorted by similarity score.
        """
        if limit is None:
            limit = settings.rag_top_k

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_for_search(query)

        # Build vector similarity search query
        # Using cosine distance: 1 - cosine_distance gives similarity score
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        if category:
            sql = text("""
                SELECT
                    id,
                    content,
                    category,
                    title,
                    metadata,
                    1 - (embedding <=> CAST(:embedding AS vector)) as score
                FROM knowledge_base
                WHERE category = :category
                    AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """)
            result = await self.db.execute(
                sql, {"embedding": embedding_str, "category": category, "limit": limit}
            )
        else:
            sql = text("""
                SELECT
                    id,
                    content,
                    category,
                    title,
                    metadata,
                    1 - (embedding <=> CAST(:embedding AS vector)) as score
                FROM knowledge_base
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """)
            result = await self.db.execute(
                sql, {"embedding": embedding_str, "limit": limit}
            )
        rows = result.fetchall()

        return [
            RAGResult(
                id=str(row.id),
                content=row.content,
                category=row.category,
                title=row.title,
                score=float(row.score),
                metadata=row.metadata or {},
            )
            for row in rows
        ]

    async def search_with_threshold(
        self,
        query: str,
        category: str | None = None,
        threshold: float | None = None,
        limit: int | None = None,
    ) -> list[RAGResult]:
        """Search knowledge base with similarity threshold filtering.

        Args:
            query: Search query text.
            category: Optional category filter.
            threshold: Minimum similarity score (defaults to settings.rag_similarity_threshold).
            limit: Maximum number of results.

        Returns:
            List of RAGResult objects above the threshold.
        """
        if threshold is None:
            threshold = settings.rag_similarity_threshold

        results = await self.search(query, category=category, limit=limit)
        return [r for r in results if r.score >= threshold]

    async def get_by_id(self, kb_id: str) -> KnowledgeBase | None:
        """Get knowledge base entry by ID.

        Args:
            kb_id: Knowledge base entry ID.

        Returns:
            KnowledgeBase model or None if not found.
        """
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> list[KnowledgeBase]:
        """Get all knowledge base entries in a category.

        Args:
            category: Category name.

        Returns:
            List of KnowledgeBase models.
        """
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.category == category)
        )
        return list(result.scalars().all())
