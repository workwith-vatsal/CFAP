from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.otp import EmailOTP
from backend.app.models.user import User
from backend.app.schemas.auth import ResendOTPRequest
from backend.app.services.email_service import send_otp_email
from backend.app.services.otp_database import create_email_otp


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


RESEND_COOLDOWN_SECONDS = 60


@router.post("/resend-otp")
def resend_otp(
    data: ResendOTPRequest,
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

    # Find the most recently created verification OTP.
    latest_otp = (
        db.query(EmailOTP)
        .filter(
            EmailOTP.user_id == user.id,
            EmailOTP.otp_type == "email_verification",
        )
        .order_by(EmailOTP.created_at.desc())
        .first()
    )

    if latest_otp is not None:
        created_at = latest_otp.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        elapsed_seconds = (
            datetime.now(timezone.utc) - created_at
        ).total_seconds()

        if elapsed_seconds < RESEND_COOLDOWN_SECONDS:
            remaining = int(
                RESEND_COOLDOWN_SECONDS - elapsed_seconds
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Please wait {remaining} second(s) "
                    "before requesting another OTP."
                ),
            )

    try:
        otp = create_email_otp(
            db=db,
            user_id=user.id,
        )

        send_otp_email(
            recipient_email=user.email,
            otp=otp,
        )

        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send a new OTP. Please try again later.",
        )

    return {
        "message": "A new verification OTP has been sent to your email."
    }