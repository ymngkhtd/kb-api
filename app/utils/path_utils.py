"""Path validation and security utilities.

All paths in the API are RELATIVE to the knowledge base root.
This module enforces:
  1. Path traversal prevention (no ../ escape)
  2. Symlink escape prevention
  3. Per-user allowed_paths whitelist (relative paths)
  4. System directory exclusion
"""

from pathlib import Path

# Directories excluded from all operations
EXCLUDED_DIRS = frozenset({
    "kb-api", ".git", ".obsidian", "node_modules",
    "__pycache__", ".trash", ".venv", "venv",
})


def normalize_rel_path(path: str) -> str:
    """Normalize a relative path: unify separators, strip slashes."""
    return path.replace("\\", "/").strip("/")


def is_excluded(rel_path: str) -> bool:
    """Check if any component of the path is in the exclusion list."""
    parts = Path(rel_path).parts
    return any(p in EXCLUDED_DIRS for p in parts)


def is_path_allowed(rel_path: str, allowed_paths: list[str]) -> bool:
    """Check if rel_path falls under any of the user's allowed paths.

    allowed_paths entries are relative to KB root.
    An empty string "" means full access to the entire knowledge base.
    """
    normalized = normalize_rel_path(rel_path)
    for ap in allowed_paths:
        ap_norm = normalize_rel_path(ap)
        if ap_norm == "":
            return True  # Full access
        if normalized == ap_norm or normalized.startswith(ap_norm + "/"):
            return True
    return False


def resolve_and_validate(
    relative_path: str,
    kb_root: Path,
    allowed_paths: list[str],
) -> Path:
    """Resolve a relative path against kb_root with full security checks.

    Returns the resolved absolute Path.
    Raises PermissionError on any violation.
    """
    normalized = normalize_rel_path(relative_path)
    kb_root_resolved = kb_root.resolve()

    # Resolve full path
    full_path = (kb_root_resolved / normalized).resolve()

    # 1. Traversal check: must remain under kb_root
    try:
        full_path.relative_to(kb_root_resolved)
    except ValueError:
        raise PermissionError("Path traversal detected")

    # 2. Exclusion check
    if normalized and is_excluded(normalized):
        raise PermissionError(f"Access to system directory is not allowed")

    # 3. Symlink escape check
    if full_path.is_symlink():
        real = full_path.resolve()
        try:
            real.relative_to(kb_root_resolved)
        except ValueError:
            raise PermissionError("Symlink target escapes knowledge base")

    # 4. User whitelist check
    rel_str = str(full_path.relative_to(kb_root_resolved)).replace("\\", "/")
    if not is_path_allowed(rel_str, allowed_paths):
        raise PermissionError("Access denied: path not in your allowed list")

    return full_path
