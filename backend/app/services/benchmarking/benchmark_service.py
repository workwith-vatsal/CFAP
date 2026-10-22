import statistics
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.config import settings
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset
from backend.app.models.feedback_result import FeedbackResult
from backend.app.models.user import User
from backend.app.schemas.benchmark import (
    BenchmarkMethodology,
    BenchmarkSummaryResponse,
    EmotionComparison,
    MetricComparison,
    SentimentComparison,
)
from backend.app.services.analytics_service import AnalyticsService


class BenchmarkService:
    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        """Calculate p-th percentile (0 <= p <= 100) from a list of floats."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        if len(sorted_vals) == 1:
            return sorted_vals[0]
        k = (len(sorted_vals) - 1) * (p / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_vals) - 1)
        d = k - f
        return sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f])

    @classmethod
    def get_benchmark_summary(
        cls,
        user: User,
        analysis_id: int,
        db: Session,
    ) -> BenchmarkSummaryResponse:
        """
        Produce privacy-preserving anonymized benchmark comparisons between the user's
        completed analysis and cross-platform aggregates from eligible completed analyses.
        """
        # 1. Authorize user and verify target analysis
        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == analysis_id, Analysis.owner_id == user.id)
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
                detail="Benchmark comparison requires a completed analysis.",
            )

        # 2. Retrieve user's authoritative analytical metrics
        user_overview = AnalyticsService.get_overview(analysis_id, user, db)
        user_dataset = (
            db.query(Dataset).filter(Dataset.id == analysis.dataset_id).first()
        )
        dataset_name = user_dataset.name if user_dataset else f"Dataset #{analysis.dataset_id}"
        user_quality_score = float(user_dataset.quality_score) if user_dataset and user_dataset.quality_score is not None else 0.0

        user_sent = user_overview.get("sentiment_distribution", {})
        user_nss = float(user_sent.get("net_sentiment_score", 0.0))
        user_pos_pct = float(user_sent.get("positive_pct", 0.0))
        user_neu_pct = float(user_sent.get("neutral_pct", 0.0))
        user_neg_pct = float(user_sent.get("negative_pct", 0.0))

        user_usable_rows = float(user_overview.get("summary", {}).get("usable_feedback", 0))

        user_emotions = user_overview.get("emotion_distribution", {})
        user_total_emotions = sum(user_emotions.values()) if user_emotions else 1
        user_emotion_pcts = {
            emo: (count / user_total_emotions) * 100.0
            for emo, count in user_emotions.items()
        }

        # 3. Query all completed eligible analyses across the platform
        eligible_analyses = (
            db.query(Analysis)
            .filter(
                Analysis.status == AnalysisStatus.COMPLETED,
                Analysis.usable_feedback_rows > 0,
            )
            .all()
        )

        eligible_count = len(eligible_analyses)
        min_threshold = settings.min_benchmark_sample_size

        methodology = BenchmarkMethodology(
            eligible_sample_size=eligible_count,
            min_required_sample_size=min_threshold,
        )

        # 4. Small-group privacy check
        if eligible_count < min_threshold:
            return BenchmarkSummaryResponse(
                is_eligible=False,
                eligible_sample_size=eligible_count,
                min_required_sample_size=min_threshold,
                message=(
                    f"Benchmark data unavailable due to insufficient aggregate sample size "
                    f"({eligible_count} completed analyses available, minimum {min_threshold} required)."
                ),
                analysis_id=analysis_id,
                dataset_name=dataset_name,
                net_sentiment_score=None,
                data_quality_score=None,
                sentiment_distribution=None,
                emotion_distribution=None,
                volume_comparison=None,
                methodology=methodology,
            )

        # 5. Compute mathematical platform aggregates across eligible analyses
        nss_list: list[float] = []
        pos_pct_list: list[float] = []
        neu_pct_list: list[float] = []
        neg_pct_list: list[float] = []
        volume_list: list[float] = []
        quality_score_list: list[float] = []

        standard_emotions = ["joy", "surprise", "neutral", "sadness", "anger", "fear", "disgust"]
        emotion_pct_lists: dict[str, list[float]] = {emo: [] for emo in standard_emotions}

        for item in eligible_analyses:
            # Query sentiment counts for this analysis
            sent_counts = (
                db.query(
                    FeedbackResult.sentiment_label,
                    func.count(FeedbackResult.id),
                )
                .filter(
                    FeedbackResult.analysis_id == item.id,
                    FeedbackResult.is_valid == True,
                )
                .group_by(FeedbackResult.sentiment_label)
                .all()
            )
            s_map = {row[0].lower(): row[1] for row in sent_counts if row[0]}
            total_s = sum(s_map.values())
            if total_s > 0:
                pos = (s_map.get("positive", 0) / total_s) * 100.0
                neu = (s_map.get("neutral", 0) / total_s) * 100.0
                neg = (s_map.get("negative", 0) / total_s) * 100.0
                nss = pos - neg

                nss_list.append(nss)
                pos_pct_list.append(pos)
                neu_pct_list.append(neu)
                neg_pct_list.append(neg)

            volume_list.append(float(item.usable_feedback_rows or 0))

            # Quality score
            ds = db.query(Dataset).filter(Dataset.id == item.dataset_id).first()
            if ds and ds.quality_score is not None:
                quality_score_list.append(float(ds.quality_score))

            # Emotion distribution
            emo_counts = (
                db.query(
                    FeedbackResult.emotion_label,
                    func.count(FeedbackResult.id),
                )
                .filter(
                    FeedbackResult.analysis_id == item.id,
                    FeedbackResult.is_valid == True,
                )
                .group_by(FeedbackResult.emotion_label)
                .all()
            )
            e_map = {row[0].lower(): row[1] for row in emo_counts if row[0]}
            total_e = sum(e_map.values())
            if total_e > 0:
                for emo in standard_emotions:
                    emo_pct = (e_map.get(emo, 0) / total_e) * 100.0
                    emotion_pct_lists[emo].append(emo_pct)

        # Fallback safeguards if lists empty
        if not nss_list:
            nss_list = [user_nss]
        if not pos_pct_list:
            pos_pct_list = [user_pos_pct]
        if not neu_pct_list:
            neu_pct_list = [user_neu_pct]
        if not neg_pct_list:
            neg_pct_list = [user_neg_pct]
        if not volume_list:
            volume_list = [user_usable_rows]
        if not quality_score_list:
            quality_score_list = [user_quality_score]

        # Aggregate Metrics Calculations
        plat_nss_mean = round(statistics.mean(nss_list), 1)
        plat_nss_median = round(statistics.median(nss_list), 1)
        plat_nss_p25 = round(cls._percentile(nss_list, 25), 1)
        plat_nss_p75 = round(cls._percentile(nss_list, 75), 1)
        nss_diff = round(user_nss - plat_nss_median, 1)

        if nss_diff > 0:
            nss_obs = f"Your Net Sentiment Score ({user_nss:+.1f}) is observed to be {nss_diff:+.1f} points above the platform median benchmark ({plat_nss_median:+.1f})."
        elif nss_diff < 0:
            nss_obs = f"Your Net Sentiment Score ({user_nss:+.1f}) is observed to be {abs(nss_diff):.1f} points below the platform median benchmark ({plat_nss_median:+.1f})."
        else:
            nss_obs = f"Your Net Sentiment Score ({user_nss:+.1f}) matches the platform median benchmark exactly."

        nss_comparison = MetricComparison(
            metric_name="Net Sentiment Score (NSS)",
            user_value=user_nss,
            platform_median=plat_nss_median,
            platform_mean=plat_nss_mean,
            platform_p25=plat_nss_p25,
            platform_p75=plat_nss_p75,
            difference=nss_diff,
            observation=nss_obs,
        )

        # Quality Score Comparison
        plat_q_mean = round(statistics.mean(quality_score_list), 1)
        plat_q_median = round(statistics.median(quality_score_list), 1)
        plat_q_p25 = round(cls._percentile(quality_score_list, 25), 1)
        plat_q_p75 = round(cls._percentile(quality_score_list, 75), 1)
        q_diff = round(user_quality_score - plat_q_median, 1)

        q_comparison = MetricComparison(
            metric_name="Data Quality Score",
            user_value=user_quality_score,
            platform_median=plat_q_median,
            platform_mean=plat_q_mean,
            platform_p25=plat_q_p25,
            platform_p75=plat_q_p75,
            difference=q_diff,
            observation=f"Dataset quality score ({user_quality_score:.1f}%) compares to platform median of {plat_q_median:.1f}%.",
        )

        # Volume Comparison
        plat_v_mean = round(statistics.mean(volume_list), 0)
        plat_v_median = round(statistics.median(volume_list), 0)
        plat_v_p25 = round(cls._percentile(volume_list, 25), 0)
        plat_v_p75 = round(cls._percentile(volume_list, 75), 0)
        v_diff = round(user_usable_rows - plat_v_median, 0)

        v_comparison = MetricComparison(
            metric_name="Usable Feedback Volume",
            user_value=user_usable_rows,
            platform_median=plat_v_median,
            platform_mean=plat_v_mean,
            platform_p25=plat_v_p25,
            platform_p75=plat_v_p75,
            difference=v_diff,
            observation=f"Dataset contains {int(user_usable_rows):,} usable rows compared to platform median of {int(plat_v_median):,} rows.",
        )

        # Sentiment Distribution Comparison
        sentiment_comparison = SentimentComparison(
            positive_user_pct=round(user_pos_pct, 1),
            positive_platform_pct=round(statistics.mean(pos_pct_list), 1),
            neutral_user_pct=round(user_neu_pct, 1),
            neutral_platform_pct=round(statistics.mean(neu_pct_list), 1),
            negative_user_pct=round(user_neg_pct, 1),
            negative_platform_pct=round(statistics.mean(neg_pct_list), 1),
        )

        # Emotion Distribution Comparison
        emotion_comparisons: list[EmotionComparison] = []
        for emo in standard_emotions:
            user_pct = round(user_emotion_pcts.get(emo, 0.0), 1)
            plat_pct_list = emotion_pct_lists.get(emo, [])
            plat_avg = round(statistics.mean(plat_pct_list), 1) if plat_pct_list else 0.0
            emotion_comparisons.append(
                EmotionComparison(
                    emotion=emo.capitalize(),
                    user_percentage=user_pct,
                    platform_average_percentage=plat_avg,
                )
            )

        return BenchmarkSummaryResponse(
            is_eligible=True,
            eligible_sample_size=eligible_count,
            min_required_sample_size=min_threshold,
            message=None,
            analysis_id=analysis_id,
            dataset_name=dataset_name,
            net_sentiment_score=nss_comparison,
            data_quality_score=q_comparison,
            sentiment_distribution=sentiment_comparison,
            emotion_distribution=emotion_comparisons,
            volume_comparison=v_comparison,
            methodology=methodology,
        )
