"""Authentication routes: login, refresh, user info."""

from fastapi import APIRouter, HTTPException, Depends

from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserInfo
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.user_manager import get_user_manager
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate and receive JWT tokens."""
    user = get_user_manager().authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(
        access_token=create_access_token({"sub": user.username}),
        refresh_token=create_refresh_token({"sub": user.username}),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    """Refresh an expired access token using a valid refresh token."""
    try:
        payload = verify_token(req.refresh_token, token_type="refresh")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    username = payload.get("sub")
    user = get_user_manager().get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=create_access_token({"sub": username}),
        refresh_token=create_refresh_token({"sub": username}),
    )


@router.get("/me", response_model=UserInfo)
async def me(user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserInfo(
        username=user.username,
        role=user.role,
        allowed_paths=user.allowed_paths,
        permissions=user.permissions,
    )


@router.post("/reload-users", tags=["Admin"])
async def reload_users(user: User = Depends(get_current_user)):
    """Hot-reload users.yaml (admin only)."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    get_user_manager().reload()
    return {"status": "users reloaded"}
