"""Full-text search service across knowledge base files."""

import re
from pathlib import Path

from app.config import get_settings
from app.models.user import User
from app.utils.path_utils import is_excluded, is_path_allowed, normalize_rel_path


class SearchService:
    def __init__(self):
        self.kb_root = get_settings().kb_root_path.resolve()

    def full_text_search(
        self,
        query: str,
        user: User,
        path: str = "",
        extensions: list[str] | None = None,
        max_results: int = 50,
        use_regex: bool = False,
    ) -> list[dict]:
        """Search file contents by text or regex pattern."""
        if extensions is None:
            extensions = [".md", ".txt"]

        # Determine search root
        search_root = self.kb_root
        if path:
            normalized = normalize_rel_path(path)
            candidate = (self.kb_root / normalized).resolve()
            try:
                candidate.relative_to(self.kb_root)
                if candidate.is_dir():
                    search_root = candidate
            except ValueError:
                pass

        # Compile pattern
        pattern = None
        if use_regex:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f"Invalid regex: {e}")
        query_lower = query.lower()

        results = []
        for file_path in search_root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue

            # Compute relative path
            try:
                rel = file_path.relative_to(self.kb_root)
            except ValueError:
                continue
            rel_str = str(rel).replace("\\", "/")

            # Skip excluded
            if is_excluded(rel_str):
                continue

            # Check user access
            if not is_path_allowed(rel_str, user.allowed_paths):
                continue

            # Read and search
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError, OSError):
                continue

            matches = []
            for i, line in enumerate(content.split("\n"), 1):
                matched = False
                if pattern:
                    matched = bool(pattern.search(line))
                else:
                    matched = query_lower in line.lower()

                if matched:
                    matches.append({"line": i, "text": line.strip()[:200]})

            if matches:
                results.append({
                    "path": rel_str,
                    "name": file_path.name,
                    "matches": matches[:10],  # limit per file
                    "match_count": len(matches),
                })
                if len(results) >= max_results:
                    break

        # Sort by match count descending
        results.sort(key=lambda x: x["match_count"], reverse=True)
        return results
