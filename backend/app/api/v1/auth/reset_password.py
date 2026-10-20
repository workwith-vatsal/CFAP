from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import MessageResponse, ResetPasswordRequest
from backend.app.services.otp_database import get_latest_valid_otp
from backend.app.services.otp_service import has_exceeded_attempts, verify_otp


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Reset the user's password using a valid password-reset OTP.
    """

    email = str(data.email).lower().strip()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset request.",
        )

    otp_record = get_latest_valid_otp(
        db=db,
        user_id=user.id,
        otp_type="password_reset",
    )

    if otp_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is invalid or expired. Please request a new password reset.",
        )

    if has_exceeded_attempts(otp_record.attempts):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum OTP attempts exceeded. Please request a new password reset.",
        )

    if not verify_otp(data.otp, otp_record.otp_hash):
        otp_record.attempts += 1
        db.commit()

        remaining = max(0, 5 - otp_record.attempts)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
        )

    # OTP is valid — update password.
    otp_record.is_used = True
    user.password_hash = hash_password(data.new_password)

    db.commit()

    return MessageResponse(
        message="Password has been reset successfully. You can now sign in.",
    )
