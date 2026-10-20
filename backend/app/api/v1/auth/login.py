from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, verify_password
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from backend.app.services.audit_service import AuditService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    data: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate with email and password.
    Returns a JWT access token on success.
    """
    client_ip = request.client.host if request.client else None
    email = str(data.email).lower().strip()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Generic error — never reveal whether email or password was wrong.
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        AuditService.log_event(
            db=db,
            action="LOGIN_FAILURE",
            resource_type="auth",
            status="FAILURE",
            ip_address=client_ip,
            metadata={"email": email, "reason": "user_not_found"},
        )
        raise credentials_error

    # OAuth-only accounts cannot use password login.
    if user.auth_provider != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "This account uses external authentication. "
                "Please sign in with your authentication provider."
            ),
        )

    if user.password_hash is None:
        raise credentials_error

    if not verify_password(data.password, user.password_hash):
        AuditService.log_event(
            db=db,
            action="LOGIN_FAILURE",
            resource_type="auth",
            resource_id=str(user.id),
            user_id=user.id,
            status="FAILURE",
            ip_address=client_ip,
            metadata={"email": email, "reason": "invalid_password"},
        )
        raise credentials_error

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been disabled. Please contact support.",
        )

    access_token = create_access_token(subject=str(user.id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    AuditService.log_event(
        db=db,
        action="LOGIN_SUCCESS",
        resource_type="auth",
        resource_id=str(user.id),
        user_id=user.id,
        status="SUCCESS",
        ip_address=client_ip,
        metadata={"email": email, "auth_provider": "local"},
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
