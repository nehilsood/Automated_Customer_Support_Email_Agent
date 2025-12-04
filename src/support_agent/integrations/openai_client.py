"""OpenAI client for embeddings and chat completions."""

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from support_agent.config import get_settings


class OpenAIClient:
    """Client for OpenAI API interactions."""

    def __init__(self, api_key: str | None = None):
        """Initialize OpenAI client.

        Args:
            api_key: Optional API key (defaults to settings).
        """
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.settings = settings

    async def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        response = await self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        response = await self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict = "auto",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ChatCompletion:
        """Generate chat completion with optional tool calling.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model to use (defaults to simple_model from settings).
            tools: Optional list of tool definitions for function calling.
            tool_choice: How to select tools ('auto', 'none', 'required', or specific tool).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            ChatCompletion object from OpenAI.
        """
        if model is None:
            model = self.settings.simple_model

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        return await self.client.chat.completions.create(**kwargs)


# Backwards compatibility - module-level functions
settings = get_settings()
_default_client = None


def _get_default_client() -> OpenAIClient:
    """Get or create default client."""
    global _default_client
    if _default_client is None:
        _default_client = OpenAIClient()
    return _default_client


async def get_embedding(text: str) -> list[float]:
    """Generate embedding for a single text (backwards compatible)."""
    return await _get_default_client().get_embedding(text)


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts (backwards compatible)."""
    return await _get_default_client().get_embeddings(texts)


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict = "auto",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> dict:
    """Generate chat completion (backwards compatible - returns dict)."""
    response = await _get_default_client().chat_completion(
        messages=messages,
        model=model,
        tools=tools,
        tool_choice=tool_choice,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {
        "message": response.choices[0].message,
        "usage": {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
        "model": response.model,
        "finish_reason": response.choices[0].finish_reason,
    }
