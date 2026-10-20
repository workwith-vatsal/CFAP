import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User


@pytest.fixture
def benchmarking_fixture(db_session: Session):
    # 1. Create User A
    user_a = db_session.query(User).filter(User.email == "bench_a@example.com").first()
    if not user_a:
        user_a = User(
            email="bench_a@example.com",
            first_name="Alice",
            last_name="Analytics",
            password_hash=hash_password("ValidPassword123!"),
            role="user",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user_a)
        db_session.commit()
        db_session.refresh(user_a)

    # 2. Create User B
    user_b = db_session.query(User).filter(User.email == "bench_b@example.com").first()
    if not user_b:
        user_b = User(
            email="bench_b@example.com",
            first_name="Bob",
            last_name="Benchmark",
            password_hash=hash_password("ValidPassword123!"),
            role="user",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user_b)
        db_session.commit()
        db_session.refresh(user_b)

    # 3. Create Dataset & Completed Analysis for User A
    ds_a = db_session.query(Dataset).filter(Dataset.owner_id == user_a.id, Dataset.name == "User A Dataset").first()
    if not ds_a:
        ds_a = Dataset(
            owner_id=user_a.id,
            name="User A Dataset",
            original_filename="user_a.csv",
            storage_path="uploads/user_a.csv",
            file_type="csv",
            file_size_bytes=1024,
            row_count=100,
            quality_score=92.5,
            status=DatasetStatus.READY,
        )
        db_session.add(ds_a)
        db_session.commit()
        db_session.refresh(ds_a)

    an_a = db_session.query(Analysis).filter(Analysis.dataset_id == ds_a.id, Analysis.status == AnalysisStatus.COMPLETED).first()
    if not an_a:
        an_a = Analysis(
            dataset_id=ds_a.id,
            owner_id=user_a.id,
            status=AnalysisStatus.COMPLETED,
            progress=100,
            total_feedback_rows=100,
            usable_feedback_rows=100,
            sentiment_model="bert",
            emotion_model="distilroberta",
            embedding_model="minilm",
            bertopic_version="0.17.4",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(an_a)
        db_session.commit()
        db_session.refresh(an_a)

        # Seed feedback results for User A
        for idx in range(10):
            sent = "positive" if idx < 7 else ("neutral" if idx < 8 else "negative")
            emo = "joy" if idx < 6 else "anger"
            fr = FeedbackResult(
                analysis_id=an_a.id,
                row_index=idx,
                text_length=50,
                sentiment_label=sent,
                raw_sentiment_label="5 stars",
                sentiment_score=0.9,
                emotion_label=emo,
                emotion_score=0.85,
                topic_id=0,
                topic_label="0_onboarding",
                is_valid=True,
            )
            db_session.add(fr)
        db_session.commit()

    return user_a, user_b, ds_a, an_a


def test_benchmarking_unauthenticated_denied(client: TestClient, benchmarking_fixture):
    _, _, _, an_a = benchmarking_fixture
    res = client.get(f"/api/v1/benchmarks/summary?analysis_id={an_a.id}")
    assert res.status_code == 401


def test_benchmarking_cross_tenant_isolation(client: TestClient, benchmarking_fixture):
    _, user_b, _, an_a = benchmarking_fixture
    token_b = create_access_token(subject=str(user_b.id))
    headers = {"Authorization": f"Bearer {token_b}"}

    # User B tries to query User A's analysis
    res = client.get(f"/api/v1/benchmarks/summary?analysis_id={an_a.id}", headers=headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "Analysis not found or access denied."


def test_benchmarking_incomplete_analysis_rejected(client: TestClient, db_session: Session, benchmarking_fixture):
    user_a, _, ds_a, _ = benchmarking_fixture
    # Create an incomplete analysis for User A
    proc_an = Analysis(
        dataset_id=ds_a.id,
        owner_id=user_a.id,
        status=AnalysisStatus.PROCESSING,
        progress=45,
        total_feedback_rows=100,
        usable_feedback_rows=0,
    )
    db_session.add(proc_an)
    db_session.commit()
    db_session.refresh(proc_an)

    token_a = create_access_token(subject=str(user_a.id))
    headers = {"Authorization": f"Bearer {token_a}"}

    res = client.get(f"/api/v1/benchmarks/summary?analysis_id={proc_an.id}", headers=headers)
    assert res.status_code == 400
    assert "requires a completed analysis" in res.json()["detail"]


def test_benchmarking_summary_response_and_zero_pii_leakage(client: TestClient, benchmarking_fixture):
    user_a, _, _, an_a = benchmarking_fixture
    token_a = create_access_token(subject=str(user_a.id))
    headers = {"Authorization": f"Bearer {token_a}"}

    res = client.get(f"/api/v1/benchmarks/summary?analysis_id={an_a.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "is_eligible" in data
    assert "eligible_sample_size" in data
    assert "min_required_sample_size" in data
    assert "methodology" in data
    assert "privacy_notice" in data

    # Strict Privacy Checks:
    # 1. Zero other user emails or identities in payload
    raw_json = str(data)
    assert "bench_b@example.com" not in raw_json
    assert "Bob" not in raw_json
    assert "user_b.csv" not in raw_json

    # 2. Zero raw customer text in payload
    assert "raw_text" not in raw_json
    assert "customer_feedback" not in raw_json

    # 3. If eligible, verify non-causal observation language
    if data["is_eligible"] and data["net_sentiment_score"]:
        obs = data["net_sentiment_score"]["observation"]
        assert any(term in obs.lower() for term in ["observed", "matches", "compares", "points"])
        assert "caused" not in obs.lower()
        assert "guarantees" not in obs.lower()
