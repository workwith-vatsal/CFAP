import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.db.database import get_db
from backend.app.models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication — Google OAuth"],
)

# In-memory state store (acceptable for single-process dev;
# production should use Redis).
_oauth_states: set[str] = set()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@router.get("/google/login")
def google_login():
    """
    Redirect the user to Google's OAuth consent screen.
    """

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured.",
        )

    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
        "prompt": "consent",
    }

    return RedirectResponse(
        url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}",
    )


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Handle the Google OAuth callback.
    Exchanges the authorisation code for tokens, verifies the ID
    token, creates or locates the user, and redirects the frontend
    with a JWT access token.
    """

    # ---- Error / state validation ----
    if error:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=google_denied",
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=invalid_callback",
        )

    if state not in _oauth_states:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=invalid_state",
        )

    _oauth_states.discard(state)

    # ---- Exchange code for tokens ----
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

        if token_response.status_code != 200:
            return RedirectResponse(
                url=f"{settings.frontend_url}/auth/login?error=token_exchange_failed",
            )

        token_data = token_response.json()

    except Exception:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=token_exchange_failed",
        )

    # ---- Verify ID token ----
    raw_id_token = token_data.get("id_token")

    if not raw_id_token:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=no_id_token",
        )

    try:
        id_info = google_id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=invalid_id_token",
        )

    google_email = id_info.get("email", "").lower().strip()
    email_verified = id_info.get("email_verified", False)

    if not google_email or not email_verified:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=unverified_google_email",
        )

    # ---- Find or create user ----
    user = (
        db.query(User)
        .filter(User.email == google_email)
        .first()
    )

    if user is None:
        # New Google user — auto-create account.
        user = User(
            first_name=id_info.get("given_name", ""),
            last_name=id_info.get("family_name", ""),
            email=google_email,
            password_hash=None,
            auth_provider="google",
            role="user",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    elif user.auth_provider == "local":
        # Existing local user signing in with Google — link the account.
        user.auth_provider = "google"
        user.is_verified = True
        db.commit()

    elif not user.is_active:
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/login?error=account_disabled",
        )

    # ---- Issue JWT in secure HttpOnly cookie and redirect to frontend ----
    access_token = create_access_token(subject=str(user.id))

    redirect_response = RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback",
    )
    redirect_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    return redirect_response
