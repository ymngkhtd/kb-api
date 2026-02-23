"""Note request/response schemas."""

from pydantic import BaseModel


class NoteContent(BaseModel):
    content: str


class CreateNoteRequest(BaseModel):
    content: str = ""
    is_directory: bool = False


class MoveRequest(BaseModel):
    src: str
    dst: str


class NoteInfo(BaseModel):
    name: str
    path: str
    type: str  # "file" | "directory"
    size: int | None = None
    modified: float | None = None


class NoteDetail(BaseModel):
    path: str
    content: str
    size: int
    modified: float


class ActionResult(BaseModel):
    path: str
    action: str
    archive_path: str | None = None
    src: str | None = None
    dst: str | None = None
