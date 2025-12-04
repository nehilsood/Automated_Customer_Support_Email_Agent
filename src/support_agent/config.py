"""Application configuration using Pydantic Settings."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars not defined in model
    )

    # Application
    environment: Environment = Environment.LOCAL
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/support_agent"

    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # LLM Models for tiered routing
    classifier_model: str = "gpt-4o-mini"
    simple_model: str = "gpt-4o-mini"
    medium_model: str = "gpt-4o-mini"
    complex_model: str = "gpt-4o"

    # Shopify
    shopify_store_url: str = ""
    shopify_access_token: str = ""
    use_mock_shopify: bool = True

    # Gmail
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    use_mock_email: bool = True

    # Escalation
    slack_webhook_url: str = ""

    # RAG Settings
    rag_top_k: int = 3
    rag_similarity_threshold: float = 0.7

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
