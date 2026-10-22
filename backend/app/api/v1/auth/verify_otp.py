from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import VerifyOTPRequest
from backend.app.services.otp_database import get_latest_valid_otp
from backend.app.services.otp_service import (
    has_exceeded_attempts,
    verify_otp,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/verify-otp")
def verify_email_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    email = str(data.email).lower().strip()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified.",
        )

    otp_record = get_latest_valid_otp(
        db=db,
        user_id=user.id,
    )

    if otp_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is invalid or expired. Please request a new OTP.",
        )

    if has_exceeded_attempts(otp_record.attempts):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum OTP verification attempts exceeded. Please request a new OTP.",
        )

    if not verify_otp(
        data.otp,
        otp_record.otp_hash,
    ):
        otp_record.attempts += 1
        db.commit()

        remaining_attempts = max(
            0,
            5 - otp_record.attempts,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid OTP. "
                f"{remaining_attempts} attempt(s) remaining."
            ),
        )

    otp_record.is_used = True
    user.is_verified = True

    db.commit()
    db.refresh(user)

    return {
        "message": "Email verified successfully.",
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_verified": user.is_verified,
        },
    }