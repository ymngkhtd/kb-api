"""Semantic search service using embeddings + ChromaDB vector store."""

import hashlib
import logging
from pathlib import Path

from app.config import get_settings
from app.embedding.base import EmbeddingProvider
from app.models.user import User
from app.utils.path_utils import is_excluded, is_path_allowed, normalize_rel_path

logger = logging.getLogger("kb-api.semantic")


class SemanticService:
    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider
        self.settings = get_settings()
        self.kb_root = self.settings.kb_root_path.resolve()
        self._collection = None
        self._init_db()

    def _init_db(self):
        import chromadb

        persist_dir = str(self.settings.chroma_dir_path)
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=persist_dir)
        self._collection = client.get_or_create_collection(
            name="kb_notes",
            metadata={"hnsw:space": "cosine"},
        )

    def index_all(self, extensions: list[str] | None = None) -> dict:
        """Build/rebuild the vector index for all files."""
        if extensions is None:
            extensions = [".md", ".txt"]

        indexed = 0
        skipped = 0
        chunks_total = 0

        for file_path in self.kb_root.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in extensions:
                continue

            try:
                rel = file_path.relative_to(self.kb_root)
            except ValueError:
                continue
            rel_str = str(rel).replace("\\", "/")

            if is_excluded(rel_str):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError, OSError):
                skipped += 1
                continue

            if not content.strip():
                skipped += 1
                continue

            doc_id = hashlib.md5(rel_str.encode()).hexdigest()
            chunks = self._chunk_text(content, max_chars=1000)

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                try:
                    embedding = self.provider.embed([chunk])[0]
                    self._collection.upsert(
                        ids=[chunk_id],
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{"path": rel_str, "chunk_index": i}],
                    )
                    chunks_total += 1
                except Exception as e:
                    logger.warning(f"Failed to embed chunk {chunk_id}: {e}")

            indexed += 1

        return {
            "indexed_files": indexed,
            "skipped_files": skipped,
            "total_chunks": chunks_total,
        }

    def search(
        self,
        query: str,
        user: User,
        top_k: int = 10,
        path_filter: str = "",
    ) -> list[dict]:
        """Semantic search: embed query, find similar chunks, filter by access."""
        embedding = self.provider.embed([query])[0]

        # Query more to allow for access filtering
        raw = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k * 5, 100),
        )

        results = []
        seen_paths = set()

        if raw and raw["metadatas"] and raw["metadatas"][0]:
            for meta, doc, dist in zip(
                raw["metadatas"][0],
                raw["documents"][0],
                raw["distances"][0],
            ):
                path = meta["path"]

                # Deduplicate by file path
                if path in seen_paths:
                    continue

                # Check user access
                if not is_path_allowed(path, user.allowed_paths):
                    continue

                # Apply optional path filter
                if path_filter:
                    pf = normalize_rel_path(path_filter)
                    if not (path == pf or path.startswith(pf + "/")):
                        continue

                seen_paths.add(path)
                results.append({
                    "path": path,
                    "snippet": doc[:500],
                    "score": round(1 - dist, 4),
                })

                if len(results) >= top_k:
                    break

        return results

    def _chunk_text(self, text: str, max_chars: int = 1000) -> list[str]:
        """Split text into chunks by paragraphs, respecting max size."""
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for p in paragraphs:
            if len(current) + len(p) + 2 > max_chars and current:
                chunks.append(current.strip())
                current = p
            else:
                current = current + "\n\n" + p if current else p

        if current.strip():
            chunks.append(current.strip())

        return chunks if chunks else [text[:max_chars]]
