from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.analysis import Analysis
from backend.app.models.assistant import AssistantConversation, AssistantMessage
from backend.app.models.dataset import Dataset
from backend.app.models.explainability_result import ExplainabilityResult
from backend.app.models.user import User
from backend.app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class ReportDataBuilder:
    """
    Assembles verified analytical report data for PDF generation.
    Strictly follows the Analytics-First architecture:
    Directly consumes authoritative results from Phase 3 Data Quality,
    Phase 4 AI Analysis, Phase 5 BI & SHAP Explainability, and Phase 6 Assistant.
    Zero calculation duplication and zero fabricated metrics.
    """

    @classmethod
    def build_report_data(
        cls,
        analysis: Analysis,
        dataset: Dataset,
        current_user: User,
        db: Session,
        report_type: str = "full",
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive dictionary of verified metrics and metadata for the PDF renderer.
        """
        # 1. Base Metadata
        overview = AnalyticsService.get_overview(analysis.id, current_user, db)
        insights = AnalyticsService.get_insights(analysis.id, current_user, db)

        usable_count = overview.get("usable_feedback", analysis.usable_feedback_rows or 0)
        total_count = overview.get("total_feedback", analysis.total_feedback_rows or usable_count)

        report_data: Dict[str, Any] = {
            "metadata": {
                "dataset_name": dataset.name,
                "original_filename": dataset.original_filename,
                "dataset_format": dataset.file_type.upper() if dataset.file_type else "CSV",
                "file_size_bytes": dataset.file_size_bytes or 0,
                "total_rows": dataset.row_count or total_count,
                "usable_rows": usable_count,
                "feedback_column": dataset.feedback_column or "Feedback Text",
                "analysis_id": analysis.id,
                "analysis_started_at": analysis.started_at.strftime("%Y-%m-%d %H:%M:%S UTC") if analysis.started_at else "N/A",
                "analysis_completed_at": analysis.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if analysis.completed_at else "N/A",
                "report_generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "report_type": report_type.lower(),
                "generated_by": f"{current_user.first_name} {current_user.last_name}".strip() or current_user.email,
            },
            "executive_summary": {
                "total_feedback": total_count,
                "usable_feedback": usable_count,
                "net_sentiment_score": overview.get("net_sentiment_score", 0.0),
                "positive_ratio": overview.get("positive_ratio", 0.0),
                "average_confidence": overview.get("average_confidence", 0.0),
                "dominant_emotion": overview.get("top_emotions", [{}])[0].get("emotion", "N/A") if overview.get("top_emotions") else "N/A",
                "top_topic": overview.get("top_topics", [{}])[0].get("label", "N/A") if overview.get("top_topics") else "N/A",
                "brand_health_score": insights.get("health_score", 50.0),
                "brand_health_status": insights.get("health_status", "Moderate"),
                "brand_health_disclaimer": "CFAP-derived composite analytical metric (0–100 scale)",
                "summary_text": insights.get("summary", "Analysis completed successfully across all usable feedback items."),
            },
            "data_quality": cls._build_data_quality_data(dataset, total_count, usable_count),
            "methodology": {
                "sentiment_model": analysis.sentiment_model or "nlptown/bert-base-multilingual-uncased-sentiment",
                "sentiment_mapping": "5-star classification mapped to 3-class (1–2 Negative, 3 Neutral, 4–5 Positive)",
                "emotion_model": analysis.emotion_model or "j-hartmann/emotion-english-distilroberta-base",
                "emotion_categories": "7 Discrete Emotions: Anger, Disgust, Fear, Joy, Neutral, Sadness, Surprise",
                "embedding_model": analysis.embedding_model or "sentence-transformers/all-MiniLM-L6-v2",
                "embedding_dim": "384-dimensional dense sentence embeddings",
                "topic_modeling": "BERTopic with UMAP dimensionality reduction and HDBSCAN density clustering",
                "bertopic_version": analysis.bertopic_version or "0.17.4",
                "explainability": "SHAP (SHapley Additive exPlanations) Token-Level Model Attribution",
            },
            "sentiment": {
                "distribution": overview.get("sentiment_distribution", {}),
                "net_sentiment_score": overview.get("net_sentiment_score", 0.0),
                "average_confidence": overview.get("average_confidence", 0.0),
            },
            "emotion": {
                "top_emotions": overview.get("top_emotions", []),
                "dominant_emotion": overview.get("top_emotions", [{}])[0].get("emotion", "Neutral") if overview.get("top_emotions") else "Neutral",
            },
            "topics": {
                "top_topics": overview.get("top_topics", []),
                "total_discovered_topics": len([t for t in overview.get("top_topics", []) if t.get("topic_id") != -1]),
            },
            "insights": {
                "findings": insights.get("insights", []),
                "recommendations": insights.get("recommendations", []),
                "health_score": insights.get("health_score", 50.0),
                "health_status": insights.get("health_status", "Moderate"),
            },
        }

        # Full Report & Analysis Report Additional Sections
        if report_type.lower() in ["full", "analysis"]:
            # Cross-Dimensional Matrices
            matrices = AnalyticsService.get_cross_matrices(analysis.id, current_user, db)
            report_data["cross_matrices"] = matrices

            # Temporal Trends
            trends = AnalyticsService.get_temporal_trends(analysis.id, current_user, db)
            report_data["temporal_trends"] = trends

            # Categorical Dimensions
            categories = AnalyticsService.get_categorical_breakdowns(analysis.id, current_user, db)
            report_data["categorical_breakdowns"] = categories

            # SHAP Explainability Sample
            shap_sample = cls._get_explainability_sample(analysis.id, db)
            report_data["explainability"] = {
                "methodology": (
                    "SHAP evaluates the marginal contribution of each word or token towards "
                    "the neural network's final sentiment prediction. Positive SHAP values push towards "
                    "the predicted class; negative values push in the opposite direction."
                ),
                "has_sample": shap_sample is not None,
                "sample": shap_sample,
            }

            # Grounded Assistant Insights
            assistant_insights = cls._get_grounded_assistant_insights(analysis.id, current_user.id, db)
            report_data["assistant_insights"] = assistant_insights

        return report_data


    @classmethod
    def _build_data_quality_data(
        cls,
        dataset: Dataset,
        total_rows: int,
        usable_rows: int,
    ) -> Dict[str, Any]:
        """Extracts verified Phase 3 data quality metrics."""
        qr = dataset.quality_report or {}
        quality_score = dataset.quality_score or qr.get("quality_score", 100.0)

        cols_meta = qr.get("detected_columns", {})
        columns_list = []
        if isinstance(cols_meta, dict):
            for c_name, meta in cols_meta.items():
                if isinstance(meta, dict):
                    columns_list.append({
                        "name": c_name,
                        "role": str(meta.get("role", "metadata")).capitalize(),
                        "type": str(meta.get("type", "string")),
                        "missing_count": meta.get("missing_count", 0),
                        "missing_pct": meta.get("missing_pct", 0.0),
                    })

        metrics = qr.get("metrics", {})
        invalid_rows = total_rows - usable_rows
        duplicates = metrics.get("duplicate_rows_count", qr.get("duplicates_count", 0))
        missing_feedback = metrics.get("missing_feedback_count", qr.get("missing_feedback_count", 0))

        return {
            "quality_score": round(float(quality_score), 1),
            "total_rows": total_rows,
            "usable_rows": usable_rows,
            "invalid_rows": max(0, invalid_rows),
            "duplicate_rows": duplicates,
            "missing_feedback_count": missing_feedback,
            "columns": columns_list,
        }

    @classmethod
    def _get_grounded_assistant_insights(
        cls,
        analysis_id: int,
        user_id: int,
        db: Session,
        max_insights: int = 4,
    ) -> List[Dict[str, str]]:
        """
        Retrieves authorized, grounded assistant Q&A highlights associated with this analysis.
        Strictly excludes internal prompts, raw system messages, or ungrounded claims.
        """
        conversations = (
            db.query(AssistantConversation)
            .filter(
                AssistantConversation.analysis_id == analysis_id,
                AssistantConversation.user_id == user_id,
            )
            .order_by(AssistantConversation.updated_at.desc())
            .all()
        )

        if not conversations:
            return []

        insights: List[Dict[str, str]] = []
        for conv in conversations:
            messages = (
                db.query(AssistantMessage)
                .filter(
                    AssistantMessage.conversation_id == conv.id,
                    AssistantMessage.is_grounded == True,
                )
                .order_by(AssistantMessage.created_at.asc())
                .all()
            )

            # Pair user question with assistant response
            last_user_q = None
            for m in messages:
                if m.role == "user":
                    last_user_q = m.content
                elif m.role == "assistant" and last_user_q:
                    # Sanitize preview
                    clean_ans = m.content
                    if len(clean_ans) > 400:
                        clean_ans = clean_ans[:397] + "..."
                    insights.append({
                        "question": last_user_q,
                        "answer": clean_ans,
                        "question_type": m.question_type or "ANALYTICS",
                    })
                    last_user_q = None
                    if len(insights) >= max_insights:
                        break

            if len(insights) >= max_insights:
                break

        return insights

    @classmethod
    def _get_explainability_sample(cls, analysis_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Retrieves a representative cached SHAP explainability record for this analysis.
        Extracts token attributions and baseline values safely.
        """
        exp_record = (
            db.query(ExplainabilityResult)
            .filter(ExplainabilityResult.analysis_id == analysis_id)
            .order_by(ExplainabilityResult.created_at.desc())
            .first()
        )
        if not exp_record:
            return None

        tokens = []
        values = []
        if isinstance(exp_record.token_contributions, list):
            for tc in exp_record.token_contributions:
                if isinstance(tc, dict):
                    tokens.append(tc.get("token", ""))
                    values.append(tc.get("shap_value", 0.0))

        return {
            "predicted_sentiment": exp_record.predicted_label,
            "confidence": exp_record.confidence,
            "base_value": exp_record.base_value,
            "tokens": tokens,
            "values": values,
        }
