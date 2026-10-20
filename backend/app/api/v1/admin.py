from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_admin
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.admin import (
    AdminAuditLogListResponse,
    AdminSystemOverviewResponse,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserStatusUpdate,
)
from backend.app.services.admin_service import AdminService
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.get(
    "/overview",
    response_model=AdminSystemOverviewResponse,
    summary="Retrieve system-wide operational statistics",
)
def get_system_overview(
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieve real aggregate system overview metrics (users, datasets, analyses, reports, health).
    """
    return AdminService.get_system_overview(db=db)


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List platform users with operational metadata",
)
def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name or email"),
    role: str | None = Query(None, description="Filter by role (user, admin)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List registered platform users with dataset/analysis counts (zero credential material).
    """
    return AdminService.list_users(
        db=db,
        page=page,
        limit=limit,
        search=search,
        role=role,
        is_active=is_active,
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserListItem,
    summary="Update user active/disabled status",
)
def update_user_status(
    request: Request,
    user_id: int,
    payload: AdminUserStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Activate or deactivate a user account with admin self-deactivation protection.
    """
    return AdminService.update_user_status(
        db=db,
        target_user_id=user_id,
        is_active=payload.is_active,
        admin_user=current_admin,
    )


@router.get(
    "/audit-logs",
    response_model=AdminAuditLogListResponse,
    summary="List system security audit logs",
)
def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    action: str | None = Query(None, description="Filter by action name"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    start_date: datetime | None = Query(None, description="Filter by start date ISO"),
    end_date: datetime | None = Query(None, description="Filter by end date ISO"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieve paginated security audit logs with action and date filters.
    """
    return AdminService.list_audit_logs(
        db=db,
        page=page,
        limit=limit,
        action=action,
        resource_type=resource_type,
        status_filter=status_filter,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
