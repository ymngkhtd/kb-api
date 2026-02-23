"""Abstract base class for embedding providers."""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts, return list of float vectors."""
        ...

    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding vector dimension."""
        ...
