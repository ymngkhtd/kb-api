"""Notes CRUD routes.

GET  /notes?path=&recursive=   → list directory
GET  /notes/{path}             → read file or list directory (auto-detect)
POST /notes/{path}             → create file or directory
PUT  /notes/{path}             → update file content
DELETE /notes/{path}?archive=  → delete or archive
"""

from fastapi import APIRouter, HTTPException, Depends

from app.auth.dependencies import require_permission
from app.models.user import User
from app.services.file_service import FileService
from app.schemas.note import (
    NoteInfo, NoteDetail, CreateNoteRequest,
    NoteContent, ActionResult,
)

router = APIRouter(prefix="/notes", tags=["Notes"])


def _fs() -> FileService:
    return FileService()


@router.get("", response_model=list[NoteInfo])
async def list_notes(
    path: str = "",
    recursive: bool = False,
    user: User = Depends(require_permission("read")),
):
    """List directory contents. Default: knowledge base root."""
    try:
        items = _fs().list_directory(path, user, recursive)
        return [NoteInfo(**item) for item in items]
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{path:path}")
async def get_note(
    path: str,
    user: User = Depends(require_permission("read")),
):
    """Read a file's content, or list a directory (auto-detected)."""
    fs = _fs()
    try:
        full = fs.validate_path(path, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if full.is_dir():
        items = fs.list_directory(path, user)
        return [NoteInfo(**item) for item in items]
    elif full.is_file():
        try:
            content = fs.read_file(path, user)
            stat = full.stat()
            return NoteDetail(
                path=path,
                content=content,
                size=stat.st_size,
                modified=stat.st_mtime,
            )
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail=f"Not found: {path}")


@router.post("/{path:path}", response_model=ActionResult)
async def create_note(
    path: str,
    req: CreateNoteRequest,
    user: User = Depends(require_permission("write")),
):
    """Create a new file or directory."""
    fs = _fs()
    try:
        if req.is_directory:
            result = fs.create_directory(path, user)
        else:
            result = fs.create_file(path, req.content, user)
        return ActionResult(**result)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{path:path}", response_model=ActionResult)
async def update_note(
    path: str,
    req: NoteContent,
    user: User = Depends(require_permission("write")),
):
    """Update an existing file's content."""
    try:
        result = _fs().update_file(path, req.content, user)
        return ActionResult(**result)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{path:path}", response_model=ActionResult)
async def delete_note(
    path: str,
    archive: bool = True,
    user: User = Depends(require_permission("delete")),
):
    """Delete a file. Default: archive to 90_Archives instead of permanent delete."""
    try:
        result = _fs().delete_file(path, user, archive)
        return ActionResult(**result)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
