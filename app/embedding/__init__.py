"""Embedding provider factory with lazy singleton initialization."""

from app.config import get_settings
from app.embedding.base import EmbeddingProvider

_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get or create the configured embedding provider (singleton)."""
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.embedding_provider == "openai":
            from app.embedding.openai_provider import OpenAIEmbeddingProvider

            _provider = OpenAIEmbeddingProvider(
                api_key=settings.openai_api_key,
                model=settings.embedding_model,
                base_url=settings.openai_base_url,
            )
        else:
            from app.embedding.local_provider import LocalEmbeddingProvider

            _provider = LocalEmbeddingProvider(model_name=settings.embedding_model)
    return _provider
