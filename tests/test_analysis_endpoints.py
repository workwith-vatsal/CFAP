import io
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User
from backend.app.services.ai.embeddings import EmbeddingStorage
from backend.app.services.ai.emotion import EmotionResult
from backend.app.services.ai.sentiment import SentimentResult
from backend.app.services.ai.topics import TopicDiscoveryResult, TopicItem
from backend.app.tasks.analysis_tasks import execute_analysis_pipeline


def _create_verified_user(db: Session, email: str = "analyst@example.com") -> User:
    user = User(
        email=email,
        first_name="Analyst",
        last_name="User",
        password_hash=hash_password("ValidPass123!"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_sample_dataset(db: Session, user: User) -> Dataset:
    dataset = Dataset(
        owner_id=user.id,
        name="Customer Reviews 2026",
        original_filename="reviews.csv",
        storage_path="uploads/test_reviews.csv",
        file_type="csv",
        file_size_bytes=1024,
        row_count=3,
        column_count=2,
        feedback_column="feedback",
        quality_score=95.0,
        status=DatasetStatus.READY,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def test_execute_analysis_pipeline_success(db_session: Session):
    user = _create_verified_user(db_session, "pipeline_user@example.com")
    dataset = _create_sample_dataset(db_session, user)

    analysis = Analysis(
        dataset_id=dataset.id,
        owner_id=user.id,
        status=AnalysisStatus.QUEUED,
        progress=0,
        current_stage="INITIALIZED",
        total_feedback_rows=3,
        usable_feedback_rows=0,
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    csv_content = "customer_id,feedback\n1,Amazing application!\n2,Bad customer service.\n3,It is okay.\n".encode("utf-8")

    mock_sentiments = [
        SentimentResult(sentiment_label="positive", raw_sentiment_label="5 stars", sentiment_score=0.98),
        SentimentResult(sentiment_label="negative", raw_sentiment_label="1 star", sentiment_score=0.92),
        SentimentResult(sentiment_label="neutral", raw_sentiment_label="3 stars", sentiment_score=0.65),
    ]

    mock_emotions = [
        EmotionResult(emotion_label="joy", emotion_score=0.90, emotion_scores={"joy": 0.90, "anger": 0.01, "fear": 0.01, "neutral": 0.05, "sadness": 0.01, "surprise": 0.01, "disgust": 0.01}),
        EmotionResult(emotion_label="anger", emotion_score=0.85, emotion_scores={"joy": 0.01, "anger": 0.85, "fear": 0.02, "neutral": 0.05, "sadness": 0.05, "surprise": 0.01, "disgust": 0.01}),
        EmotionResult(emotion_label="neutral", emotion_score=0.75, emotion_scores={"joy": 0.05, "anger": 0.05, "fear": 0.05, "neutral": 0.75, "sadness": 0.05, "surprise": 0.03, "disgust": 0.02}),
    ]

    mock_embeddings = np.random.randn(3, 384).astype(np.float32)

    mock_topics = TopicDiscoveryResult(
        row_topics=[
            TopicItem(topic_id=0, topic_label="Topic 0: amazing, application"),
            TopicItem(topic_id=1, topic_label="Topic 1: bad, service"),
            TopicItem(topic_id=0, topic_label="Topic 0: amazing, application"),
        ],
        topic_info=[
            {"topic_id": 0, "name": "Topic 0: amazing, application", "count": 2, "percentage": 66.67, "keywords": []},
            {"topic_id": 1, "name": "Topic 1: bad, service", "count": 1, "percentage": 33.33, "keywords": []},
        ],
        total_topics=2,
        outlier_count=0,
        outlier_percentage=0.0,
    )

    with (
        patch("backend.app.tasks.analysis_tasks.LocalStorageService.get_file", return_value=csv_content),
        patch("backend.app.services.ai.sentiment.SentimentService.analyze_batch", return_value=mock_sentiments),
        patch("backend.app.services.ai.emotion.EmotionService.analyze_batch", return_value=mock_emotions),
        patch("backend.app.services.ai.embeddings.EmbeddingService.generate_embeddings", return_value=mock_embeddings),
        patch("backend.app.services.ai.topics.TopicService.discover_topics", return_value=mock_topics),
    ):
        success = execute_analysis_pipeline(analysis_id=analysis.id, db=db_session)
        assert success is True

    # Refresh analysis and verify
    db_session.refresh(analysis)
    assert analysis.status == AnalysisStatus.COMPLETED
    assert analysis.progress == 100
    assert analysis.current_stage == "COMPLETED"
    assert analysis.usable_feedback_rows == 3
    assert analysis.sentiment_summary is not None
    assert analysis.sentiment_summary["positive_count"] == 1
    assert analysis.sentiment_summary["negative_count"] == 1
    assert analysis.sentiment_summary["neutral_count"] == 1
    assert analysis.emotion_summary is not None
    assert analysis.topic_summary is not None

    # Verify FeedbackResult rows
    results = db_session.query(FeedbackResult).filter(FeedbackResult.analysis_id == analysis.id).all()
    assert len(results) == 3
    assert results[0].sentiment_label == "positive"
    assert results[0].raw_sentiment_label == "5 stars"
    assert results[0].emotion_label == "joy"
    assert results[0].topic_id == 0
    assert results[0].embedding is not None

    # Verify embedding deserialization from DB
    retrieved_emb = EmbeddingStorage.deserialize(results[0].embedding)
    assert retrieved_emb.shape == (384,)


def test_analysis_endpoints_lifecycle(client: TestClient, db_session: Session):
    user = _create_verified_user(db_session, "api_tester@example.com")
    dataset = _create_sample_dataset(db_session, user)
    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    with patch("backend.app.services.analysis_service.run_analysis_pipeline.delay") as mock_delay:
        # 1. Trigger analysis
        resp = client.post(f"/api/v1/datasets/{dataset.id}/analyze", headers=headers)
        assert resp.status_code == 202
        data = resp.json()
        assert data["dataset_id"] == dataset.id
        assert data["status"] == "QUEUED"
        analysis_id = data["id"]
        mock_delay.assert_called_once_with(analysis_id)

        # 2. Prevent concurrent analysis
        resp_conflict = client.post(f"/api/v1/datasets/{dataset.id}/analyze", headers=headers)
        assert resp_conflict.status_code == 409

        # 3. Get analysis details
        resp_detail = client.get(f"/api/v1/analyses/{analysis_id}", headers=headers)
        assert resp_detail.status_code == 200
        assert resp_detail.json()["id"] == analysis_id

        # 4. Get latest analysis for dataset
        resp_latest = client.get(f"/api/v1/datasets/{dataset.id}/analysis", headers=headers)
        assert resp_latest.status_code == 200
        assert resp_latest.json()["id"] == analysis_id

        # 5. List analyses for dataset
        resp_list = client.get(f"/api/v1/datasets/{dataset.id}/analyses", headers=headers)
        assert resp_list.status_code == 200
        assert len(resp_list.json()) >= 1

        # 6. Delete analysis
        resp_del = client.delete(f"/api/v1/analyses/{analysis_id}", headers=headers)
        assert resp_del.status_code == 200

        # 7. Verify 404 after deletion
        resp_after_del = client.get(f"/api/v1/analyses/{analysis_id}", headers=headers)
        assert resp_after_del.status_code == 404
