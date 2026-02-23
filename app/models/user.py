"""User model for authentication and authorization."""

from pydantic import BaseModel


class User(BaseModel):
    username: str
    password_hash: str
    role: str = "agent"  # "admin" | "agent"
    allowed_paths: list[str] = [""]  # relative to kb_root, "" = full access
    permissions: list[str] = ["read"]
