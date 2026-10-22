import logging
import threading
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models.analysis import Analysis, AnalysisStage, AnalysisStatus
from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.feedback_result import FeedbackResult
from backend.app.tasks.analysis_tasks import execute_analysis_pipeline, run_analysis_pipeline

logger = logging.getLogger(__name__)


def trigger_dataset_analysis(
    dataset: Dataset,
    user_id: int,
    db: Session,
) -> Analysis:
    """
    Triggers an AI analysis run for the specified dataset.
    Enforces that only one active (QUEUED / PROCESSING) analysis can run concurrently per dataset.
    Supports unlimited historical analyses per dataset.
    """
    if dataset.status != DatasetStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot analyze dataset in '{dataset.status}' status. Must be 'READY'.",
        )

    if not dataset.feedback_column:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset does not have a designated feedback text column.",
        )

    # Check for active analysis
    active_analysis = (
        db.query(Analysis)
        .filter(
            Analysis.dataset_id == dataset.id,
            Analysis.status.in_([AnalysisStatus.QUEUED, AnalysisStatus.PROCESSING]),
        )
        .first()
    )
    if active_analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An analysis (ID: {active_analysis.id}) is already currently {active_analysis.status} for this dataset.",
        )

    # Create new Analysis record
    new_analysis = Analysis(
        dataset_id=dataset.id,
        owner_id=user_id,
        status=AnalysisStatus.QUEUED,
        progress=0,
        current_stage=AnalysisStage.INITIALIZED,
        total_feedback_rows=dataset.row_count,
        usable_feedback_rows=0,
    )
    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)

    # Dispatch to Celery background worker or fallback to background thread
    try:
        run_analysis_pipeline.delay(new_analysis.id)
        logger.info(f"Dispatched Analysis {new_analysis.id} to Celery worker.")
    except Exception as celery_err:
        logger.warning(
            f"Celery dispatch failed ({celery_err}), launching background thread fallback."
        )
        thread = threading.Thread(
            target=execute_analysis_pipeline,
            args=(new_analysis.id,),
            daemon=True,
        )
        thread.start()

    return new_analysis


def get_latest_dataset_analysis(
    dataset_id: int,
    user_id: int,
    db: Session,
) -> Optional[Analysis]:
    """
    Retrieves the latest analysis run for a dataset owned by the user.
    """
    analysis = (
        db.query(Analysis)
        .join(Dataset)
        .filter(
            Analysis.dataset_id == dataset_id,
            Dataset.owner_id == user_id,
        )
        .order_by(desc(Analysis.created_at))
        .first()
    )
    return analysis


def list_dataset_analyses(
    dataset_id: int,
    user_id: int,
    db: Session,
) -> List[Analysis]:
    """
    Retrieves all historical analysis runs for a dataset owned by the user.
    """
    analyses = (
        db.query(Analysis)
        .join(Dataset)
        .filter(
            Analysis.dataset_id == dataset_id,
            Dataset.owner_id == user_id,
        )
        .order_by(desc(Analysis.created_at))
        .all()
    )
    return analyses


def get_analysis_by_id(
    analysis_id: int,
    user_id: int,
    db: Session,
) -> Analysis:
    """
    Retrieves a single analysis by ID, verifying tenant ownership.
    """
    analysis = (
        db.query(Analysis)
        .filter(
            Analysis.id == analysis_id,
            Analysis.owner_id == user_id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or access denied.",
        )
    return analysis


def get_paginated_feedback_results(
    analysis: Analysis,
    db: Session,
    page: int = 1,
    page_size: int = 50,
    sentiment: Optional[str] = None,
    emotion: Optional[str] = None,
    topic_id: Optional[int] = None,
    is_valid: Optional[bool] = None,
) -> Tuple[List[FeedbackResult], int]:
    """
    Retrieves paginated and filtered feedback analysis row results.
    Does NOT return embeddings or preprocessed customer text.
    """
    query = db.query(FeedbackResult).filter(FeedbackResult.analysis_id == analysis.id)

    if sentiment:
        query = query.filter(FeedbackResult.sentiment_label == sentiment.lower())
    if emotion:
        query = query.filter(FeedbackResult.emotion_label == emotion.lower())
    if topic_id is not None:
        query = query.filter(FeedbackResult.topic_id == topic_id)
    if is_valid is not None:
        query = query.filter(FeedbackResult.is_valid == is_valid)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(FeedbackResult.row_index).offset(offset).limit(page_size).all()

    return items, total


def delete_analysis(
    analysis: Analysis,
    db: Session,
) -> None:
    """
    Deletes an analysis and cascades deletion of its feedback results.
    """
    db.delete(analysis)
    db.commit()
