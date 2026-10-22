import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User
from backend.app.services.audit_service import AuditService


def test_ip_hashing():
    assert AuditService.hash_ip(None) is None
    assert AuditService.hash_ip("") is None
    hash1 = AuditService.hash_ip("192.168.1.50")
    hash2 = AuditService.hash_ip("192.168.1.50")
    hash3 = AuditService.hash_ip("10.0.0.1")
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


def test_metadata_sanitization_strips_sensitive_data():
    raw_payload = {
        "password": "SuperSecretPassword123!",
        "password_hash": "$2b$12$eX4mpleH4sh...",
        "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
        "otp": "123456",
        "jwt": "ey...",
        "api_key": "AIzaSy...",
        "raw_text": "Customer raw complaint about delivery",
        "feedback_text": "Sensitive feedback text",
        "dataset_name": "Q4 Survey",
        "row_count": 500,
        "is_valid": True,
        "nested": {
            "token": "secret_token",
            "model": "bert",
        },
    }

    sanitized = AuditService.sanitize_metadata(raw_payload)

    # Disallowed keys must be stripped
    assert "password" not in sanitized
    assert "password_hash" not in sanitized
    assert "access_token" not in sanitized
    assert "otp" not in sanitized
    assert "jwt" not in sanitized
    assert "api_key" not in sanitized
    assert "raw_text" not in sanitized
    assert "feedback_text" not in sanitized

    # Allowed keys preserved
    assert sanitized["dataset_name"] == "Q4 Survey"
    assert sanitized["row_count"] == 500
    assert sanitized["is_valid"] is True
    assert "token" not in sanitized["nested"]
    assert sanitized["nested"]["model"] == "bert"


def test_audit_service_log_event(db_session: Session):
    log = AuditService.log_event(
        db=db_session,
        action="DATASET_CREATED",
        resource_type="dataset",
        resource_id="42",
        status="SUCCESS",
        ip_address="127.0.0.1",
        metadata={"filename": "test.csv", "format": "csv"},
    )

    assert log is not None
    assert log.action == "DATASET_CREATED"
    assert log.resource_type == "dataset"
    assert log.resource_id == "42"
    assert log.status == "SUCCESS"
    assert log.ip_hash is not None
    assert log.metadata_json["format"] == "csv"

    # Query from DB to verify persistence
    db_log = db_session.query(AuditLog).filter(AuditLog.id == log.id).first()
    assert db_log is not None
    assert db_log.action == "DATASET_CREATED"


def test_admin_query_audit_logs(client: TestClient, db_session: Session):
    admin_user = db_session.query(User).filter(User.role == "admin").first()
    if not admin_user:
        admin_user = User(
            email="audit_admin@example.com",
            first_name="Audit",
            last_name="Admin",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            is_active=True,
            is_verified=True,
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

    # Seed an audit log
    AuditService.log_event(
        db=db_session,
        action="TEST_ACTION_AUDIT",
        resource_type="test",
        user_id=admin_user.id,
        status="SUCCESS",
    )

    token = create_access_token(subject=str(admin_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/admin/audit-logs?action=TEST_ACTION_AUDIT", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["action"] == "TEST_ACTION_AUDIT"
