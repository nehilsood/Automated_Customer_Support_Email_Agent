"""OpenAI client for embeddings and chat completions."""

from openai import AsyncOpenAI

from support_agent.config import get_settings

settings = get_settings()

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def get_embedding(text: str) -> list[float]:
    """Generate embedding for a single text.

    Args:
        text: Text to embed.

    Returns:
        List of floats representing the embedding vector.
    """
    response = await openai_client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return response.data[0].embedding


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in batch.

    Args:
        texts: List of texts to embed.

    Returns:
        List of embedding vectors.
    """
    response = await openai_client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict = "auto",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> dict:
    """Generate chat completion with optional tool calling.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        model: Model to use (defaults to simple_model from settings).
        tools: Optional list of tool definitions for function calling.
        tool_choice: How to select tools ('auto', 'none', 'required', or specific tool).
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in response.

    Returns:
        Dict containing the response message and usage info.
    """
    if model is None:
        model = settings.simple_model

    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    response = await openai_client.chat.completions.create(**kwargs)

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
