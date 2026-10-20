from datetime import timedelta
import time
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    raw_password = "SecurePassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_access_token_creation_and_decoding():
    subject = "42"
    token = create_access_token(subject=subject, expires_minutes=15)

    assert isinstance(token, str)
    decoded_subject = decode_access_token(token)
    assert decoded_subject == "42"


def test_expired_access_token_returns_none():
    subject = "42"
    # Create an immediately expired token (negative minutes)
    token = create_access_token(subject=subject, expires_minutes=-1)

    decoded = decode_access_token(token)
    assert decoded is None


def test_invalid_token_returns_none():
    invalid_token = "invalid.token.payload"
    assert decode_access_token(invalid_token) is None
