"""Google OAuth2 login for teacher authentication."""

from datetime import datetime

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.models import User, LoginRecord

router = APIRouter()

oauth = OAuth()

if settings.google_oauth_enabled:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@router.get("/login")
async def login(request: Request):
    if not settings.google_oauth_enabled:
        return RedirectResponse(url="/teacher")
    redirect_uri = f"{settings.app_base_url}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request, session: Session = Depends(get_session)):
    if not settings.google_oauth_enabled:
        return RedirectResponse(url="/teacher")

    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        return RedirectResponse(url="/login?error=no_user_info")

    google_id = user_info["sub"]
    email = user_info.get("email", "")
    name = user_info.get("name", "")
    avatar = user_info.get("picture", "")

    # Find or create user
    user = session.exec(
        select(User).where(User.google_id == google_id)
    ).first()

    normalized_super_email = settings.super_user_email
    is_super_user = email.lower() == normalized_super_email

    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar,
            role="super_user" if is_super_user else "student",
        )
        session.add(user)
    else:
        user.email = email
        user.name = name
        user.avatar_url = avatar
        user.last_login = datetime.now()
        if is_super_user and user.role != "super_user":
            user.role = "super_user"
        session.add(user)

    session.commit()
    session.refresh(user)

    # Record login
    login_record = LoginRecord(
        user_id=user.id,
        email=email,
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    session.add(login_record)
    session.commit()

    # Save to session
    request.session["user_id"] = user.id
    request.session["user_name"] = user.name
    request.session["user_email"] = user.email
    request.session["user_avatar"] = user.avatar_url
    request.session["user_role"] = user.role

    if user.role in {"teacher", "super_user"}:
        return RedirectResponse(url="/teacher")
    return RedirectResponse(url="/")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


def get_current_user(request: Request) -> dict | None:
    """Get current user from session. Returns None if not logged in."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return {
        "id": user_id,
        "name": request.session.get("user_name", ""),
        "email": request.session.get("user_email", ""),
        "avatar": request.session.get("user_avatar", ""),
        "role": request.session.get("user_role", "student"),
    }


def require_teacher(request: Request, session: Session) -> dict:
    """Require teacher/super_user role to access teacher features."""
    user = get_current_user(request)
    if not user:
        raise _LoginRequired()

    db_user = session.get(User, user["id"])
    if not db_user:
        request.session.clear()
        raise _LoginRequired()

    request.session["user_role"] = db_user.role
    if db_user.role not in {"teacher", "super_user"}:
        raise _RoleRequired("/?error=teacher_required")

    user["role"] = db_user.role
    return user


def require_super_user(request: Request, session: Session) -> dict:
    """Require super_user role for account management features."""
    user = require_teacher(request, session)
    if user["role"] != "super_user":
        raise _RoleRequired("/teacher?error=super_user_required")
    return user


def require_login(request: Request) -> dict:
    """Dependency that requires login. Redirects to /login if not authenticated."""
    user = get_current_user(request)
    if not user:
        raise _LoginRequired()
    return user


class _LoginRequired(Exception):
    """Raised when login is required but user is not authenticated."""
    pass


class _RoleRequired(Exception):
    """Raised when role permission is required."""

    def __init__(self, redirect_url: str):
        self.redirect_url = redirect_url
