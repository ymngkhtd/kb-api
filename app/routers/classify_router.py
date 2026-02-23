"""P.A.R.A. classification and file move routes."""

from fastapi import APIRouter, HTTPException, Depends

from app.auth.dependencies import require_permission
from app.models.user import User
from app.services.para_classifier import PARAClassifier
from app.services.file_service import FileService
from app.schemas.search import ClassifyRequest, ClassifySuggestion
from app.schemas.note import MoveRequest, ActionResult

router = APIRouter(prefix="/classify", tags=["Classification"])


@router.post("/suggest", response_model=list[ClassifySuggestion])
async def suggest_category(
    req: ClassifyRequest,
    user: User = Depends(require_permission("classify")),
):
    """Analyze content and suggest the best P.A.R.A. category."""
    classifier = PARAClassifier()
    results = classifier.classify(req.title, req.content)
    return [
        ClassifySuggestion(
            category=r.category,
            suggested_path=r.suggested_path,
            confidence=r.confidence,
            reason=r.reason,
        )
        for r in results
    ]


@router.post("/move", response_model=ActionResult)
async def move_note(
    req: MoveRequest,
    user: User = Depends(require_permission("write")),
):
    """Move a note to a new location (e.g., from Inbox to classified path)."""
    fs = FileService()
    try:
        result = fs.move_file(req.src, req.dst, user)
        return ActionResult(**result)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
