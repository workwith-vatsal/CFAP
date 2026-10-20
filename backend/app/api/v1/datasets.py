from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_verified_user
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import MessageResponse
from backend.app.schemas.dataset import (
    DataPreviewResponse,
    DataQualityReport,
    DatasetDetailResponse,
    DatasetListResponse,
    DatasetSummaryResponse,
    DatasetUpdate,
)
from backend.app.services.dataset_service import (
    archive_dataset,
    create_and_process_dataset,
    delete_dataset,
    get_dataset_preview,
    get_user_dataset_by_id,
    list_user_datasets,
    restore_dataset,
    update_dataset_name,
)
from backend.app.services.storage import StorageService, get_storage_service

router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)


@router.post(
    "/upload",
    response_model=DatasetDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """
    Upload and process a customer feedback dataset (.csv or .xlsx).
    Performs dynamic column detection, feedback classification, and deterministic quality analysis.
    """
    file_bytes = await file.read()

    dataset = create_and_process_dataset(
        user=current_user,
        file_bytes=file_bytes,
        original_filename=file.filename or "uploaded_dataset.csv",
        content_type=file.content_type,
        custom_name=name,
        db=db,
        storage=storage,
    )

    return dataset


@router.get(
    "",
    response_model=DatasetListResponse,
)
def get_datasets(
    include_archived: bool = Query(False, description="Include archived datasets"),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    List all datasets owned by the authenticated user.
    Strictly tenant-isolated.
    """
    datasets = list_user_datasets(
        user_id=current_user.id,
        include_archived=include_archived,
        db=db,
    )
    return DatasetListResponse(
        datasets=[DatasetSummaryResponse.model_validate(d) for d in datasets],
        total=len(datasets),
    )


@router.get(
    "/{dataset_id}",
    response_model=DatasetDetailResponse,
)
def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve single dataset metadata and quality report.
    Enforces multi-tenant ownership.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    return dataset


@router.get(
    "/{dataset_id}/quality",
    response_model=DataQualityReport,
)
def get_dataset_quality(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full data quality analysis report for the dataset.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    if not dataset.quality_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality report not available for this dataset.",
        )
    return dataset.quality_report


@router.get(
    "/{dataset_id}/preview",
    response_model=DataPreviewResponse,
)
def get_dataset_data_preview(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """
    Retrieve a privacy-sanitized tabular preview of the first 15 rows.
    Obvious PII columns are masked.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    preview = get_dataset_preview(
        dataset=dataset,
        storage=storage,
        max_rows=15,
    )
    return preview


@router.patch(
    "/{dataset_id}",
    response_model=DatasetSummaryResponse,
)
def rename_dataset(
    dataset_id: int,
    data: DatasetUpdate,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Rename user's dataset.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    updated = update_dataset_name(
        dataset=dataset,
        new_name=data.name,
        db=db,
    )
    return updated


@router.post(
    "/{dataset_id}/archive",
    response_model=DatasetSummaryResponse,
)
def archive_user_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Archive user's dataset.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    archived = archive_dataset(
        dataset=dataset,
        db=db,
    )
    return archived


@router.post(
    "/{dataset_id}/restore",
    response_model=DatasetSummaryResponse,
)
def restore_user_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Restore an archived dataset back to READY.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    restored = restore_dataset(
        dataset=dataset,
        db=db,
    )
    return restored


@router.delete(
    "/{dataset_id}",
    response_model=MessageResponse,
)
def delete_user_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """
    Permanently delete dataset record and physical file from storage.
    """
    dataset = get_user_dataset_by_id(
        dataset_id=dataset_id,
        user_id=current_user.id,
        db=db,
    )
    delete_dataset(
        dataset=dataset,
        db=db,
        storage=storage,
    )
    return MessageResponse(
        message="Dataset deleted successfully.",
    )
