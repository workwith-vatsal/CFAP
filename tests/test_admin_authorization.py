import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.user import User


@pytest.fixture
def admin_and_normal_users(db_session: Session):
    # Create Normal User
    normal_user = db_session.query(User).filter(User.email == "normal_user@example.com").first()
    if not normal_user:
        normal_user = User(
            email="normal_user@example.com",
            first_name="Normal",
            last_name="User",
            password_hash=hash_password("ValidPassword123!"),
            role="user",
            is_active=True,
            is_verified=True,
        )
        db_session.add(normal_user)
        db_session.commit()
        db_session.refresh(normal_user)

    # Create Admin User
    admin_user = db_session.query(User).filter(User.email == "admin_user@example.com").first()
    if not admin_user:
        admin_user = User(
            email="admin_user@example.com",
            first_name="System",
            last_name="Admin",
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

    # Create Target User for status toggling
    target_user = db_session.query(User).filter(User.email == "target_user@example.com").first()
    if not target_user:
        target_user = User(
            email="target_user@example.com",
            first_name="Target",
            last_name="Account",
            password_hash=hash_password("TargetPassword123!"),
            role="user",
            is_active=True,
            is_verified=True,
        )
        db_session.add(target_user)
        db_session.commit()
        db_session.refresh(target_user)

    return normal_user, admin_user, target_user


def test_normal_user_denied_from_all_admin_endpoints(client: TestClient, admin_and_normal_users):
    normal_user, _, _ = admin_and_normal_users
    token = create_access_token(subject=str(normal_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Overview
    res = client.get("/api/v1/admin/overview", headers=headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Admin access required."

    # 2. Users list
    res = client.get("/api/v1/admin/users", headers=headers)
    assert res.status_code == 403

    # 3. User status update
    res = client.patch("/api/v1/admin/users/1/status", json={"is_active": False}, headers=headers)
    assert res.status_code == 403

    # 4. Audit logs
    res = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert res.status_code == 403


def test_unauthenticated_denied_from_admin(client: TestClient, admin_and_normal_users):
    res = client.get("/api/v1/admin/overview")
    assert res.status_code == 401


def test_admin_user_access_overview(client: TestClient, admin_and_normal_users):
    _, admin_user, _ = admin_and_normal_users
    token = create_access_token(subject=str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/admin/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "total_datasets" in data
    assert "total_analyses" in data
    assert "total_reports" in data
    assert data["total_users"] >= 2
    assert data["database_connected"] is True


def test_admin_list_users_and_zero_credential_exposure(client: TestClient, admin_and_normal_users):
    _, admin_user, _ = admin_and_normal_users
    token = create_access_token(subject=str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/admin/users?limit=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 2

    for user_item in data["items"]:
        # Strict security test: zero password hash, token, or OTP in payload
        assert "password" not in user_item
        assert "password_hash" not in user_item
        assert "token" not in user_item
        assert "otp" not in user_item
        assert "email" in user_item
        assert "role" in user_item


def test_admin_toggle_user_status(client: TestClient, admin_and_normal_users):
    _, admin_user, target_user = admin_and_normal_users
    token = create_access_token(subject=str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Deactivate target user
    res = client.patch(
        f"/api/v1/admin/users/{target_user.id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Reactivate target user
    res = client.patch(
        f"/api/v1/admin/users/{target_user.id}/status",
        json={"is_active": True},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is True


def test_admin_self_deactivation_protection(client: TestClient, admin_and_normal_users):
    _, admin_user, _ = admin_and_normal_users
    token = create_access_token(subject=str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    # Admin attempts to deactivate themselves
    res = client.patch(
        f"/api/v1/admin/users/{admin_user.id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Administrators cannot deactivate their own account" in res.json()["detail"]
