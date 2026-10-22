import io
import logging
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
import numpy as np
import pandas as pd
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset
from backend.app.models.explainability_result import ExplainabilityResult
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User
from backend.app.services.ai.explainability import (
    RAW_STAR_TO_SENTIMENT,
    STAR_MAPPING_RULES,
    ExplainabilityService,
)
from backend.app.services.storage.local import LocalStorageService

logger = logging.getLogger(__name__)

# Standard emotions tracked in Phase 4
ALL_EMOTIONS = ["joy", "anger", "sadness", "surprise", "fear", "disgust", "neutral"]
ALL_SENTIMENTS = ["positive", "neutral", "negative"]


def _verify_analysis_ownership(
    analysis_id: int,
    current_user_id: int,
    db: Session,
) -> Analysis:
    """
    Verifies tenant isolation: ensures the analysis exists, belongs to the authenticated user,
    and has completed successfully.
    """
    analysis = (
        db.query(Analysis)
        .filter(
            Analysis.id == analysis_id,
            Analysis.owner_id == current_user_id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or access denied.",
        )

    if analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis is not completed (current status: {analysis.status}). Analytics are available only for completed analyses.",
        )

    return analysis


def _get_valid_feedback_results(analysis_id: int, db: Session) -> List[FeedbackResult]:
    """Retrieves all valid FeedbackResult rows for an analysis."""
    return (
        db.query(FeedbackResult)
        .filter(
            FeedbackResult.analysis_id == analysis_id,
            FeedbackResult.is_valid == True,
        )
        .order_by(FeedbackResult.row_index)
        .all()
    )


