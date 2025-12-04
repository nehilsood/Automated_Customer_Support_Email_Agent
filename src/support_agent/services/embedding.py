"""Embedding service for generating and managing text embeddings."""

from support_agent.integrations.openai_client import get_embedding, get_embeddings


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        return await get_embedding(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        return await get_embeddings(texts)

    async def embed_for_search(self, query: str) -> list[float]:
        """Generate embedding optimized for search query.

        Currently uses same embedding as regular text,
        but can be customized for query-specific preprocessing.

        Args:
            query: Search query text.

        Returns:
            Query embedding vector.
        """
        # Optionally preprocess query (e.g., add "query: " prefix for some models)
        return await get_embedding(query)
