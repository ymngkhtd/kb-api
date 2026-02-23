"""Application configuration loaded from .env and environment variables."""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global settings. All env vars prefixed with KB_."""

    # Knowledge base root directory (defaults to parent of kb-api)
    kb_root: str = ""

    # JWT
    jwt_secret: str = "please-change-this-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Embedding
    embedding_provider: str = "local"  # "local" | "openai"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    openai_api_key: str = ""
    openai_base_url: str = ""

    # Git
    git_auto_commit: bool = False

    # Logging
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "KB_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def project_dir(self) -> Path:
        """The kb-api project directory."""
        return Path(__file__).resolve().parent.parent

    @property
    def kb_root_path(self) -> Path:
        """Resolved knowledge base root path."""
        if self.kb_root:
            return Path(self.kb_root).resolve()
        # Default: parent of kb-api directory
        return self.project_dir.parent.resolve()

    @property
    def users_config_path(self) -> Path:
        return self.project_dir / "config" / "users.yaml"

    @property
    def chroma_dir_path(self) -> Path:
        return self.project_dir / "data" / "chroma"

    @property
    def log_dir_path(self) -> Path:
        return self.project_dir / "logs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
