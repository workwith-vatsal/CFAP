from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.dataset import DatasetStatus


class ColumnQualityInfo(BaseModel):
    name: str
    detected_type: str
    raw_dtype: str
    null_count: int
    null_percentage: float
    unique_count: int
    is_sensitive: bool = False


class ScoreBreakdown(BaseModel):
    usable_feedback_score: float
    completeness_score: float
    uniqueness_score: float
    structure_score: float


class DataQualityReport(BaseModel):
    rows: int
    columns: int
    usable_rows: int
    invalid_rows: int
    duplicate_rows: int
    missing_values: int
    feedback_column: str | None = None
    feedback_confidence: float | None = None
    missing_feedback: int = 0
    blank_feedback: int = 0
    quality_score: float
    score_breakdown: ScoreBreakdown
    columns_detail: list[ColumnQualityInfo] = Field(default_factory=list, alias="columns")

    model_config = ConfigDict(populate_by_name=True)


class DatasetSummaryResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    row_count: int
    column_count: int
    status: str
    feedback_column: str | None = None
    feedback_confidence: float | None = None
    quality_score: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetDetailResponse(DatasetSummaryResponse):
    error_message: str | None = None
    quality_checked_at: datetime | None = None
    quality_report: dict[str, Any] | None = None


class DatasetListResponse(BaseModel):
    datasets: list[DatasetSummaryResponse]
    total: int


class DatasetUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class DataPreviewResponse(BaseModel):
    columns: list[str]
    total_preview_rows: int
    rows: list[dict[str, Any]]