class AnalyticsService:
    """
    Advanced Business Intelligence & Deterministic Insights Service.
    Produces mathematical KPIs, cross-dimensional matrices, temporal trends,
    and on-demand SHAP explainability caching.
    """

    @staticmethod
    def get_overview(
        analysis_id: int,
        current_user: User,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Calculates executive KPIs: Net Sentiment Score (NSS), Sentiment distribution,
        dominant emotions, topic breakdowns, and confidence averages.
        """
        analysis = _verify_analysis_ownership(analysis_id, current_user.id, db)
        results = _get_valid_feedback_results(analysis_id, db)

        usable_count = len(results)
        total_count = analysis.total_feedback_rows or usable_count

        if usable_count == 0:
            return {
                "analysis_id": analysis.id,
                "total_feedback": total_count,
                "usable_feedback": 0,
                "sentiment_distribution": {
                    "positive": {"count": 0, "percentage": 0.0},
                    "neutral": {"count": 0, "percentage": 0.0},
                    "negative": {"count": 0, "percentage": 0.0},
                },
                "net_sentiment_score": 0.0,
                "positive_ratio": 0.0,
                "average_confidence": 0.0,
                "top_emotions": [],
                "top_topics": [],
            }

        # 1. Sentiment Distribution & Net Sentiment Score (NSS)
        sent_counts = Counter(
            (r.sentiment_label or "neutral").lower() for r in results
        )
        pos_c = sent_counts.get("positive", 0)
        neu_c = sent_counts.get("neutral", 0)
        neg_c = sent_counts.get("negative", 0)

        pos_pct = round((pos_c / usable_count) * 100, 1)
        neu_pct = round((neu_c / usable_count) * 100, 1)
        neg_pct = round((neg_c / usable_count) * 100, 1)

        # Net Sentiment Score = ((Positive - Negative) / Usable) * 100
        nss = round(((pos_c - neg_c) / usable_count) * 100, 1)
        positive_ratio = pos_pct

        # Average sentiment confidence
        valid_scores = [
            r.sentiment_score for r in results if r.sentiment_score is not None
        ]
        avg_confidence = (
            round(float(np.mean(valid_scores)), 4) if valid_scores else 0.0
        )

        # 2. Top Emotions
        emotion_counts = Counter(
            (r.emotion_label or "neutral").lower() for r in results
        )
        top_emotions = [
            {
                "emotion": emo,
                "count": count,
                "percentage": round((count / usable_count) * 100, 1),
            }
            for emo, count in emotion_counts.most_common()
        ]

        # 3. Top Topics Breakdown with Topic-Level NSS
        topic_groups = defaultdict(lambda: {"total": 0, "pos": 0, "neg": 0, "neu": 0, "label": "Unknown"})
        for r in results:
            t_id = r.topic_id if r.topic_id is not None else -1
            t_label = r.topic_label or "Outliers & General"
            topic_groups[t_id]["total"] += 1
            topic_groups[t_id]["label"] = t_label
            s_label = (r.sentiment_label or "neutral").lower()
            if s_label == "positive":
                topic_groups[t_id]["pos"] += 1
            elif s_label == "negative":
                topic_groups[t_id]["neg"] += 1
            else:
                topic_groups[t_id]["neu"] += 1

        top_topics = []
        for t_id, t_data in sorted(
            topic_groups.items(), key=lambda x: x[1]["total"], reverse=True
        ):
            t_tot = t_data["total"]
            t_nss = (
                round(((t_data["pos"] - t_data["neg"]) / t_tot) * 100, 1)
                if t_tot > 0
                else 0.0
            )
            top_topics.append({
                "topic_id": t_id,
                "label": t_data["label"],
                "count": t_tot,
                "percentage": round((t_tot / usable_count) * 100, 1),
                "positive_count": t_data["pos"],
                "negative_count": t_data["neg"],
                "neutral_count": t_data["neu"],
                "net_sentiment_score": t_nss,
            })

        return {
            "analysis_id": analysis.id,
            "total_feedback": total_count,
            "usable_feedback": usable_count,
            "sentiment_distribution": {
                "positive": {"count": pos_c, "percentage": pos_pct},
                "neutral": {"count": neu_c, "percentage": neu_pct},
                "negative": {"count": neg_c, "percentage": neg_pct},
            },
            "net_sentiment_score": nss,
            "positive_ratio": positive_ratio,
            "average_confidence": avg_confidence,
            "top_emotions": top_emotions,
            "top_topics": top_topics,
        }

    @staticmethod
    def get_insights(
        analysis_id: int,
        current_user: User,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Deterministic Mathematical Insights Engine (Zero LLM hallucinations).
        Generates grounded, rule-based executive insights directly from analytical distributions.
        """
        analysis = _verify_analysis_ownership(analysis_id, current_user.id, db)
        results = _get_valid_feedback_results(analysis_id, db)

        usable_count = len(results)
        if usable_count == 0:
            return {
                "health_score": 50.0,
                "health_status": "Neutral",
                "summary": "Insufficient usable feedback items to generate deterministic insights.",
                "insights": [],
                "recommendations": [],
            }

        sent_counts = Counter(
            (r.sentiment_label or "neutral").lower() for r in results
        )
        pos_c = sent_counts.get("positive", 0)
        neg_c = sent_counts.get("negative", 0)
        nss = round(((pos_c - neg_c) / usable_count) * 100, 1)

        # Health score calculation (bounded 0 to 100)
        health_score = max(0.0, min(100.0, round(50.0 + (nss / 2.0), 1)))
        if health_score >= 70:
            health_status = "Excellent"
        elif health_score >= 55:
            health_status = "Good"
        elif health_score >= 45:
            health_status = "Moderate"
        elif health_score >= 30:
            health_status = "At Risk"
        else:
            health_status = "Critical"

        insights = []
        recommendations = []

        # Topic Aggregations for Drivers
        topic_stats = defaultdict(lambda: {"total": 0, "pos": 0, "neg": 0, "neu": 0, "label": "Unknown"})
        for r in results:
            t_id = r.topic_id if r.topic_id is not None else -1
            t_label = r.topic_label or "Outliers & General"
            topic_stats[t_id]["total"] += 1
            topic_stats[t_id]["label"] = t_label
            s = (r.sentiment_label or "neutral").lower()
            if s == "positive":
                topic_stats[t_id]["pos"] += 1
            elif s == "negative":
                topic_stats[t_id]["neg"] += 1
            else:
                topic_stats[t_id]["neu"] += 1

        # Min feedback threshold for topic insight significance
        min_topic_thresh = max(1, min(3, usable_count // 10))
        qualified_topics = [
            (t_id, data)
            for t_id, data in topic_stats.items()
            if data["total"] >= min_topic_thresh and t_id != -1
        ]

        # 1. Top Positive Driver Insight
        if qualified_topics:
            best_pos_topic = max(
                qualified_topics,
                key=lambda x: (x[1]["pos"] / x[1]["total"], x[1]["total"]),
            )
            t_id, data = best_pos_topic
            pos_ratio = round((data["pos"] / data["total"]) * 100, 1)
            if pos_ratio >= 40:
                insights.append({
                    "id": "insight_pos_driver",
                    "type": "positive_driver",
                    "title": f"Key Satisfaction Driver: {data['label']}",
                    "description": (
                        f"Feedback related to '{data['label']}' demonstrates the highest customer satisfaction, "
                        f"with {pos_ratio}% positive sentiment across {data['total']} responses."
                    ),
                    "metric_value": f"{pos_ratio}% Positive",
                    "severity": "positive",
                })
                recommendations.append({
                    "id": "rec_pos_leverage",
                    "title": f"Promote Strengths in {data['label']}",
                    "description": (
                        f"Highlight successes and best practices from '{data['label']}' in marketing and onboarding."
                    ),
                    "priority": "Medium",
                })

        # 2. Top Friction Driver Insight
        if qualified_topics:
            worst_neg_topic = max(
                qualified_topics,
                key=lambda x: (x[1]["neg"] / x[1]["total"], x[1]["total"]),
            )
            t_id, data = worst_neg_topic
            neg_ratio = round((data["neg"] / data["total"]) * 100, 1)
            if neg_ratio >= 30:
                insights.append({
                    "id": "insight_neg_friction",
                    "type": "friction_driver",
                    "title": f"Primary Friction Driver: {data['label']}",
                    "description": (
                        f"Topic '{data['label']}' exhibits the highest dissatisfaction rate, "
                        f"with {neg_ratio}% negative feedback ({data['neg']} out of {data['total']} items)."
                    ),
                    "metric_value": f"{neg_ratio}% Negative",
                    "severity": "critical" if neg_ratio >= 50 else "warning",
                })
                recommendations.append({
                    "id": "rec_friction_fix",
                    "title": f"Address Quality Concerns in {data['label']}",
                    "description": (
                        f"Prioritize product and customer experience remediation for '{data['label']}' to reduce churn risk."
                    ),
                    "priority": "High" if neg_ratio >= 50 else "Medium",
                })

        # 3. Emotion Tone Insight
        emotion_counts = Counter(
            (r.emotion_label or "neutral").lower() for r in results
        )
        if emotion_counts:
            top_emo, top_emo_count = emotion_counts.most_common(1)[0]
            top_emo_pct = round((top_emo_count / usable_count) * 100, 1)

            emo_severity = "positive" if top_emo in ["joy", "surprise"] else (
                "critical" if top_emo in ["anger", "disgust"] else (
                    "warning" if top_emo in ["sadness", "fear"] else "info"
                )
            )

            insights.append({
                "id": "insight_dominant_emotion",
                "type": "emotion_tone",
                "title": f"Dominant Tone: {top_emo.capitalize()}",
                "description": (
                    f"The prevailing emotional sentiment across feedback is '{top_emo}', "
                    f"accounting for {top_emo_pct}% ({top_emo_count} items) of analyzed customer responses."
                ),
                "metric_value": f"{top_emo_pct}% {top_emo.capitalize()}",
                "severity": emo_severity,
            })

            # Check for elevated anger / frustration
            anger_c = emotion_counts.get("anger", 0) + emotion_counts.get("disgust", 0)
            if anger_c / usable_count >= 0.20:
                insights.append({
                    "id": "insight_escalation_risk",
                    "type": "risk_alert",
                    "title": "Elevated Customer Frustration Alert",
                    "description": (
                        f"High frustration levels detected: {round((anger_c / usable_count) * 100, 1)}% of feedback "
                        "expresses anger or disgust. Immediate support review recommended."
                    ),
                    "metric_value": f"{round((anger_c / usable_count) * 100, 1)}% Frustrated",
                    "severity": "critical",
                })
                recommendations.append({
                    "id": "rec_escalation_support",
                    "title": "Establish Priority Support Routing",
                    "description": "Implement fast-track escalation workflows for customer feedback tagged with anger or disgust.",
                    "priority": "High",
                })

        # 4. Overall Executive Summary
        if nss >= 30:
            summary = (
                f"Customer sentiment is overwhelmingly positive with a Net Sentiment Score of +{nss} and {health_status} overall health. "
                "Customer satisfaction is high across core touchpoints."
            )
        elif nss >= 0:
            summary = (
                f"Customer sentiment is moderately balanced with a Net Sentiment Score of +{nss}. "
                "Identified friction topics provide clear opportunities for operational improvement."
            )
        else:
            summary = (
                f"Customer sentiment requires attention with a Net Sentiment Score of {nss} and {health_status} health. "
                "Negative sentiment clusters indicate critical pain points that require swift intervention."
            )

        return {
            "health_score": health_score,
            "health_status": health_status,
            "summary": summary,
            "insights": insights,
            "recommendations": recommendations,
        }

    @staticmethod
    def get_cross_matrices(
        analysis_id: int,
        current_user: User,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Builds cross-dimensional analytical matrices:
        - Sentiment × Emotion
        - Sentiment × Topic
        - Emotion × Topic
        """
        analysis = _verify_analysis_ownership(analysis_id, current_user.id, db)
        results = _get_valid_feedback_results(analysis_id, db)
        usable_count = len(results)

        if usable_count == 0:
            return {
                "sentiment_emotion": {"rows": [], "columns": ALL_EMOTIONS, "data": []},
                "sentiment_topic": {"topics": []},
                "emotion_topic": {"topics": [], "emotions": ALL_EMOTIONS},
            }

        # 1. Sentiment × Emotion Matrix
        se_counts = defaultdict(lambda: defaultdict(int))
        for r in results:
            s = (r.sentiment_label or "neutral").lower()
            e = (r.emotion_label or "neutral").lower()
            se_counts[s][e] += 1

        se_matrix = []
        for s in ALL_SENTIMENTS:
            row_data = {}
            for e in ALL_EMOTIONS:
                cnt = se_counts[s][e]
                pct = round((cnt / usable_count) * 100, 1)
                row_data[e] = {"count": cnt, "percentage": pct}
            se_matrix.append({
                "sentiment": s,
                "emotions": row_data,
                "total": sum(se_counts[s].values()),
            })

        # 2. Sentiment × Topic Matrix
        topic_sent = defaultdict(lambda: {"total": 0, "pos": 0, "neg": 0, "neu": 0, "label": "Unknown"})
        topic_emo = defaultdict(lambda: defaultdict(int))
        for r in results:
            t_id = r.topic_id if r.topic_id is not None else -1
            t_label = r.topic_label or "Outliers & General"
            topic_sent[t_id]["total"] += 1
            topic_sent[t_id]["label"] = t_label
            s = (r.sentiment_label or "neutral").lower()
            e = (r.emotion_label or "neutral").lower()
            topic_emo[t_id][e] += 1
            if s == "positive":
                topic_sent[t_id]["pos"] += 1
            elif s == "negative":
                topic_sent[t_id]["neg"] += 1
            else:
                topic_sent[t_id]["neu"] += 1

        st_topics = []
        et_topics = []
        for t_id, data in sorted(
            topic_sent.items(), key=lambda x: x[1]["total"], reverse=True
        ):
            tot = data["total"]
            nss = round(((data["pos"] - data["neg"]) / tot) * 100, 1) if tot > 0 else 0.0
            st_topics.append({
                "topic_id": t_id,
                "topic_label": data["label"],
                "total_count": tot,
                "positive_count": data["pos"],
                "positive_percentage": round((data["pos"] / tot) * 100, 1) if tot else 0.0,
                "neutral_count": data["neu"],
                "neutral_percentage": round((data["neu"] / tot) * 100, 1) if tot else 0.0,
                "negative_count": data["neg"],
                "negative_percentage": round((data["neg"] / tot) * 100, 1) if tot else 0.0,
                "net_sentiment_score": nss,
            })

            # Emotion x Topic
            emo_breakdown = {}
            for e in ALL_EMOTIONS:
                cnt = topic_emo[t_id][e]
                emo_breakdown[e] = {
                    "count": cnt,
                    "percentage": round((cnt / tot) * 100, 1) if tot else 0.0,
                }
            et_topics.append({
                "topic_id": t_id,
                "topic_label": data["label"],
                "total_count": tot,
                "emotions": emo_breakdown,
            })

        return {
            "sentiment_emotion": {
                "columns": ALL_EMOTIONS,
                "rows": se_matrix,
            },
            "sentiment_topic": {
                "topics": st_topics,
            },
            "emotion_topic": {
                "emotions": ALL_EMOTIONS,
                "topics": et_topics,
            },
        }

    @staticmethod
    def get_temporal_trends(
        analysis_id: int,
        current_user: User,
        db: Session,
        interval: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extracts temporal trends safely from the source dataset file without fabricating dates.
        Enforces multi-tenant ownership: User -> Analysis -> Dataset -> Authorized storage path.
        """
        analysis = _verify_analysis_ownership(analysis_id, current_user.id, db)
        dataset = analysis.dataset or db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()

        if not dataset:
            return {
                "available": False,
                "reason": "Associated dataset not found.",
                "timeline": [],
            }

        # 1. Identify date column in dataset schema
        date_col = None
        quality_report = dataset.quality_report or {}
        detected_cols_meta = quality_report.get("detected_columns", {})
        if isinstance(detected_cols_meta, dict):
            for col_name, meta in detected_cols_meta.items():
                if isinstance(meta, dict):
                    role = str(meta.get("role", "")).lower()
                    dtype = str(meta.get("type", "")).lower()
                    if role == "date" or "date" in dtype or "time" in dtype:
                        date_col = col_name
                        break

        # Fallback check on dataset file columns
        storage = LocalStorageService()
        try:
            file_path = storage.get_file_path(dataset.storage_path)
        except Exception as e:
            logger.warning(f"Could not resolve storage path for temporal analytics: {e}")
            return {
                "available": False,
                "reason": "Dataset file is temporarily inaccessible.",
                "timeline": [],
            }

        if not date_col:
            try:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == ".csv":
                    header_cols = list(pd.read_csv(file_path, nrows=0).columns)
                else:
                    header_cols = list(pd.read_excel(file_path, nrows=0).columns)
                for col in header_cols:
                    c_low = col.lower()
                    if c_low in ["date", "timestamp", "created_at", "time", "review_date", "feedback_date", "datetime", "created_date"]:
                        date_col = col
                        break
            except Exception:
                pass

        if not date_col:
            return {
                "available": False,
                "reason": "No valid date column detected in source dataset.",
                "timeline": [],
            }

        # 3. Read ONLY date column memory-safely
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".csv":
                df_dates = pd.read_csv(file_path, usecols=[date_col])
            else:
                df_dates = pd.read_excel(file_path, usecols=[date_col])
        except Exception as read_err:
            logger.warning(f"Failed to read date column '{date_col}': {read_err}")
            return {
                "available": False,
                "reason": f"Unable to parse date column '{date_col}'.",
                "timeline": [],
            }

        # 4. Parse dates safely
        parsed_dates = pd.to_datetime(df_dates[date_col], errors="coerce")
        if parsed_dates.dropna().empty:
            return {
                "available": False,
                "reason": f"Date column '{date_col}' contains no valid dates.",
                "timeline": [],
            }

        # 5. Join with FeedbackResult by row_index
        results = _get_valid_feedback_results(analysis_id, db)
        results_by_row = {r.row_index: r for r in results}

        valid_points = []
        for row_idx, dt in parsed_dates.items():
            if pd.isna(dt):
                continue
            r = results_by_row.get(row_idx)
            if not r:
                continue
            valid_points.append({
                "date": dt,
                "sentiment": (r.sentiment_label or "neutral").lower(),
                "emotion": (r.emotion_label or "neutral").lower(),
            })

        if len(valid_points) < 2:
            return {
                "available": False,
                "reason": "Insufficient timestamped feedback items to compute timeline trends.",
                "timeline": [],
            }

        # 6. Group by interval (Day / Week / Month)
        df_pts = pd.DataFrame(valid_points)
        min_date = df_pts["date"].min()
        max_date = df_pts["date"].max()
        span_days = (max_date - min_date).days

        selected_interval = interval
        if not selected_interval or selected_interval == "auto":
            if span_days <= 31:
                selected_interval = "day"
            elif span_days <= 180:
                selected_interval = "week"
            else:
                selected_interval = "month"

        if selected_interval == "day":
            df_pts["period"] = df_pts["date"].dt.strftime("%Y-%m-%d")
        elif selected_interval == "week":
            df_pts["period"] = df_pts["date"].dt.to_period("W").apply(lambda r: str(r.start_time.strftime("%Y-%m-%d")))
        else:
            df_pts["period"] = df_pts["date"].dt.strftime("%Y-%m")

        timeline = []
        for period, group in df_pts.groupby("period", sort=True):
            tot = len(group)
            s_counts = group["sentiment"].value_counts()
            pos = int(s_counts.get("positive", 0))
            neu = int(s_counts.get("neutral", 0))
            neg = int(s_counts.get("negative", 0))
            nss = round(((pos - neg) / tot) * 100, 1) if tot > 0 else 0.0

            emo_counts = group["emotion"].value_counts()
            dom_emo = str(emo_counts.index[0]) if not emo_counts.empty else "neutral"

            timeline.append({
                "period": str(period),
                "total_count": tot,
                "positive_count": pos,
                "neutral_count": neu,
                "negative_count": neg,
                "net_sentiment_score": nss,
                "dominant_emotion": dom_emo,
            })

        return {
            "available": True,
            "date_column": date_col,
            "interval": selected_interval,
            "timeline": timeline,
        }

    @staticmethod
    def get_categorical_breakdowns(
        analysis_id: int,
        current_user: User,
        db: Session,
        column_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Computes sentiment breakdowns across categorical metadata columns (e.g. Channel, Region, Product Tier).
        """
        analysis = _verify_analysis_ownership(analysis_id, current_user.id, db)
        dataset = analysis.dataset or db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()

        if not dataset:
            return {
                "available": False,
                "reason": "Associated dataset not found.",
                "breakdown": [],
            }

        # Identify potential categorical columns
        cat_cols = []
        quality_report = dataset.quality_report or {}
        detected_cols_meta = quality_report.get("detected_columns", {})
        if isinstance(detected_cols_meta, dict):
            for col, meta in detected_cols_meta.items():
                if isinstance(meta, dict):
                    role = str(meta.get("role", "")).lower()
                    dtype = str(meta.get("type", "")).lower()
                    if role in ["category", "dimension", "metadata"] or (
                        role not in ["feedback", "date", "id"] and dtype in ["string", "category", "integer"]
                    ):
                        cat_cols.append(col)

        # Fallback check on file columns
        storage = LocalStorageService()
        try:
            file_path = storage.get_file_path(dataset.storage_path)
            ext = os.path.splitext(file_path)[1].lower()
            if not cat_cols:
                if ext == ".csv":
                    header_cols = list(pd.read_csv(file_path, nrows=0).columns)
                else:
                    header_cols = list(pd.read_excel(file_path, nrows=0).columns)
                f_col = dataset.feedback_column
                for col in header_cols:
                    if col != f_col and col.lower() not in ["id", "index", "row", "date", "timestamp", "created_at", "time"]:
                        cat_cols.append(col)
        except Exception as e:
            logger.warning(f"Error accessing dataset file for categorical columns: {e}")
            return {
                "available": False,
                "reason": "Dataset file is temporarily inaccessible.",
                "breakdown": [],
            }

        if not cat_cols:
            return {
                "available": False,
                "reason": "No categorical dimension columns found in source dataset.",
                "breakdown": [],
            }

        target_col = column_name if column_name in cat_cols else cat_cols[0]

        # Secure read
        try:
            if ext == ".csv":
                df_cat = pd.read_csv(file_path, usecols=[target_col])
            else:
                df_cat = pd.read_excel(file_path, usecols=[target_col])
        except Exception as e:
            logger.warning(f"Error reading categorical column '{target_col}': {e}")
            return {
                "available": False,
                "reason": f"Unable to read dimension column '{target_col}'.",
                "breakdown": [],
            }

        results = _get_valid_feedback_results(analysis_id, db)
        results_by_row = {r.row_index: r for r in results}

        cat_groups = defaultdict(lambda: {"total": 0, "pos": 0, "neg": 0, "neu": 0, "emotions": Counter()})
        for row_idx, val in df_cat[target_col].items():
            if pd.isna(val):
                val_str = "(Missing)"
            else:
                val_str = str(val).strip()

            r = results_by_row.get(row_idx)
            if not r:
                continue

            g = cat_groups[val_str]
            g["total"] += 1
            s = (r.sentiment_label or "neutral").lower()
            e = (r.emotion_label or "neutral").lower()
            g["emotions"][e] += 1
            if s == "positive":
                g["pos"] += 1
            elif s == "negative":
                g["neg"] += 1
            else:
                g["neu"] += 1

        breakdown = []
        for cat_val, g in sorted(cat_groups.items(), key=lambda x: x[1]["total"], reverse=True):
            tot = g["total"]
            nss = round(((g["pos"] - g["neg"]) / tot) * 100, 1) if tot > 0 else 0.0
            top_e = g["emotions"].most_common(1)[0][0] if g["emotions"] else "neutral"
            breakdown.append({
                "category_value": cat_val,
                "total_count": tot,
                "positive_count": g["pos"],
                "positive_percentage": round((g["pos"] / tot) * 100, 1) if tot else 0.0,
                "neutral_count": g["neu"],
                "neutral_percentage": round((g["neu"] / tot) * 100, 1) if tot else 0.0,
                "negative_count": g["neg"],
                "negative_percentage": round((g["neg"] / tot) * 100, 1) if tot else 0.0,
                "net_sentiment_score": nss,
                "dominant_emotion": top_e,
            })

        return {
            "available": True,
            "categorical_columns": cat_cols,
            "active_column": target_col,
            "breakdown": breakdown,
        }

    @staticmethod
    def explain_feedback_row(
        analysis_id: int,
        feedback_result_id: int,
        current_user: User,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Provides on-demand SHAP token-level feature attribution for a specific feedback result.
        Reuses cached ExplainabilityResult when available; otherwise runs explainability inference,
        persists attribution weights without duplicating customer text, and returns the explanation.
        """
        analysis = _verify_analysis_ownership(analysis_id, current_user.id, db)
        feedback_result = (
            db.query(FeedbackResult)
            .filter(
                FeedbackResult.id == feedback_result_id,
                FeedbackResult.analysis_id == analysis.id,
            )
            .first()
        )
        if not feedback_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback result not found for this analysis.",
            )

        # 1. Check persistent cache
        cached = (
            db.query(ExplainabilityResult)
            .filter(
                ExplainabilityResult.analysis_id == analysis.id,
                ExplainabilityResult.feedback_result_id == feedback_result.id,
                ExplainabilityResult.model_name == settings.sentiment_model,
                ExplainabilityResult.explainer_name == "PartitionExplainer",
            )
            .first()
        )

        if cached:
            raw_label = cached.raw_predicted_label or f"{cached.predicted_label}"
            pos_tokens = sorted(
                [t for t in cached.token_contributions if t.get("shap_value", 0) > 0],
                key=lambda x: x.get("shap_value", 0),
                reverse=True,
            )[:5]
            neg_tokens = sorted(
                [t for t in cached.token_contributions if t.get("shap_value", 0) < 0],
                key=lambda x: x.get("shap_value", 0),
            )[:5]

            return {
                "id": cached.id,
                "analysis_id": cached.analysis_id,
                "feedback_result_id": cached.feedback_result_id,
                "predicted_label": cached.predicted_label,
                "raw_predicted_label": cached.raw_predicted_label,
                "confidence": cached.confidence,
                "base_value": cached.base_value,
                "token_contributions": cached.token_contributions,
                "positive_tokens": pos_tokens,
                "negative_tokens": neg_tokens,
                "model_name": cached.model_name,
                "explainer_name": cached.explainer_name,
                "is_cached": True,
                "sentiment_mapping": {
                    "raw_star_output": raw_label,
                    "cfap_mapped_sentiment": cached.predicted_label,
                    "mapping_rule": STAR_MAPPING_RULES.get(raw_label, "Deterministic 3-Class Mapping"),
                    "explanation_basis": (
                        f"SHAP attribution mathematically computed for raw model output '{raw_label}', "
                        f"mapped deterministically to CFAP '{cached.predicted_label}' sentiment."
                    ),
                },
            }

        # 2. Extract feedback text securely for this row index from source dataset
        dataset = analysis.dataset or db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
        if not dataset or not dataset.feedback_column:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source dataset or feedback column not available for explanation.",
            )

        storage = LocalStorageService()
        file_path = storage.get_file_path(dataset.storage_path)
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".csv":
                df = pd.read_csv(file_path, usecols=[dataset.feedback_column])
            else:
                df = pd.read_excel(file_path, usecols=[dataset.feedback_column])
            raw_text = str(df.iloc[feedback_result.row_index][dataset.feedback_column])
        except Exception as err:
            logger.error(f"Error reading row {feedback_result.row_index} from dataset: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve feedback text from source storage for explanation.",
            )

        # 3. Run SHAP Explainability Service
        explainer_svc = ExplainabilityService.get_instance()
        explanation = explainer_svc.explain_text(raw_text)

        # 4. Cache explanation without duplicating text
        new_cached = ExplainabilityResult(
            analysis_id=analysis.id,
            feedback_result_id=feedback_result.id,
            predicted_label=explanation["predicted_label"],
            raw_predicted_label=explanation["raw_predicted_label"],
            confidence=explanation["confidence"],
            base_value=explanation["base_value"],
            token_contributions=explanation["token_contributions"],
            model_name=explanation["model_name"],
            explainer_name=explanation["explainer_name"],
        )
        db.add(new_cached)
        db.commit()
        db.refresh(new_cached)

        explanation["id"] = new_cached.id
        explanation["analysis_id"] = analysis.id
        explanation["feedback_result_id"] = feedback_result.id
        explanation["is_cached"] = False
        return explanation
