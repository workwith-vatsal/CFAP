import math
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_verified_user
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.analysis import (
    AnalysisResponse,
    AnalysisSummaryResponse,
    FeedbackResultItemResponse,
    FeedbackResultListResponse,
)
from backend.app.schemas.auth import MessageResponse
from backend.app.services.analysis_service import (
    delete_analysis,
    get_analysis_by_id,
    get_latest_dataset_analysis,
    get_paginated_feedback_results,
    list_dataset_analyses,
    trigger_dataset_analysis,
)
from backend.app.services.dataset_service import get_user_dataset_by_id

router = APIRouter(tags=["AI Analysis"])


@router.post(
    "/datasets/{dataset_id}/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_dataset_analysis(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Triggers an AI analysis run (Sentiment, Emotion, Embeddings, BERTopic) for a dataset.
    Dispatches task asynchronously.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    analysis = trigger_dataset_analysis(
        dataset=dataset,
        user_id=current_user.id,
        db=db,
    )
    return analysis


@router.get(
    "/datasets/{dataset_id}/analysis",
    response_model=AnalysisResponse,
)
def get_dataset_latest_analysis(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the latest analysis run for the specified dataset.
    """
    # Verify dataset access
    get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    analysis = get_latest_dataset_analysis(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis has been run for this dataset yet.",
        )
    return analysis


@router.get(
    "/datasets/{dataset_id}/analyses",
    response_model=List[AnalysisSummaryResponse],
)
def get_dataset_analysis_history(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves all historical analysis runs for the specified dataset.
    """
    # Verify dataset access
    get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    analyses = list_dataset_analyses(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    return [AnalysisSummaryResponse.model_validate(a) for a in analyses]


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisResponse,
)
def get_analysis_details(
    analysis_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves status, progress, metrics, and aggregated summaries for a specific analysis run.
    """
    analysis = get_analysis_by_id(
        analysis_id=analysis_id,
        user_id=current_user.id,
        db=db,
    )
    return analysis


@router.get(
    "/analyses/{analysis_id}/results",
    response_model=FeedbackResultListResponse,
)
def get_analysis_row_results(
    analysis_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive, neutral, negative)"),
    emotion: Optional[str] = Query(None, description="Filter by dominant emotion"),
    topic_id: Optional[int] = Query(None, description="Filter by topic ID"),
    is_valid: Optional[bool] = Query(None, description="Filter by validity"),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated and filtered feedback analysis results.
    Does NOT return customer text or embedding bytes (privacy preserved).
    """
    analysis = get_analysis_by_id(
        analysis_id=analysis_id,
        user_id=current_user.id,
        db=db,
    )
    items, total = get_paginated_feedback_results(
        analysis=analysis,
        db=db,
        page=page,
        page_size=page_size,
        sentiment=sentiment,
        emotion=emotion,
        topic_id=topic_id,
        is_valid=is_valid,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return FeedbackResultListResponse(
        items=[FeedbackResultItemResponse.model_validate(it) for it in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.delete(
    "/analyses/{analysis_id}",
    response_model=MessageResponse,
)
def delete_single_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Deletes an analysis run and its associated feedback results.
    """
    analysis = get_analysis_by_id(
        analysis_id=analysis_id,
        user_id=current_user.id,
        db=db,
    )
    delete_analysis(analysis=analysis, db=db)
    return MessageResponse(message="Analysis deleted successfully.")
