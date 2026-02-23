"""OpenAI-compatible embedding provider.

Works with OpenAI API and any compatible endpoint (e.g. vLLM, Ollama, LiteLLM).
Set KB_OPENAI_BASE_URL for custom endpoints.
"""

from app.embedding.base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "",
    ):
        from openai import OpenAI

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self._model = model
        # Common dimensions
        self._dim = 1536 if "small" in model else 3072

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in response.data]

    def dimension(self) -> int:
        return self._dim
