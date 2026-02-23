"""Local embedding provider using sentence-transformers.

Supports any HuggingFace model. Recommended multilingual models:
  - paraphrase-multilingual-MiniLM-L12-v2 (fast, 384d)
  - BAAI/bge-small-zh-v1.5 (Chinese-optimized, 512d)
  - BAAI/bge-m3 (multilingual, 1024d)
"""

from app.embedding.base import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def dimension(self) -> int:
        return self._dim
