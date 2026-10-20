"""
Unit tests for ReportDataBuilder.
Verifies data assembly, metric fidelity, data quality mapping, and assistant insight filtering.
"""

import pytest
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.assistant import AssistantConversation, AssistantMessage
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User
from backend.app.services.reporting.report_data import ReportDataBuilder


def _setup_test_analysis(db: Session, email: str = "report_test@example.com"):
    user = User(
        email=email,
        first_name="Report",
        last_name="Tester",
        password_hash=hash_password("ValidPass123!"),
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    dataset = Dataset(
        owner_id=user.id,
        name="Customer Experience Survey Q3",
        original_filename="cx_survey_q3.csv",
        storage_path="uploads/cx_survey_q3.csv",
        file_type="csv",
        file_size_bytes=4096,
        row_count=3,
        feedback_column="feedback_text",
        quality_score=92.5,
        quality_report={
            "detected_columns": {
                "feedback_text": {"role": "feedback", "type": "string", "missing_count": 0, "missing_pct": 0.0},
                "created_at": {"role": "date", "type": "datetime", "missing_count": 0, "missing_pct": 0.0},
                "product_tier": {"role": "category", "type": "string", "missing_count": 0, "missing_pct": 0.0},
            },
            "metrics": {
                "duplicate_rows_count": 0,
                "missing_feedback_count": 0,
            },
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
        sentiment_model="nlptown/bert-base-multilingual-uncased-sentiment",
        emotion_model="j-hartmann/emotion-english-distilroberta-base",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        bertopic_version="0.17.4",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Add sample feedback results
    f1 = FeedbackResult(
        analysis_id=analysis.id,
        row_index=0,
        text_length=45,
        sentiment_label="positive",
        raw_sentiment_label="5 stars",
        sentiment_score=0.95,
        emotion_label="joy",
        emotion_score=0.92,
        topic_id=0,
        topic_label="0_interface_fast_intuitive",
        is_valid=True,
    )
    f2 = FeedbackResult(
        analysis_id=analysis.id,
        row_index=1,
        text_length=52,
        sentiment_label="negative",
        raw_sentiment_label="1 star",
        sentiment_score=0.88,
        emotion_label="anger",
        emotion_score=0.85,
        topic_id=1,
        topic_label="1_support_slow_issue",
        is_valid=True,
    )
    f3 = FeedbackResult(
        analysis_id=analysis.id,
        row_index=2,
        text_length=38,
        sentiment_label="neutral",
        raw_sentiment_label="3 stars",
        sentiment_score=0.75,
        emotion_label="neutral",
        emotion_score=0.70,
        topic_id=0,
        topic_label="0_interface_fast_intuitive",
        is_valid=True,
    )
    db.add_all([f1, f2, f3])
    db.commit()


    # Add grounded assistant conversation
    conv = AssistantConversation(
        user_id=user.id,
        dataset_id=dataset.id,
        analysis_id=analysis.id,
        title="Report Q&A",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    m1 = AssistantMessage(
        conversation_id=conv.id,
        role="user",
        content="What is the net sentiment score?",
    )
    m2 = AssistantMessage(
        conversation_id=conv.id,
        role="assistant",
        content="The net sentiment score is 0.0 with 33.3% positive and 33.3% negative feedback.",
        is_grounded=True,
    )
    db.add_all([m1, m2])
    db.commit()

    return user, dataset, analysis


def test_build_report_data_full(db_session: Session):
    user, dataset, analysis = _setup_test_analysis(db_session, "full_report@example.com")

    data = ReportDataBuilder.build_report_data(
        analysis=analysis,
        dataset=dataset,
        current_user=user,
        db=db_session,
        report_type="full",
    )

    # 1. Metadata Checks
    assert data["metadata"]["dataset_name"] == "Customer Experience Survey Q3"
    assert data["metadata"]["usable_rows"] == 3
    assert data["metadata"]["report_type"] == "full"

    # 2. Executive Summary
    exec_s = data["executive_summary"]
    assert exec_s["usable_feedback"] == 3
    assert "brand_health_disclaimer" in exec_s
    assert "CFAP-derived composite" in exec_s["brand_health_disclaimer"]

    # 3. Data Quality
    dq = data["data_quality"]
    assert dq["quality_score"] == 92.5
    assert len(dq["columns"]) >= 3

    # 4. Methodology
    assert "nlptown" in data["methodology"]["sentiment_model"]

    # 5. Full Report Specific Sections
    assert "cross_matrices" in data
    assert "temporal_trends" in data
    assert "categorical_breakdowns" in data
    assert "explainability" in data
    assert "assistant_insights" in data

    # 6. Assistant Insights
    assert len(data["assistant_insights"]) == 1
    assert data["assistant_insights"][0]["question"] == "What is the net sentiment score?"


def test_build_report_data_executive(db_session: Session):
    user, dataset, analysis = _setup_test_analysis(db_session, "exec_report@example.com")

    data = ReportDataBuilder.build_report_data(
        analysis=analysis,
        dataset=dataset,
        current_user=user,
        db=db_session,
        report_type="executive",
    )

    assert data["metadata"]["report_type"] == "executive"
    assert "executive_summary" in data
    assert "data_quality" in data
    # Full-only sections should be omitted
    assert "cross_matrices" not in data
    assert "explainability" not in data
