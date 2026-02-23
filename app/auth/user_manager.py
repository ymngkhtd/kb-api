"""User management: load users from YAML, authenticate with bcrypt."""

import yaml
from passlib.context import CryptContext

from app.config import get_settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserManager:
    def __init__(self):
        self._users: dict[str, User] = {}
        self._load_users()

    def _load_users(self):
        config_path = get_settings().users_config_path
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for u in data.get("users", []):
            user = User(**u)
            self._users[user.username] = user

    def reload(self):
        """Hot-reload user configuration."""
        self._users.clear()
        self._load_users()

    def get_user(self, username: str) -> User | None:
        return self._users.get(username)

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.get_user(username)
        if user and pwd_context.verify(password, user.password_hash):
            return user
        return None

    def list_users(self) -> list[str]:
        return list(self._users.keys())


# Singleton
_manager: UserManager | None = None


def get_user_manager() -> UserManager:
    global _manager
    if _manager is None:
        _manager = UserManager()
    return _manager
