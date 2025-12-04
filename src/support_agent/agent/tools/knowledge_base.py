"""Knowledge base search tool for RAG retrieval."""

from sqlalchemy.ext.asyncio import AsyncSession

from support_agent.agent.tools.base import BaseTool, ToolResult
from support_agent.services.rag import RAGService


class SearchKnowledgeBaseTool(BaseTool):
    """Tool for searching the knowledge base using RAG."""

    name = "search_knowledge_base"
    description = (
        "Search the company knowledge base for FAQs, policies, product information, "
        "and shipping details. Use this tool to find accurate information before "
        "responding to customer queries about policies, returns, shipping, products, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant information",
            },
            "category": {
                "type": "string",
                "enum": ["faq", "policy", "product", "shipping"],
                "description": "Optional category to filter search results",
            },
        },
        "required": ["query"],
    }

    def __init__(self, db: AsyncSession):
        """Initialize with database session.

        Args:
            db: Async database session.
        """
        self.db = db
        self.rag_service = RAGService(db)

    async def execute(
        self, query: str, category: str | None = None, **kwargs
    ) -> ToolResult:
        """Search the knowledge base.

        Args:
            query: Search query text.
            category: Optional category filter.

        Returns:
            ToolResult with search results.
        """
        try:
            results = await self.rag_service.search_with_threshold(
                query=query,
                category=category,
            )

            if not results:
                return ToolResult(
                    success=True,
                    data={
                        "results": [],
                        "message": "No relevant information found in knowledge base.",
                    },
                )

            formatted_results = [
                {
                    "title": r.title or "Untitled",
                    "category": r.category,
                    "content": r.content,
                    "relevance_score": round(r.score, 3),
                }
                for r in results
            ]

            return ToolResult(
                success=True,
                data={
                    "results": formatted_results,
                    "count": len(formatted_results),
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Knowledge base search failed: {str(e)}",
            )
