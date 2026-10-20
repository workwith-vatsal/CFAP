import secrets
from datetime import datetime, timedelta, timezone

from backend.app.core.security import hash_password, verify_password


OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


def generate_otp() -> str:
    """
    Generate a cryptographically secure 6-digit OTP.
    """
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    """
    Hash the OTP before storing it in the database.
    """
    return hash_password(otp)


def verify_otp(otp: str, otp_hash: str) -> bool:
    """
    Verify a submitted OTP against its stored hash.
    """
    return verify_password(otp, otp_hash)


def get_otp_expiry() -> datetime:
    """
    Return the UTC expiration time for a newly generated OTP.
    """
    return datetime.now(timezone.utc) + timedelta(
        minutes=OTP_EXPIRY_MINUTES
    )


def is_otp_expired(expires_at: datetime) -> bool:
    """
    Check whether an OTP has expired.
    """
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) >= expires_at


def has_exceeded_attempts(attempts: int) -> bool:
    """
    Check whether the maximum number of verification attempts
    has been reached.
    """
    return attempts >= MAX_OTP_ATTEMPTS