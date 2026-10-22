import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.otp import EmailOTP
from backend.app.models.user import User
from backend.app.services.otp_database import create_email_otp


# ---------------- Register Tests ----------------


def test_register_success(client: TestClient, db_session: Session):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "StrongPassword123!",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == "john.doe@example.com"
    assert data["user"]["is_verified"] is False

    # Check user in DB
    user = (
        db_session.query(User)
        .filter(User.email == "john.doe@example.com")
        .first()
    )
    assert user is not None
    assert user.is_verified is False


def test_register_duplicate_email(client: TestClient, db_session: Session):
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "password": "AnotherPassword123!",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_register_terms_not_accepted(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "NoTerms",
            "last_name": "User",
            "email": "noterms@example.com",
            "password": "StrongPassword123!",
            "terms_accepted": False,
        },
    )
    assert response.status_code == 400
    assert "terms" in response.json()["detail"].lower()


# ---------------- Verify OTP Tests ----------------


def test_verify_otp_success(client: TestClient, db_session: Session):
    user = User(
        first_name="Verify",
        last_name="Me",
        email="verify@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    otp = create_email_otp(
        db=db_session, user_id=user.id, otp_type="email_verification"
    )
    db_session.commit()

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "verify@example.com",
            "otp": otp,
        },
    )
    assert response.status_code == 200
    assert response.json()["user"]["is_verified"] is True

    # Verify user state in DB
    db_session.refresh(user)
    assert user.is_verified is True


def test_verify_otp_invalid_otp(client: TestClient, db_session: Session):
    user = User(
        first_name="Wrong",
        last_name="OTP",
        email="wrongotp@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    create_email_otp(
        db=db_session, user_id=user.id, otp_type="email_verification"
    )
    db_session.commit()

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": "wrongotp@example.com",
            "otp": "000000",
        },
    )
    assert response.status_code == 400
    assert "Invalid OTP" in response.json()["detail"]


# ---------------- Resend OTP Tests ----------------


def test_resend_otp_verified_user(client: TestClient, db_session: Session):
    user = User(
        first_name="Already",
        last_name="Verified",
        email="already@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "already@example.com"},
    )
    assert response.status_code == 400
    assert "already verified" in response.json()["detail"].lower()


# ---------------- Login Tests ----------------


def test_login_success(client: TestClient, db_session: Session):
    user = User(
        first_name="Login",
        last_name="User",
        email="login@example.com",
        password_hash=hash_password("CorrectPassword123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "CorrectPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@example.com"


def test_login_wrong_password(client: TestClient, db_session: Session):
    user = User(
        first_name="Login",
        last_name="User",
        email="loginwrong@example.com",
        password_hash=hash_password("CorrectPassword123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginwrong@example.com",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_unverified_email(client: TestClient, db_session: Session):
    user = User(
        first_name="Unverified",
        last_name="User",
        email="unverified@example.com",
        password_hash=hash_password("Password123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unverified@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 403
    assert "verify your email" in response.json()["detail"].lower()


def test_login_disabled_account(client: TestClient, db_session: Session):
    user = User(
        first_name="Disabled",
        last_name="User",
        email="disabled@example.com",
        password_hash=hash_password("Password123!"),
        auth_provider="local",
        role="user",
        is_active=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "disabled@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


# ---------------- /auth/me Tests ----------------


def test_get_me_authenticated(client: TestClient, db_session: Session):
    user = User(
        first_name="Me",
        last_name="Test",
        email="me@example.com",
        password_hash=hash_password("Password123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    # Log in to get token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]

    # Call /auth/me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert response.json()["first_name"] == "Me"


def test_get_me_unauthenticated(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


# ---------------- /auth/logout Tests ----------------


def test_logout(client: TestClient, db_session: Session):
    user = User(
        first_name="Logout",
        last_name="Test",
        email="logout@example.com",
        password_hash=hash_password("Password123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()


# ---------------- Forgot & Reset Password Tests ----------------


def test_forgot_password_generic_response(client: TestClient):
    # Non-existent user
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200
    assert "password reset code has been sent" in response.json()["message"]


def test_forgot_and_reset_password_flow(
    client: TestClient, db_session: Session
):
    user = User(
        first_name="Reset",
        last_name="Flow",
        email="resetflow@example.com",
        password_hash=hash_password("OldPassword123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 1. Request forgot password
    forgot_res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "resetflow@example.com"},
    )
    assert forgot_res.status_code == 200

    # 2. Extract OTP created for user
    otp_record = (
        db_session.query(EmailOTP)
        .filter(
            EmailOTP.user_id == user.id,
            EmailOTP.otp_type == "password_reset",
            EmailOTP.is_used.is_(False),
        )
        .first()
    )
    assert otp_record is not None

    # Reset with a known OTP created manually for testing
    otp = create_email_otp(
        db=db_session, user_id=user.id, otp_type="password_reset"
    )
    db_session.commit()

    # 3. Reset password
    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "resetflow@example.com",
            "otp": otp,
            "new_password": "BrandNewPassword123!",
        },
    )
    assert reset_res.status_code == 200
    assert "reset successfully" in reset_res.json()["message"]

    # 4. Sign in with old password (must fail)
    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "resetflow@example.com",
            "password": "OldPassword123!",
        },
    )
    assert old_login.status_code == 401

    # 5. Sign in with new password (must succeed)
    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "resetflow@example.com",
            "password": "BrandNewPassword123!",
        },
    )
    assert new_login.status_code == 200


# ---------------- Change Password Tests ----------------


def test_change_password_success(client: TestClient, db_session: Session):
    user = User(
        first_name="Change",
        last_name="Pass",
        email="changepass@example.com",
        password_hash=hash_password("OldPassword123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "OldPassword123!"},
    )
    token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword123!",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert change_res.status_code == 200
    assert "changed successfully" in change_res.json()["message"].lower()

    # Login with old password fails
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "OldPassword123!"},
    )
    assert old_login.status_code == 401

    # Login with new password succeeds
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "changepass@example.com", "password": "NewSecurePassword123!"},
    )
    assert new_login.status_code == 200


def test_change_password_wrong_current(client: TestClient, db_session: Session):
    user = User(
        first_name="Change",
        last_name="Pass",
        email="changepasswrong@example.com",
        password_hash=hash_password("OldPassword123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "changepasswrong@example.com", "password": "OldPassword123!"},
    )
    token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "IncorrectPassword!",
            "new_password": "NewSecurePassword123!",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert change_res.status_code == 400
    assert "incorrect" in change_res.json()["detail"].lower()


def test_change_password_same_password(client: TestClient, db_session: Session):
    user = User(
        first_name="Change",
        last_name="Pass",
        email="changepasssame@example.com",
        password_hash=hash_password("OldPassword123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "changepasssame@example.com", "password": "OldPassword123!"},
    )
    token = login_res.json()["access_token"]

    change_res = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "OldPassword123!",
            "new_password": "OldPassword123!",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert change_res.status_code == 400
    assert "different" in change_res.json()["detail"].lower()


# ---------------- Cookie Authentication Tests ----------------


def test_cookie_authentication_me_and_logout(client: TestClient, db_session: Session):
    user = User(
        first_name="Cookie",
        last_name="User",
        email="cookieuser@example.com",
        password_hash=hash_password("Password123!"),
        auth_provider="local",
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    # Login without manually passing token headers — client automatically receives cookie
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "cookieuser@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.cookies

    # /auth/me should work with the cookie alone
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "cookieuser@example.com"

    # Logout clears the cookie
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
