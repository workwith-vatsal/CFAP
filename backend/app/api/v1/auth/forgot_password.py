from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import ForgotPasswordRequest, MessageResponse
from backend.app.services.email_service import send_password_reset_email
from backend.app.services.otp_database import create_email_otp


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# Generic response — NEVER reveal whether the email actually exists.
_GENERIC_RESPONSE = MessageResponse(
    message=(
        "If an account with that email exists, "
        "a password reset code has been sent."
    ),
)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset OTP.
    Always returns a generic success message to prevent email enumeration.
    """

    email = str(data.email).lower().strip()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Return the same generic response regardless — prevent enumeration.
    if user is None:
        return _GENERIC_RESPONSE

    if not user.is_verified:
        return _GENERIC_RESPONSE

    if not user.is_active:
        return _GENERIC_RESPONSE

    # Only local-auth accounts can reset passwords.
    if user.auth_provider != "local":
        return _GENERIC_RESPONSE

    try:
        otp = create_email_otp(
            db=db,
            user_id=user.id,
            otp_type="password_reset",
        )

        send_password_reset_email(
            recipient_email=user.email,
            otp=otp,
        )

        db.commit()

    except Exception:
        db.rollback()
        # Still return generic response — don't leak internal errors.
        return _GENERIC_RESPONSE

    return _GENERIC_RESPONSE
