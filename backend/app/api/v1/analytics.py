import logging
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_verified_user
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.analytics import (
    CategoricalBreakdownResponse,
    CrossMatricesResponse,
    ExecutiveOverviewResponse,
    ExplainabilityResponse,
    InsightsResponse,
    TemporalTrendsResponse,
)
from backend.app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Analytics & Explainability"])


@router.get(
    "/analyses/{analysis_id}/analytics/overview",
    response_model=ExecutiveOverviewResponse,
)
def get_analysis_executive_overview(
    analysis_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves executive overview KPIs for a completed analysis:
    Net Sentiment Score (NSS), positive ratio, sentiment distribution,
    top emotions, and topic-level sentiment breakdown.
    """
    return AnalyticsService.get_overview(
        analysis_id=analysis_id,
        current_user=current_user,
        db=db,
    )


@router.get(
    "/analyses/{analysis_id}/analytics/insights",
    response_model=InsightsResponse,
)
def get_analysis_deterministic_insights(
    analysis_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Deterministic Mathematical Insights Engine (Zero LLM hallucinations).
    Returns grounded health score, satisfaction drivers, friction drivers,
    emotional tone evaluation, and actionable recommendations.
    """
    return AnalyticsService.get_insights(
        analysis_id=analysis_id,
        current_user=current_user,
        db=db,
    )


@router.get(
    "/analyses/{analysis_id}/analytics/cross-matrices",
    response_model=CrossMatricesResponse,
)
def get_analysis_cross_matrices(
    analysis_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves cross-dimensional analytical matrices:
    - Sentiment × Emotion Intersection Matrix
    - Sentiment × Topic Cross Matrix (with Topic NSS)
    - Emotion × Topic Distribution Matrix
    """
    return AnalyticsService.get_cross_matrices(
        analysis_id=analysis_id,
        current_user=current_user,
        db=db,
    )


@router.get(
    "/analyses/{analysis_id}/analytics/temporal-trends",
    response_model=TemporalTrendsResponse,
)
def get_analysis_temporal_trends(
    analysis_id: int,
    interval: Optional[str] = Query("auto", description="Aggregation interval: auto, day, week, month"),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Computes secure, memory-safe time-series sentiment trends from the source dataset.
    Returns graceful unavailable state if no valid date column exists.
    """
    return AnalyticsService.get_temporal_trends(
        analysis_id=analysis_id,
        current_user=current_user,
        db=db,
        interval=interval,
    )


@router.get(
    "/analyses/{analysis_id}/analytics/categorical",
    response_model=CategoricalBreakdownResponse,
)
def get_analysis_categorical_breakdown(
    analysis_id: int,
    column: Optional[str] = Query(None, description="Metadata dimension column name"),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Computes sentiment distribution and Net Sentiment Score across categorical metadata dimensions
    (e.g., Channel, Product Tier, Region).
    """
    return AnalyticsService.get_categorical_breakdowns(
        analysis_id=analysis_id,
        current_user=current_user,
        db=db,
        column_name=column,
    )


@router.get(
    "/analyses/{analysis_id}/results/{feedback_result_id}/explain",
    response_model=ExplainabilityResponse,
)
def explain_feedback_result(
    analysis_id: int,
    feedback_result_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    On-Demand Explainable AI (SHAP):
    Computes token-level feature attribution mathematically grounded in the real
    BERT sequence classification model. Caches results in explainability_results
    without duplicating customer text.
    """
    return AnalyticsService.explain_feedback_row(
        analysis_id=analysis_id,
        feedback_result_id=feedback_result_id,
        current_user=current_user,
        db=db,
    )
