"""Knowledge Base API — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()

    # Ensure data directories exist
    Path(settings.chroma_dir_path).mkdir(parents=True, exist_ok=True)
    Path(settings.log_dir_path).mkdir(parents=True, exist_ok=True)

    # Configure audit logger
    audit_logger = logging.getLogger("kb-api.audit")
    audit_handler = logging.FileHandler(
        Path(settings.log_dir_path) / "audit.log", encoding="utf-8"
    )
    audit_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(message)s")
    )
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)

    # General logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    logging.info(
        f"KB-API starting — root={settings.kb_root_path}, host={settings.host}:{settings.port}"
    )

    yield

    logging.info("KB-API shutting down")


app = FastAPI(
    title="Knowledge Base API",
    description=(
        "RESTful API for managing a P.A.R.A.-structured personal knowledge base. "
        "Supports CRUD, full-text search, semantic search, and intelligent classification."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# --- Include routers ---
from app.routers import auth_router, notes_router, search_router, classify_router  # noqa: E402

app.include_router(auth_router.router)
app.include_router(notes_router.router)
app.include_router(search_router.router)
app.include_router(classify_router.router)


@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "ok",
        "kb_root": str(settings.kb_root_path),
        "embedding_provider": settings.embedding_provider,
    }
