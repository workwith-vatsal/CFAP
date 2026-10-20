import logging
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.analysis import Analysis
from backend.app.models.dataset import Dataset
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.assistant.question_router import QuestionCategory

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Constructs focused, authoritative analytical context from Phase 4 and Phase 5 engines.
    Ensures zero dataset dumping: only retrieves the precise mathematical metrics
    and bounded excerpts needed to ground the answer.
    """

    @classmethod
    def build_context(
        cls,
        analysis: Analysis,
        current_user: User,
        db: Session,
        question: str,
        question_type: str,
    ) -> Dict[str, Any]:
        """
        Builds the minimal, authoritative context dictionary for the requested question type.
        """
        context: Dict[str, Any] = {
            "analysis_id": analysis.id,
            "dataset_id": analysis.dataset_id,
            "question_type": question_type,
            "sources": [],
        }

        # 1. Base overview summary (always provides total counts and sentiment distribution)
        overview = AnalyticsService.get_overview(analysis.id, current_user, db)
        context["overview"] = {
            "total_feedback": overview.get("total_feedback", 0),
            "usable_feedback": overview.get("usable_feedback", 0),
            "net_sentiment_score": overview.get("net_sentiment_score", 0.0),
            "sentiment_distribution": overview.get("sentiment_distribution", {}),
            "top_emotions": overview.get("top_emotions", [])[:5],
            "top_topics": overview.get("top_topics", [])[:5],
        }

        if question_type == QuestionCategory.UNSUPPORTED:
            context["supported"] = False
            return context

        if question_type == QuestionCategory.SENTIMENT:
            context["sources"].append({"type": "analytics", "label": "Sentiment Distribution & Net Sentiment Score"})

        elif question_type == QuestionCategory.EMOTION:
            context["emotions"] = overview.get("top_emotions", [])
            context["sources"].append({"type": "analytics", "label": "Emotion Analysis Distribution"})

        elif question_type == QuestionCategory.TOPIC:
            context["topics"] = overview.get("top_topics", [])
            context["sources"].append({"type": "analytics", "label": "BERTopic Discovery & Topic Metrics"})

        elif question_type == QuestionCategory.CROSS_DIMENSION:
            matrices = AnalyticsService.get_cross_matrices(analysis.id, current_user, db)
            context["cross_matrices"] = matrices
            context["sources"].append({"type": "analytics", "label": "Cross-Dimensional Matrices (Sentiment x Topic x Emotion)"})

        elif question_type == QuestionCategory.TREND:
            trends = AnalyticsService.get_temporal_trends(analysis.id, current_user, db)
            context["trends"] = trends
            context["sources"].append({"type": "analytics", "label": "Temporal Trend Analysis"})

        elif question_type == QuestionCategory.CATEGORY:
            breakdowns = AnalyticsService.get_categorical_breakdowns(analysis.id, current_user, db)
            context["categories"] = breakdowns
            context["sources"].append({"type": "analytics", "label": "Categorical Dimension Breakdown"})

        elif question_type == QuestionCategory.FEEDBACK_SEARCH:
            samples = cls._retrieve_bounded_feedback(analysis, db, question)
            context["feedback_samples"] = samples
            context["sources"].append({
                "type": "feedback_samples",
                "label": f"Representative Feedback Samples ({len(samples)} records)",
            })

        elif question_type == QuestionCategory.EXPLANATION:
            # Provide top explanation sample if present
            sample_exp = AnalyticsService.get_explainability_sample(analysis.id, current_user, db)
            context["explainability_sample"] = sample_exp
            context["sources"].append({"type": "explainability", "label": "SHAP Model Interpretability"})

        elif question_type == QuestionCategory.DATASET:
            dataset = db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
            if dataset:
                qr = dataset.quality_report or {}
                cols = list(qr.get("detected_columns", {}).keys()) if qr.get("detected_columns") else []
                context["dataset_info"] = {
                    "name": dataset.name,
                    "total_rows": dataset.total_rows,
                    "feedback_column": dataset.feedback_column,
                    "columns": cols,
                    "created_at": str(dataset.created_at),
                }
            context["sources"].append({"type": "dataset_metadata", "label": "Dataset Metadata & Schema"})

        else:  # OVERVIEW / GENERAL
            insights = AnalyticsService.get_insights(analysis.id, current_user, db)
            context["insights"] = {
                "health_score": insights.get("health_score", 50.0),
                "health_status": insights.get("health_status", "Moderate"),
                "summary": insights.get("summary", ""),
                "insights": insights.get("insights", []),
                "recommendations": insights.get("recommendations", []),
            }
            context["sources"].append({"type": "analytics", "label": "Executive Overview & Deterministic Insights"})

        return context

    @classmethod
    def _retrieve_bounded_feedback(
        cls,
        analysis: Analysis,
        db: Session,
        question: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a strictly bounded, sanitized sample of feedback results matching the user's intent.
        Never dumps the whole dataset. Maximum default 5 records.
        Reads text from source dataset file via storage service using row_index.
        """
        from backend.app.services.storage.local import LocalStorageService
        import os
        import pandas as pd

        max_samples = min(limit, settings.ai_assistant_max_feedback_samples or 5)
        query = db.query(FeedbackResult).filter(
            FeedbackResult.analysis_id == analysis.id,
            FeedbackResult.is_valid == True,
        )

        q_lower = question.lower()

        # Check for sentiment filtering
        if "negative" in q_lower or "complaint" in q_lower or "issue" in q_lower or "worst" in q_lower:
            query = query.filter(FeedbackResult.sentiment_label == "negative")
        elif "positive" in q_lower or "praise" in q_lower or "best" in q_lower:
            query = query.filter(FeedbackResult.sentiment_label == "positive")

        results = query.limit(max_samples).all()
        if not results:
            results = db.query(FeedbackResult).filter(
                FeedbackResult.analysis_id == analysis.id,
                FeedbackResult.is_valid == True,
            ).limit(max_samples).all()

        if not results:
            return []

        # Read row text from dataset file if accessible
        dataset = analysis.dataset or db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
        row_texts = {}
        if dataset and dataset.feedback_column:
            try:
                storage = LocalStorageService()
                file_path = storage.get_file_path(dataset.storage_path)
                if os.path.exists(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    f_col = dataset.feedback_column
                    if ext == ".csv":
                        df = pd.read_csv(file_path, usecols=[f_col])
                    else:
                        df = pd.read_excel(file_path, usecols=[f_col])
                    for r in results:
                        if 0 <= r.row_index < len(df):
                            row_texts[r.row_index] = str(df.iloc[r.row_index][f_col])
            except Exception as e:
                logger.warning(f"Unable to read feedback texts from file for assistant: {e}")

        samples = []
        for r in results:
            text = row_texts.get(r.row_index, f"Feedback record #{r.row_index + 1}")
            if len(text) > 250:
                text = text[:247] + "..."

            samples.append({
                "row_index": r.row_index,
                "text": text,
                "sentiment": r.sentiment_label,
                "emotion": r.emotion_label,
                "topic": r.topic_label or "General",
            })

        return samples
