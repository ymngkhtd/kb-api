"""File operations service with path sandboxing and audit logging."""

import shutil
import logging
import subprocess
from pathlib import Path

from app.config import get_settings
from app.models.user import User
from app.utils.path_utils import (
    resolve_and_validate,
    is_excluded,
    is_path_allowed,
    normalize_rel_path,
    EXCLUDED_DIRS,
)

logger = logging.getLogger("kb-api.audit")


class FileService:
    def __init__(self):
        self.settings = get_settings()
        self.kb_root = self.settings.kb_root_path

    def validate_path(self, relative_path: str, user: User) -> Path:
        """Resolve and validate a path against the user's allowed_paths."""
        return resolve_and_validate(
            relative_path, self.kb_root, user.allowed_paths
        )

    def list_directory(
        self, relative_path: str, user: User, recursive: bool = False
    ) -> list[dict]:
        """List contents of a directory, filtered by user access."""
        full = self.validate_path(relative_path or "", user)
        if not full.is_dir():
            raise FileNotFoundError(f"Directory not found: {relative_path}")

        items = []
        entries = full.rglob("*") if recursive else full.iterdir()
        kb_resolved = self.kb_root.resolve()

        for entry in sorted(entries):
            try:
                rel = entry.relative_to(kb_resolved)
            except ValueError:
                continue

            rel_str = str(rel).replace("\\", "/")

            # Skip excluded directories
            if is_excluded(rel_str):
                continue

            # Filter by user access
            if not is_path_allowed(rel_str, user.allowed_paths):
                continue

            stat = entry.stat()
            items.append({
                "name": entry.name,
                "path": rel_str,
                "type": "directory" if entry.is_dir() else "file",
                "size": stat.st_size if entry.is_file() else None,
                "modified": stat.st_mtime,
            })

        return items

    def read_file(self, relative_path: str, user: User) -> str:
        """Read a file's text content."""
        full = self.validate_path(relative_path, user)
        if not full.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return full.read_text(encoding="utf-8")

    def create_file(self, relative_path: str, content: str, user: User) -> dict:
        """Create a new file with content."""
        full = self.validate_path(relative_path, user)
        if full.exists():
            raise FileExistsError(f"Already exists: {relative_path}")

        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        logger.info(f"CREATE user={user.username} path={relative_path}")
        self._git_commit(f"Create {relative_path}", user.username)
        return {"path": relative_path, "action": "created"}

    def create_directory(self, relative_path: str, user: User) -> dict:
        """Create a new directory."""
        full = self.validate_path(relative_path, user)
        if full.exists():
            raise FileExistsError(f"Already exists: {relative_path}")

        full.mkdir(parents=True, exist_ok=True)
        logger.info(f"MKDIR user={user.username} path={relative_path}")
        return {"path": relative_path, "action": "directory_created"}

    def update_file(self, relative_path: str, content: str, user: User) -> dict:
        """Overwrite an existing file's content."""
        full = self.validate_path(relative_path, user)
        if not full.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")

        full.write_text(content, encoding="utf-8")
        logger.info(f"UPDATE user={user.username} path={relative_path}")
        self._git_commit(f"Update {relative_path}", user.username)
        return {"path": relative_path, "action": "updated"}

    def delete_file(
        self, relative_path: str, user: User, archive: bool = True
    ) -> dict:
        """Delete or archive a file/directory."""
        full = self.validate_path(relative_path, user)
        if not full.exists():
            raise FileNotFoundError(f"Not found: {relative_path}")

        if archive and full.is_file():
            # Move to 90_Archives instead of permanent delete
            archive_rel = f"90_Archives/99_Legacy_Resources/{relative_path}"
            archive_full = self.kb_root.resolve() / archive_rel
            archive_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(full), str(archive_full))
            archive_path = normalize_rel_path(archive_rel)
            logger.info(
                f"ARCHIVE user={user.username} path={relative_path} -> {archive_path}"
            )
            self._git_commit(f"Archive {relative_path}", user.username)
            return {
                "path": relative_path,
                "action": "archived",
                "archive_path": archive_path,
            }
        else:
            if full.is_dir():
                shutil.rmtree(full)
            else:
                full.unlink()
            logger.info(f"DELETE user={user.username} path={relative_path}")
            self._git_commit(f"Delete {relative_path}", user.username)
            return {"path": relative_path, "action": "deleted"}

    def move_file(self, src_path: str, dst_path: str, user: User) -> dict:
        """Move/rename a file or directory."""
        src = self.validate_path(src_path, user)
        dst = self.validate_path(dst_path, user)

        if not src.exists():
            raise FileNotFoundError(f"Source not found: {src_path}")
        if dst.exists():
            raise FileExistsError(f"Destination exists: {dst_path}")

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        logger.info(f"MOVE user={user.username} {src_path} -> {dst_path}")
        self._git_commit(f"Move {src_path} -> {dst_path}", user.username)
        return {"path": dst_path, "action": "moved", "src": src_path, "dst": dst_path}

    def get_stat(self, relative_path: str, user: User) -> dict:
        """Get file/directory metadata."""
        full = self.validate_path(relative_path, user)
        if not full.exists():
            raise FileNotFoundError(f"Not found: {relative_path}")
        stat = full.stat()
        return {
            "path": relative_path,
            "type": "directory" if full.is_dir() else "file",
            "size": stat.st_size if full.is_file() else None,
            "modified": stat.st_mtime,
        }

    def _git_commit(self, message: str, username: str):
        """Auto-commit changes if git integration is enabled."""
        if not self.settings.git_auto_commit:
            return
        try:
            cwd = str(self.kb_root)
            subprocess.run(
                ["git", "add", "-A"],
                cwd=cwd, capture_output=True, timeout=10,
            )
            subprocess.run(
                ["git", "commit", "-m", f"[kb-api:{username}] {message}"],
                cwd=cwd, capture_output=True, timeout=10,
            )
        except Exception as e:
            logger.warning(f"Git commit failed: {e}")
