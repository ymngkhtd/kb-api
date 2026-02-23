"""Search routes: full-text and semantic search."""

from fastapi import APIRouter, HTTPException, Depends

from app.auth.dependencies import get_current_user, require_permission
from app.models.user import User
from app.services.search_service import SearchService
from app.services.semantic_service import SemanticService
from app.embedding import get_embedding_provider
from app.schemas.search import (
    SearchQuery, SemanticSearchQuery,
    SearchResult, SearchMatch, SemanticResult,
)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=list[SearchResult])
async def full_text_search(
    query: SearchQuery,
    user: User = Depends(require_permission("search")),
):
    """Full-text search across knowledge base files."""
    try:
        service = SearchService()
        results = service.full_text_search(
            query=query.q,
            user=user,
            path=query.path,
            extensions=query.extensions,
            max_results=query.max_results,
            use_regex=query.use_regex,
        )
        return [
            SearchResult(
                path=r["path"],
                name=r["name"],
                matches=[SearchMatch(**m) for m in r["matches"]],
                match_count=r["match_count"],
            )
            for r in results
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/semantic", response_model=list[SemanticResult])
async def semantic_search(
    query: SemanticSearchQuery,
    user: User = Depends(require_permission("search")),
):
    """Semantic search using embeddings. Requires vector index to be built first."""
    try:
        provider = get_embedding_provider()
        service = SemanticService(provider)
        results = service.search(
            query=query.query,
            user=user,
            top_k=query.top_k,
            path_filter=query.path,
        )
        return [SemanticResult(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search error: {e}")


@router.post("/index")
async def rebuild_index(user: User = Depends(get_current_user)):
    """Rebuild the semantic search vector index (admin only)."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    provider = get_embedding_provider()
    service = SemanticService(provider)
    result = service.index_all()
    return result
