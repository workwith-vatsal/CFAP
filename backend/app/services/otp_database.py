from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.otp import EmailOTP
from backend.app.services.otp_service import (
    generate_otp,
    get_otp_expiry,
    hash_otp,
)


def create_email_otp(
    db: Session,
    user_id: int,
    otp_type: str = "email_verification",
) -> str:
    """
    Invalidate existing OTPs of the same type, generate a new OTP,
    and add the OTP record to the current transaction.
    """

    existing_otps = (
        db.query(EmailOTP)
        .filter(
            EmailOTP.user_id == user_id,
            EmailOTP.otp_type == otp_type,
            EmailOTP.is_used.is_(False),
        )
        .all()
    )

    for existing_otp in existing_otps:
        existing_otp.is_used = True

    otp = generate_otp()

    otp_record = EmailOTP(
        user_id=user_id,
        otp_type=otp_type,
        otp_hash=hash_otp(otp),
        expires_at=get_otp_expiry(),
        attempts=0,
        is_used=False,
    )

    db.add(otp_record)

    return otp


def get_latest_valid_otp(
    db: Session,
    user_id: int,
    otp_type: str = "email_verification",
) -> EmailOTP | None:
    """
    Return the latest unused, non-expired OTP of the given type.
    """

    otp_record = (
        db.query(EmailOTP)
        .filter(
            EmailOTP.user_id == user_id,
            EmailOTP.otp_type == otp_type,
            EmailOTP.is_used.is_(False),
        )
        .order_by(EmailOTP.created_at.desc())
        .first()
    )

    if otp_record is None:
        return None

    expires_at = otp_record.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) >= expires_at:
        return None

    return otp_record