import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.dependencies import (
    get_current_user,
    get_current_active_verified_user,
    require_admin,
)
from backend.app.core.security import create_access_token, hash_password
from backend.app.models.user import User


def test_get_current_user_no_credentials(db_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail


def test_get_current_user_invalid_token(db_session: Session):
    creds = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid-token"
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Invalid or expired token" in exc_info.value.detail


def test_get_current_user_valid_token(db_session: Session):
    user = User(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(subject=str(user.id))
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    current_user = get_current_user(credentials=creds, db=db_session)
    assert current_user.id == user.id
    assert current_user.email == "alice@example.com"


def test_get_current_user_disabled_account(db_session: Session):
    user = User(
        first_name="Bob",
        last_name="Disabled",
        email="bob@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(subject=str(user.id))
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=creds, db=db_session)
    assert exc_info.value.status_code == 403
    assert "disabled" in exc_info.value.detail.lower()


def test_get_current_active_verified_user_unverified():
    user = User(
        first_name="Charlie",
        last_name="Unverified",
        email="charlie@example.com",
        is_active=True,
        is_verified=False,
    )
    with pytest.raises(HTTPException) as exc_info:
        get_current_active_verified_user(current_user=user)
    assert exc_info.value.status_code == 403
    assert "not verified" in exc_info.value.detail.lower()


def test_require_admin_non_admin():
    user = User(
        first_name="Regular",
        last_name="User",
        email="user@example.com",
        role="user",
        is_active=True,
        is_verified=True,
    )
    with pytest.raises(HTTPException) as exc_info:
        require_admin(current_user=user)
    assert exc_info.value.status_code == 403
    assert "Admin access required" in exc_info.value.detail


def test_require_admin_admin_user():
    admin = User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    result = require_admin(current_user=admin)
    assert result.role == "admin"
