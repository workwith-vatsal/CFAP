"""
Pydantic schemas for Report generation, status tracking, and metadata responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReportCreateRequest(BaseModel):
    dataset_id: int = Field(..., description="ID of the dataset associated with the report")
    analysis_id: int = Field(..., description="ID of the completed analysis to report on")
    report_type: str = Field(
        default="FULL",
        description="Type of report to generate: FULL, EXECUTIVE, or ANALYSIS",
    )


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    dataset_id: int
    analysis_id: int
    report_type: str
    status: str
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
