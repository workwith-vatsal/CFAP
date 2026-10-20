import io
import os
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.explainability_result import ExplainabilityResult
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User
from backend.app.services.ai.explainability import ExplainabilityService
from backend.app.services.analytics_service import AnalyticsService


def _setup_analysis_with_results(db: Session):
    user = User(
        email="bi_analyst@example.com",
        first_name="BI",
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
        name="Feedback 2026",
        original_filename="feedback.csv",
        storage_path="uploads/test_bi.csv",
        file_type="csv",
        file_size_bytes=1024,
        row_count=5,
        feedback_column="review_text",
        quality_score=98.0,
        quality_report={
            "detected_columns": {
                "review_text": {"role": "feedback", "type": "string"},
                "created_date": {"role": "date", "type": "datetime"},
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
        total_feedback_rows=5,
        usable_feedback_rows=5,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 5 feedback rows:
    # 0: Pos / Joy / Topic 1 (UI & UX)
    # 1: Pos / Joy / Topic 1 (UI & UX)
    # 2: Neu / Neutral / Topic 2 (Billing)
    # 3: Neg / Anger / Topic 2 (Billing)
    # 4: Neg / Anger / Topic 2 (Billing)
    rows_data = [
        ("positive", "5 stars", 0.95, "joy", 0.90, 1, "UI & UX"),
        ("positive", "4 stars", 0.85, "joy", 0.88, 1, "UI & UX"),
        ("neutral", "3 stars", 0.70, "neutral", 0.65, 2, "Billing"),
        ("negative", "1 star", 0.92, "anger", 0.85, 2, "Billing"),
        ("negative", "2 stars", 0.80, "anger", 0.78, 2, "Billing"),
    ]

    f_results = []
    for idx, (sent, r_sent, s_score, emo, e_score, t_id, t_label) in enumerate(rows_data):
        fr = FeedbackResult(
            analysis_id=analysis.id,
            row_index=idx,
            text_length=50,
            sentiment_label=sent,
            raw_sentiment_label=r_sent,
            sentiment_score=s_score,
            emotion_label=emo,
            emotion_score=e_score,
            topic_id=t_id,
            topic_label=t_label,
            is_valid=True,
        )
        db.add(fr)
        f_results.append(fr)

    db.commit()
    for fr in f_results:
        db.refresh(fr)

    return user, dataset, analysis, f_results


def test_analytics_overview_kpis(db_session: Session):
    user, dataset, analysis, f_results = _setup_analysis_with_results(db_session)

    overview = AnalyticsService.get_overview(analysis.id, user, db_session)

    assert overview["total_feedback"] == 5
    assert overview["usable_feedback"] == 5
    assert overview["sentiment_distribution"]["positive"]["count"] == 2
    assert overview["sentiment_distribution"]["neutral"]["count"] == 1
    assert overview["sentiment_distribution"]["negative"]["count"] == 2
    # Net Sentiment Score = (2 - 2) / 5 * 100 = 0.0
    assert overview["net_sentiment_score"] == 0.0
    assert overview["positive_ratio"] == 40.0
    assert len(overview["top_emotions"]) >= 3
    assert len(overview["top_topics"]) == 2


def test_analytics_deterministic_insights(db_session: Session):
    user, dataset, analysis, f_results = _setup_analysis_with_results(db_session)

    insights_data = AnalyticsService.get_insights(analysis.id, user, db_session)

    assert insights_data["health_score"] == 50.0
    assert insights_data["health_status"] == "Moderate"
    assert len(insights_data["insights"]) > 0

    types = [ins["type"] for ins in insights_data["insights"]]
    assert "positive_driver" in types or "friction_driver" in types or "emotion_tone" in types


def test_analytics_cross_matrices(db_session: Session):
    user, dataset, analysis, f_results = _setup_analysis_with_results(db_session)

    matrices = AnalyticsService.get_cross_matrices(analysis.id, user, db_session)

    # Sentiment x Emotion
    assert "sentiment_emotion" in matrices
    assert len(matrices["sentiment_emotion"]["rows"]) == 3

    # Sentiment x Topic
    assert "sentiment_topic" in matrices
    assert len(matrices["sentiment_topic"]["topics"]) == 2

    # Emotion x Topic
    assert "emotion_topic" in matrices
    assert len(matrices["emotion_topic"]["topics"]) == 2


def test_analytics_temporal_trends(db_session: Session):
    user, dataset, analysis, f_results = _setup_analysis_with_results(db_session)

    # Mock storage file read
    csv_content = (
        "review_text,created_date,channel\n"
        "Great UI,2026-01-01,Web\n"
        "Love the design,2026-01-02,Mobile\n"
        "Okay billing,2026-01-03,Web\n"
        "Horrible charges,2026-01-04,Web\n"
        "Charged twice,2026-01-05,Support\n"
    )

    with patch("backend.app.services.analytics_service.LocalStorageService") as mock_storage_cls:
        mock_storage = MagicMock()
        mock_storage.get_file_path.return_value = "fake_path.csv"
        mock_storage_cls.return_value = mock_storage

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({
                "created_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"]
            })

            trends = AnalyticsService.get_temporal_trends(analysis.id, user, db_session, interval="day")

            assert trends["available"] is True
            assert trends["date_column"] == "created_date"
            assert len(trends["timeline"]) == 5


def test_analytics_categorical_breakdowns(db_session: Session):
    user, dataset, analysis, f_results = _setup_analysis_with_results(db_session)

    with patch("backend.app.services.analytics_service.LocalStorageService") as mock_storage_cls:
        mock_storage = MagicMock()
        mock_storage.get_file_path.return_value = "fake_path.csv"
        mock_storage_cls.return_value = mock_storage

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({
                "channel": ["Web", "Mobile", "Web", "Web", "Support"]
            })

            breakdown = AnalyticsService.get_categorical_breakdowns(
                analysis.id, user, db_session, column_name="channel"
            )

            assert breakdown["available"] is True
            assert breakdown["active_column"] == "channel"
            assert len(breakdown["breakdown"]) == 3


def test_analytics_explain_feedback_row_and_caching(db_session: Session):
    user, dataset, analysis, f_results = _setup_analysis_with_results(db_session)
    target_fr = f_results[0]

    with patch("backend.app.services.analytics_service.LocalStorageService") as mock_storage_cls:
        mock_storage = MagicMock()
        mock_storage.get_file_path.return_value = "fake_path.csv"
        mock_storage_cls.return_value = mock_storage

        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({
                "review_text": ["Super clean interface!"] * 5
            })

            with patch.object(
                ExplainabilityService,
                "get_instance",
            ) as mock_explainer_get:
                mock_svc = MagicMock()
                mock_svc.explain_text.return_value = {
                    "predicted_label": "Positive",
                    "raw_predicted_label": "5 stars",
                    "confidence": 0.98,
                    "base_value": 0.15,
                    "token_contributions": [
                        {"token": "Super", "shap_value": 0.5, "position": 0, "importance": 0.5, "direction": "positive"},
                        {"token": "clean", "shap_value": 0.3, "position": 1, "importance": 0.3, "direction": "positive"},
                    ],
                    "positive_tokens": [{"token": "Super", "shap_value": 0.5, "position": 0, "importance": 0.5, "direction": "positive"}],
                    "negative_tokens": [],
                    "model_name": "nlptown/bert-base-multilingual-uncased-sentiment",
                    "explainer_name": "PartitionExplainer",
                    "sentiment_mapping": {
                        "raw_star_output": "5 stars",
                        "cfap_mapped_sentiment": "Positive",
                        "mapping_rule": "4★-5★ → Positive",
                        "explanation_basis": "Computed on raw output",
                    }
                }
                mock_explainer_get.return_value = mock_svc

                # 1. First invocation: calls explainer service and caches
                exp1 = AnalyticsService.explain_feedback_row(
                    analysis.id, target_fr.id, user, db_session
                )
                assert exp1["predicted_label"] == "Positive"
                assert exp1["is_cached"] is False

                # 2. Second invocation: retrieved from cache
                exp2 = AnalyticsService.explain_feedback_row(
                    analysis.id, target_fr.id, user, db_session
                )
                assert exp2["predicted_label"] == "Positive"
                assert exp2["is_cached"] is True

                # 3. Verify that adding another explainability result with different explainer_name does not violate unique constraints
                exp_alt = ExplainabilityResult(
                    analysis_id=analysis.id,
                    feedback_result_id=target_fr.id,
                    predicted_label="Positive",
                    raw_predicted_label="5 stars",
                    confidence=0.98,
                    base_value=0.15,
                    token_contributions=[],
                    model_name="nlptown/bert-base-multilingual-uncased-sentiment",
                    explainer_name="AlternativeExplainer",
                )
                db_session.add(exp_alt)
                db_session.commit()
                # Should commit without error since unique=True on feedback_result_id was removed
