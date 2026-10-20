import logging
import os
import uuid
from datetime import datetime
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.dataset import Dataset, DatasetStatus
from backend.app.models.user import User
from backend.app.services.column_detection.detector import detect_all_columns, detect_feedback_column
from backend.app.services.data_quality.quality_engine import (
    calculate_data_quality,
    generate_sanitized_preview,
)
from backend.app.services.ingestion.file_validator import (
    FileValidationError,
    validate_upload_file,
)
from backend.app.services.ingestion.tabular_reader import ingest_tabular_file
from backend.app.services.storage.base import StorageService

logger = logging.getLogger(__name__)


def create_and_process_dataset(
    user: User,
    file_bytes: bytes,
    original_filename: str,
    content_type: str | None,
    custom_name: str | None,
    db: Session,
    storage: StorageService,
) -> Dataset:
    """
    Ingest, validate, store, and compute data quality for an uploaded dataset.
    Strictly isolated under user's tenancy.
    """
    file_size_bytes = len(file_bytes)

    # 1. Validate file format and constraints
    try:
        file_type = validate_upload_file(
            filename=original_filename,
            file_size_bytes=file_size_bytes,
            content_type=content_type,
        )
    except FileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Clean display name
    clean_display_name = (
        custom_name.strip()
        if custom_name and custom_name.strip()
        else os.path.splitext(os.path.basename(original_filename))[0]
    )
    if len(clean_display_name) > 255:
        clean_display_name = clean_display_name[:255]

    # 2. Generate safe UUID-based storage path
    file_uuid = str(uuid.uuid4())
    relative_storage_path = f"datasets/{user.id}/{file_uuid}.{file_type}"

    # 3. Persist file bytes via storage abstraction
    try:
        storage.save_file(file_bytes, relative_storage_path)
    except Exception as e:
        logger.error(f"Failed to store dataset file for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file to storage.",
        )

    # 4. Create initial Dataset record in database
    dataset = Dataset(
        owner_id=user.id,
        name=clean_display_name,
        original_filename=os.path.basename(original_filename),
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        storage_path=relative_storage_path,
        row_count=0,
        column_count=0,
        status=DatasetStatus.PROCESSING.value,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # 5. Execute tabular ingestion & quality analysis
    try:
        file_abs_path = storage.get_file_path(relative_storage_path)
        df = ingest_tabular_file(file_abs_path, file_type)

        # Dynamic column and feedback detection
        detected_cols = detect_all_columns(df)
        fb_col, fb_conf, fb_reason = detect_feedback_column(df)

        # Calculate deterministic quality metrics
        quality_rep = calculate_data_quality(
            df=df,
            detected_columns=detected_cols,
            feedback_column=fb_col,
            feedback_confidence=fb_conf,
        )

        dataset.row_count = int(len(df))
        dataset.column_count = int(len(df.columns))
        dataset.feedback_column = fb_col
        dataset.feedback_confidence = fb_conf
        dataset.quality_score = quality_rep["quality_score"]
        dataset.quality_report = quality_rep
        dataset.status = DatasetStatus.READY.value
        dataset.quality_checked_at = datetime.utcnow()
        dataset.error_message = None

        db.commit()
        db.refresh(dataset)
        return dataset

    except FileValidationError as e:
        # User-correctable validation error during parsing
        dataset.status = DatasetStatus.FAILED.value
        dataset.error_message = str(e)
        db.commit()
        db.refresh(dataset)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error processing dataset {dataset.id}: {str(e)}")
        dataset.status = DatasetStatus.FAILED.value
        dataset.error_message = "Dataset parsing and quality analysis failed."
        db.commit()
        db.refresh(dataset)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to parse dataset structure.",
        )


def list_user_datasets(
    user_id: int,
    include_archived: bool,
    db: Session,
) -> list[Dataset]:
    """Retrieve datasets owned strictly by the authenticated user."""
    query = db.query(Dataset).filter(Dataset.owner_id == user_id)
    if not include_archived:
        query = query.filter(Dataset.status != DatasetStatus.ARCHIVED.value)
    return query.order_by(Dataset.created_at.desc()).all()


def get_user_dataset_by_id(
    dataset_id: int,
    user_id: int,
    db: Session,
) -> Dataset:
    """
    Retrieve single dataset owned by user_id.
    Raises HTTP 404 on non-existent or cross-user attempts to prevent enumeration.
    """
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.owner_id == user_id)
        .first()
    )
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )
    return dataset


def update_dataset_name(
    dataset: Dataset,
    new_name: str,
    db: Session,
) -> Dataset:
    """Rename user's dataset without changing physical storage path."""
    dataset.name = new_name.strip()
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    return dataset


def archive_dataset(
    dataset: Dataset,
    db: Session,
) -> Dataset:
    """Mark dataset as ARCHIVED."""
    dataset.status = DatasetStatus.ARCHIVED.value
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    return dataset


def restore_dataset(
    dataset: Dataset,
    db: Session,
) -> Dataset:
    """Restore an archived dataset back to READY."""
    if dataset.status != DatasetStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only archived datasets can be restored.",
        )
    dataset.status = DatasetStatus.READY.value
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    return dataset


def delete_dataset(
    dataset: Dataset,
    db: Session,
    storage: StorageService,
) -> None:
    """Safely delete dataset record and associated stored file."""
    try:
        storage.delete_file(dataset.storage_path)
    except Exception as e:
        logger.warning(f"Failed to delete stored file {dataset.storage_path}: {str(e)}")

    db.delete(dataset)
    db.commit()


def get_dataset_preview(
    dataset: Dataset,
    storage: StorageService,
    max_rows: int = 15,
) -> dict[str, Any]:
    """
    Generate sanitized preview rows for the user's dataset.
    Masks sensitive/PII columns.
    """
    if dataset.status != DatasetStatus.READY.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data preview is only available for READY datasets.",
        )

    file_abs_path = storage.get_file_path(dataset.storage_path)
    df = ingest_tabular_file(file_abs_path, dataset.file_type)
    detected_cols = detect_all_columns(df)
    return generate_sanitized_preview(df, detected_cols, max_rows=max_rows)
