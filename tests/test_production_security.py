import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.user import User


@pytest.fixture
def security_users(db_session: Session):
    u1 = db_session.query(User).filter(User.email == "sec_user1@example.com").first()
    if not u1:
        u1 = User(
            email="sec_user1@example.com",
            first_name="Sec",
            last_name="One",
            password_hash=hash_password("ValidPassword123!"),
            role="user",
            is_active=True,
            is_verified=True,
        )
        db_session.add(u1)
        db_session.commit()
        db_session.refresh(u1)

    u2 = db_session.query(User).filter(User.email == "sec_user2@example.com").first()
    if not u2:
        u2 = User(
            email="sec_user2@example.com",
            first_name="Sec",
            last_name="Two",
            password_hash=hash_password("ValidPassword123!"),
            role="user",
            is_active=True,
            is_verified=True,
        )
        db_session.add(u2)
        db_session.commit()
        db_session.refresh(u2)

    admin = db_session.query(User).filter(User.email == "sec_admin@example.com").first()
    if not admin:
        admin = User(
            email="sec_admin@example.com",
            first_name="Sec",
            last_name="Admin",
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

    return u1, u2, admin


def test_health_endpoints_zero_credentials_leak(client: TestClient):
    # 1. Root
    res = client.get("/")
    assert res.status_code == 200
    assert "password" not in str(res.json())
    assert "secret" not in str(res.json())

    # 2. Health
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # 3. Health DB
    res = client.get("/health/db")
    assert res.status_code == 200
    assert "password" not in str(res.json())


def test_unauthenticated_protected_routes_return_401(client: TestClient):
    protected_routes = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/datasets"),
        ("GET", "/api/v1/analyses/1"),
        ("GET", "/api/v1/reports"),
        ("GET", "/api/v1/benchmarks/summary?analysis_id=1"),
        ("GET", "/api/v1/assistant/conversations"),
        ("GET", "/api/v1/admin/overview"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/audit-logs"),
    ]

    for method, path in protected_routes:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path)
        assert res.status_code == 401, f"Route {path} did not return 401 when unauthenticated"


def test_idor_dataset_anti_enumeration(client: TestClient, security_users):
    u1, u2, _ = security_users
    token1 = create_access_token(subject=str(u1.id))
    headers = {"Authorization": f"Bearer {token1}"}

    # Requesting non-existent or other user's dataset ID returns 404 (anti-enumeration)
    res = client.get("/api/v1/datasets/999999", headers=headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_idor_analysis_anti_enumeration(client: TestClient, security_users):
    u1, u2, _ = security_users
    token1 = create_access_token(subject=str(u1.id))
    headers = {"Authorization": f"Bearer {token1}"}

    res = client.get("/api/v1/analyses/999999", headers=headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_idor_report_anti_enumeration(client: TestClient, security_users):
    u1, u2, _ = security_users
    token1 = create_access_token(subject=str(u1.id))
    headers = {"Authorization": f"Bearer {token1}"}

    res = client.get("/api/v1/reports/999999", headers=headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_idor_assistant_anti_enumeration(client: TestClient, security_users):
    u1, u2, _ = security_users
    token1 = create_access_token(subject=str(u1.id))
    headers = {"Authorization": f"Bearer {token1}"}

    res = client.get("/api/v1/assistant/conversations/999999", headers=headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
