from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User
from backend.app.services.ai.explainability import ExplainabilityService


def _create_user_and_analysis(db: Session, email: str = "api_analyst@example.com"):
    user = User(
        email=email,
        first_name="API",
        last_name="Analyst",
        password_hash=hash_password("ValidPass123!"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    dataset = Dataset(
        owner_id=user.id,
        name="API Dataset",
        original_filename="api_data.csv",
        storage_path="uploads/api_data.csv",
        file_type="csv",
        file_size_bytes=1024,
        row_count=3,
        feedback_column="feedback",
        quality_score=90.0,
        quality_report={
            "detected_columns": {
                "feedback": {"role": "feedback", "type": "string"},
                "date": {"role": "date", "type": "datetime"},
                "channel": {"role": "category", "type": "string"},
            }
        },
        status=DatasetStatus.READY,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    analysis = Analysis(
        dataset_id=dataset.id,
        owner_id=user.id,
        status=AnalysisStatus.COMPLETED,
        progress=100,
        total_feedback_rows=3,
        usable_feedback_rows=3,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    fr1 = FeedbackResult(
        analysis_id=analysis.id,
        row_index=0,
        text_length=30,
        sentiment_label="positive",
        raw_sentiment_label="5 stars",
        sentiment_score=0.95,
        emotion_label="joy",
        emotion_score=0.90,
        topic_id=1,
        topic_label="Usability",
        is_valid=True,
    )
    fr2 = FeedbackResult(
        analysis_id=analysis.id,
        row_index=1,
        text_length=30,
        sentiment_label="negative",
        raw_sentiment_label="1 star",
        sentiment_score=0.88,
        emotion_label="anger",
        emotion_score=0.85,
        topic_id=2,
        topic_label="Speed",
        is_valid=True,
    )
    db.add(fr1)
    db.add(fr2)
    db.commit()
    db.refresh(fr1)
    db.refresh(fr2)

    return user, dataset, analysis, [fr1, fr2]


def test_get_overview_endpoint_success(client: TestClient, db_session: Session):
    user, dataset, analysis, _ = _create_user_and_analysis(db_session)
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/v1/analyses/{analysis.id}/analytics/overview",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == analysis.id
    assert data["usable_feedback"] == 2
    assert "sentiment_distribution" in data
    assert "net_sentiment_score" in data


def test_get_insights_endpoint_success(client: TestClient, db_session: Session):
    user, dataset, analysis, _ = _create_user_and_analysis(db_session)
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/v1/analyses/{analysis.id}/analytics/insights",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "health_score" in data
    assert "health_status" in data
    assert "insights" in data
    assert "recommendations" in data


def test_get_cross_matrices_endpoint_success(client: TestClient, db_session: Session):
    user, dataset, analysis, _ = _create_user_and_analysis(db_session)
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/v1/analyses/{analysis.id}/analytics/cross-matrices",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "sentiment_emotion" in data
    assert "sentiment_topic" in data
    assert "emotion_topic" in data


def test_explain_endpoint_success(client: TestClient, db_session: Session):
    user, dataset, analysis, f_results = _create_user_and_analysis(db_session)
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}
    target_fr = f_results[0]

    with patch("backend.app.services.analytics_service.LocalStorageService") as mock_storage_cls:
        mock_storage = MagicMock()
        mock_storage.get_file_path.return_value = "fake.csv"
        mock_storage_cls.return_value = mock_storage

        with patch("pandas.read_csv") as mock_read:
            mock_read.return_value = pd.DataFrame({"feedback": ["Great tool!"] * 3})

            with patch.object(ExplainabilityService, "get_instance") as mock_explainer_get:
                mock_svc = MagicMock()
                mock_svc.explain_text.return_value = {
                    "predicted_label": "Positive",
                    "raw_predicted_label": "5 stars",
                    "confidence": 0.99,
                    "base_value": 0.10,
                    "token_contributions": [
                        {"token": "Great", "shap_value": 0.6, "position": 0, "importance": 0.6, "direction": "positive"}
                    ],
                    "positive_tokens": [{"token": "Great", "shap_value": 0.6, "position": 0, "importance": 0.6, "direction": "positive"}],
                    "negative_tokens": [],
                    "model_name": "nlptown/bert-base-multilingual-uncased-sentiment",
                    "explainer_name": "PartitionExplainer",
                    "sentiment_mapping": {
                        "raw_star_output": "5 stars",
                        "cfap_mapped_sentiment": "Positive",
                        "mapping_rule": "4★-5★ → Positive",
                        "explanation_basis": "SHAP basis",
                    }
                }
                mock_explainer_get.return_value = mock_svc

                response = client.get(
                    f"/api/v1/analyses/{analysis.id}/results/{target_fr.id}/explain",
                    headers=headers,
                )
                assert response.status_code == 200
                data = response.json()
                assert data["predicted_label"] == "Positive"
                assert data["raw_predicted_label"] == "5 stars"
                assert len(data["token_contributions"]) == 1


def test_analytics_endpoints_unauthorized_and_cross_tenant(client: TestClient, db_session: Session):
    user, dataset, analysis, f_results = _create_user_and_analysis(db_session)
    target_fr = f_results[0]

    # 1. No auth header -> 401
    resp_noauth = client.get(f"/api/v1/analyses/{analysis.id}/analytics/overview")
    assert resp_noauth.status_code == 401

    # 2. Other user -> 404 / 403
    other_user = User(
        email="stranger@example.com",
        first_name="Other",
        last_name="User",
        password_hash=hash_password("ValidPass123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    stranger_token = create_access_token(subject=str(other_user.id))
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    resp_stranger = client.get(
        f"/api/v1/analyses/{analysis.id}/analytics/overview",
        headers=stranger_headers,
    )
    assert resp_stranger.status_code == 404
