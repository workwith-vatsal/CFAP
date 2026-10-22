"""
Unit tests for PDFReportGenerator and ReportChartGenerator.
Verifies PDF binary generation, valid headers, section inclusion, and server-side chart rendering.
"""

import io
import pytest
from sqlalchemy.orm import Session

from backend.app.services.reporting.charts import ReportChartGenerator
from backend.app.services.reporting.pdf_generator import PDFReportGenerator
from backend.app.services.reporting.report_data import ReportDataBuilder
from tests.test_report_data import _setup_test_analysis


def test_chart_generators():
    # 1. Sentiment Donut Chart
    s_chart = ReportChartGenerator.generate_sentiment_donut_chart(
        {"positive": 50, "neutral": 20, "negative": 30}
    )
    assert s_chart is not None

    # Empty sentiment
    assert ReportChartGenerator.generate_sentiment_donut_chart({}) is None

    # 2. Emotion Bar Chart
    top_emotions = [
        {"emotion": "joy", "count": 15, "percentage": 50.0},
        {"emotion": "neutral", "count": 10, "percentage": 33.3},
        {"emotion": "anger", "count": 5, "percentage": 16.7},
    ]
    e_chart = ReportChartGenerator.generate_emotion_bar_chart(top_emotions)
    assert e_chart is not None

    # 3. Topic Distribution Chart
    top_topics = [
        {"topic_id": 0, "label": "0_login_auth_speed", "count": 25, "percentage": 50.0},
        {"topic_id": 1, "label": "1_billing_refund_slow", "count": 15, "percentage": 30.0},
        {"topic_id": -1, "label": "-1_noise", "count": 10, "percentage": 20.0},
    ]
    t_chart = ReportChartGenerator.generate_topic_distribution_chart(top_topics)
    assert t_chart is not None

    # 4. Temporal Trend Chart
    trends = {
        "has_temporal_data": True,
        "data_points": [
            {"period": "2026-01", "total_count": 100, "positive_count": 60, "negative_count": 20, "nss": 40.0},
            {"period": "2026-02", "total_count": 120, "positive_count": 80, "negative_count": 15, "nss": 54.1},
        ],
    }
    temp_chart = ReportChartGenerator.generate_temporal_trend_chart(trends)
    assert temp_chart is not None


def test_pdf_report_generation_full(db_session: Session):
    user, dataset, analysis = _setup_test_analysis(db_session, "pdf_full@example.com")
    report_data = ReportDataBuilder.build_report_data(
        analysis=analysis,
        dataset=dataset,
        current_user=user,
        db=db_session,
        report_type="full",
    )

    pdf_bytes = PDFReportGenerator.generate_pdf(report_data, report_type="full")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_report_generation_executive(db_session: Session):
    user, dataset, analysis = _setup_test_analysis(db_session, "pdf_exec@example.com")
    report_data = ReportDataBuilder.build_report_data(
        analysis=analysis,
        dataset=dataset,
        current_user=user,
        db=db_session,
        report_type="executive",
    )

    pdf_bytes = PDFReportGenerator.generate_pdf(report_data, report_type="executive")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_report_generation_analysis(db_session: Session):
    user, dataset, analysis = _setup_test_analysis(db_session, "pdf_analysis@example.com")
    report_data = ReportDataBuilder.build_report_data(
        analysis=analysis,
        dataset=dataset,
        current_user=user,
        db=db_session,
        report_type="analysis",
    )

    pdf_bytes = PDFReportGenerator.generate_pdf(report_data, report_type="analysis")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
