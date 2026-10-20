from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


class AdminSystemOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    admin_users: int
    total_datasets: int
    total_dataset_rows: int
    total_analyses: int
    completed_analyses: int
    failed_analyses: int
    processing_analyses: int
    total_reports: int
    system_status: str = "operational"
    database_connected: bool = True
    recent_activities: list[dict[str, Any]] = []


class AdminUserListItem(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    is_active: bool
    is_verified: bool
    auth_provider: str
    dataset_count: int
    analysis_count: int
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminAuditLogListItem(BaseModel):
    id: int
    user_id: int | None = None
    user_email: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    status: str
    ip_hash: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminAuditLogListItem]
    total: int
    page: int
    limit: int
    total_pages: int
