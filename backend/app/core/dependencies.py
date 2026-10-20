from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.security import decode_access_token
from backend.app.db.database import get_db
from backend.app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the token from either the Authorization Bearer header
    or the HttpOnly 'access_token' cookie, then return the authenticated user.
    Raises HTTP 401 on any failure.
    """
    token: str | None = None

    if credentials is not None and credentials.credentials:
        token = credentials.credentials
    elif request is not None and "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    return user


def get_current_active_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require both an active AND verified user.
    """

    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified.",
        )

    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_verified_user),
) -> User:
    """
    Require the authenticated user to have the 'admin' role.
    """

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user
