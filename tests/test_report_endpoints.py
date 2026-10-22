"""
Integration tests for Report API endpoints.
Verifies authentication, tenant isolation, invalid state guards, and PDF download functionality.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.report import Report, ReportStatus, ReportType
from backend.app.models.user import User
from backend.app.services.reporting.report_service import ReportService
from tests.test_report_data import _setup_test_analysis


def _get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}




def test_create_report_endpoint(client: TestClient, db_session: Session):
    user, dataset, analysis = _setup_test_analysis(db_session, "api_report_user@example.com")
    headers = _get_auth_headers(user)

    # 1. Unauthenticated request -> 401
    res = client.post("/api/v1/reports", json={"dataset_id": dataset.id, "analysis_id": analysis.id, "report_type": "FULL"})
    assert res.status_code == 401

    # 2. Valid report creation
    with patch("backend.app.api.v1.reports.generate_pdf_report.delay") as mock_delay:
        res = client.post(
            "/api/v1/reports",
            json={"dataset_id": dataset.id, "analysis_id": analysis.id, "report_type": "FULL"},
            headers=headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["dataset_id"] == dataset.id
        assert data["analysis_id"] == analysis.id
        assert data["status"] == "QUEUED"
        report_id = data["id"]
        mock_delay.assert_called_once_with(report_id)

    # 3. List reports
    res = client.get("/api/v1/reports", headers=headers)
    assert res.status_code == 200
    list_data = res.json()
    assert list_data["total"] >= 1
    assert any(r["id"] == report_id for r in list_data["items"])

    # 4. Get report by ID
    res = client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == report_id



def test_report_tenant_isolation(client: TestClient, db_session: Session):
    user_a, dataset_a, analysis_a = _setup_test_analysis(db_session, "user_a@example.com")
    user_b, dataset_b, analysis_b = _setup_test_analysis(db_session, "user_b@example.com")

    headers_a = _get_auth_headers(user_a)
    headers_b = _get_auth_headers(user_b)

    # User A creates a report
    report_a = ReportService.create_report(user_a, dataset_a.id, analysis_a.id, "EXECUTIVE", db_session)

    # User B attempts to access User A's report -> 404 Not Found
    res = client.get(f"/api/v1/reports/{report_a.id}", headers=headers_b)
    assert res.status_code == 404

    # User B attempts to download User A's report -> 404 Not Found
    res = client.get(f"/api/v1/reports/{report_a.id}/download", headers=headers_b)
    assert res.status_code == 404

    # User B attempts to delete User A's report -> 404 Not Found
    res = client.delete(f"/api/v1/reports/{report_a.id}", headers=headers_b)
    assert res.status_code == 404

    # User B attempts to generate report using User A's dataset -> 400 Bad Request
    res = client.post(
        "/api/v1/reports",
        json={"dataset_id": dataset_a.id, "analysis_id": analysis_a.id, "report_type": "FULL"},
        headers=headers_b,
    )
    assert res.status_code == 400


def test_report_incomplete_analysis_guard(client: TestClient, db_session: Session):
    user, dataset, _ = _setup_test_analysis(db_session, "incomplete_user@example.com")
    headers = _get_auth_headers(user)

    # Create analysis in PROCESSING state
    proc_analysis = Analysis(
        dataset_id=dataset.id,
        owner_id=user.id,
        status=AnalysisStatus.PROCESSING,
        progress=50,
    )
    db_session.add(proc_analysis)
    db_session.commit()
    db_session.refresh(proc_analysis)

    res = client.post(
        "/api/v1/reports",
        json={"dataset_id": dataset.id, "analysis_id": proc_analysis.id, "report_type": "FULL"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "must be completed" in res.json()["detail"].lower()


def test_report_download_and_delete(client: TestClient, db_session: Session):
    user, dataset, analysis = _setup_test_analysis(db_session, "download_user@example.com")
    headers = _get_auth_headers(user)

    # Generate and store report directly
    report = ReportService.create_report(user, dataset.id, analysis.id, "FULL", db_session)
    report_completed = ReportService.generate_and_store_report(report.id, db_session)
    assert report_completed.status == ReportStatus.COMPLETED

    # Download PDF
    res = client.get(f"/api/v1/reports/{report.id}/download", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF")

    # Delete Report
    del_res = client.delete(f"/api/v1/reports/{report.id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["id"] == report.id

    # Verify deleted
    get_res = client.get(f"/api/v1/reports/{report.id}", headers=headers)
    assert get_res.status_code == 404
