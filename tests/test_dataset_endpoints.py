import io
import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.user import User


@pytest.fixture
def test_user_a(db_session: Session) -> User:
    user = User(
        first_name="Alice",
        last_name="Owner",
        email="alice.dataset@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_b(db_session: Session) -> User:
    user = User(
        first_name="Bob",
        last_name="Other",
        email="bob.dataset@example.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}


def test_upload_csv_dataset_success(client: TestClient, test_user_a: User):
    csv_content = (
        "Customer_Review,Rating,Date\n"
        "Amazing experience with fast response times!,5,2026-03-01\n"
        "Could improve documentation for developers.,3,2026-03-02\n"
        "Buggy checkout flow on mobile Safari.,1,2026-03-03\n"
    ).encode("utf-8")

    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(test_user_a),
        files={"file": ("feedback_march.csv", csv_content, "text/csv")},
        data={"name": "March Feedback"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "March Feedback"
    assert data["original_filename"] == "feedback_march.csv"
    assert data["file_type"] == "csv"
    assert data["row_count"] == 3
    assert data["column_count"] == 3
    assert data["status"] == "READY"
    assert data["feedback_column"] == "Customer_Review"
    assert data["quality_score"] is not None
    assert "quality_report" in data


def test_upload_xlsx_dataset_success(client: TestClient, test_user_a: User):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["review_text", "user_email", "rating"])
    ws.append(["Very happy with this SaaS platform", "user1@example.com", 5])
    ws.append(["Disappointed by the recent downtime", "user2@example.com", 2])

    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_bytes = excel_buffer.getvalue()

    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(test_user_a),
        files={
            "file": (
                "q1_reviews.xlsx",
                excel_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"name": "Q1 Excel Reviews"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Q1 Excel Reviews"
    assert data["file_type"] == "xlsx"
    assert data["row_count"] == 2
    assert data["status"] == "READY"


def test_upload_unsupported_file_format(client: TestClient, test_user_a: User):
    response = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(test_user_a),
        files={"file": ("malicious.exe", b"binary content", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "unsupported file format" in response.json()["detail"].lower()


def test_list_datasets_tenant_isolation(
    client: TestClient,
    test_user_a: User,
    test_user_b: User,
):
    # Upload for User A
    csv_a = b"Review,Rating\nGreat,5\n"
    client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(test_user_a),
        files={"file": ("user_a_data.csv", csv_a, "text/csv")},
        data={"name": "User A Dataset"},
    )

    # Upload for User B
    csv_b = b"Feedback,Rating\nBad,1\n"
    client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(test_user_b),
        files={"file": ("user_b_data.csv", csv_b, "text/csv")},
        data={"name": "User B Dataset"},
    )

    # List as User A
    res_a = client.get("/api/v1/datasets", headers=auth_headers(test_user_a))
    assert res_a.status_code == 200
    datasets_a = res_a.json()["datasets"]
    assert len(datasets_a) == 1
    assert datasets_a[0]["name"] == "User A Dataset"

    # List as User B
    res_b = client.get("/api/v1/datasets", headers=auth_headers(test_user_b))
    assert res_b.status_code == 200
    datasets_b = res_b.json()["datasets"]
    assert len(datasets_b) == 1
    assert datasets_b[0]["name"] == "User B Dataset"


def test_cross_user_access_blocked_anti_enumeration(
    client: TestClient,
    test_user_a: User,
    test_user_b: User,
):
    # User A uploads a dataset
    csv_a = b"Review,Score\nTop notch service,5\n"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(test_user_a),
        files={"file": ("secret_reviews.csv", csv_a, "text/csv")},
        data={"name": "Secret Dataset"},
    )
    dataset_id = upload_res.json()["id"]

    # User B attempts to GET User A's dataset -> 404 (anti-enumeration)
    get_res = client.get(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers(test_user_b),
    )
    assert get_res.status_code == 404

    # User B attempts to GET User A's quality report -> 404
    quality_res = client.get(
        f"/api/v1/datasets/{dataset_id}/quality",
        headers=auth_headers(test_user_b),
    )
    assert quality_res.status_code == 404

    # User B attempts to GET User A's preview -> 404
    preview_res = client.get(
        f"/api/v1/datasets/{dataset_id}/preview",
        headers=auth_headers(test_user_b),
    )
    assert preview_res.status_code == 404

    # User B attempts to PATCH User A's dataset -> 404
    patch_res = client.patch(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers(test_user_b),
        json={"name": "Hacked Name"},
    )
    assert patch_res.status_code == 404

    # User B attempts to ARCHIVE User A's dataset -> 404
    archive_res = client.post(
        f"/api/v1/datasets/{dataset_id}/archive",
        headers=auth_headers(test_user_b),
    )
    assert archive_res.status_code == 404

    # User B attempts to DELETE User A's dataset -> 404
    del_res = client.delete(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers(test_user_b),
    )
    assert del_res.status_code == 404


def test_dataset_lifecycle_rename_archive_restore_delete(
    client: TestClient,
    test_user_a: User,
):
    csv = b"Review,Rating\nSuperb software,5\n"
    upload_res = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers(test_user_a),
        files={"file": ("lifecycle.csv", csv, "text/csv")},
        data={"name": "Initial Name"},
    )
    dataset_id = upload_res.json()["id"]

    # 1. Rename
    rename_res = client.patch(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers(test_user_a),
        json={"name": "Updated Renamed Dataset"},
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["name"] == "Updated Renamed Dataset"

    # 2. Archive
    archive_res = client.post(
        f"/api/v1/datasets/{dataset_id}/archive",
        headers=auth_headers(test_user_a),
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "ARCHIVED"

    # Active list should not include archived by default
    list_active = client.get("/api/v1/datasets", headers=auth_headers(test_user_a))
    assert list_active.json()["total"] == 0

    # Include archived
    list_archived = client.get(
        "/api/v1/datasets?include_archived=true",
        headers=auth_headers(test_user_a),
    )
    assert list_archived.json()["total"] == 1

    # 3. Restore
    restore_res = client.post(
        f"/api/v1/datasets/{dataset_id}/restore",
        headers=auth_headers(test_user_a),
    )
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "READY"

    # 4. Preview
    preview_res = client.get(
        f"/api/v1/datasets/{dataset_id}/preview",
        headers=auth_headers(test_user_a),
    )
    assert preview_res.status_code == 200
    assert len(preview_res.json()["rows"]) == 1

    # 5. Delete
    delete_res = client.delete(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers(test_user_a),
    )
    assert delete_res.status_code == 200

    # Verify not found after deletion
    get_res = client.get(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers(test_user_a),
    )
    assert get_res.status_code == 404
