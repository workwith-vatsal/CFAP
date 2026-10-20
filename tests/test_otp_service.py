from datetime import datetime, timedelta, timezone
from backend.app.services.otp_service import (
    generate_otp,
    get_otp_expiry,
    has_exceeded_attempts,
    hash_otp,
    is_otp_expired,
    verify_otp,
)


def test_generate_otp_is_six_digits():
    for _ in range(20):
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()


def test_otp_hashing_and_verification():
    otp = "123456"
    hashed = hash_otp(otp)

    assert hashed != otp
    assert verify_otp("123456", hashed) is True
    assert verify_otp("654321", hashed) is False


def test_otp_expiry_calculation():
    expiry = get_otp_expiry()
    now = datetime.now(timezone.utc)
    diff = (expiry - now).total_seconds()

    # Should be approximately 600 seconds (10 minutes)
    assert 590 <= diff <= 610


def test_has_exceeded_attempts():
    assert has_exceeded_attempts(0) is False
    assert has_exceeded_attempts(4) is False
    assert has_exceeded_attempts(5) is True
    assert has_exceeded_attempts(6) is True


def test_is_otp_expired():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    assert is_otp_expired(future_time) is False
    assert is_otp_expired(past_time) is True
