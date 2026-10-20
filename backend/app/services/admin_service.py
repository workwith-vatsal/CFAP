import math
from datetime import datetime
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.audit_log import AuditLog
from backend.app.models.dataset import Dataset
from backend.app.models.report import Report
from backend.app.models.user import User
from backend.app.schemas.admin import (
    AdminAuditLogListItem,
    AdminAuditLogListResponse,
    AdminSystemOverviewResponse,
    AdminUserListItem,
    AdminUserListResponse,
)
from backend.app.services.audit_service import AuditService


class AdminService:
    @classmethod
    def get_system_overview(cls, db: Session) -> AdminSystemOverviewResponse:
        """
        Aggregate real system-wide operational metrics for the administrative dashboard.
        """
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        verified_users = db.query(func.count(User.id)).filter(User.is_verified == True).scalar() or 0
        admin_users = db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0

        total_datasets = db.query(func.count(Dataset.id)).scalar() or 0
        total_dataset_rows = db.query(func.sum(Dataset.row_count)).scalar() or 0

        total_analyses = db.query(func.count(Analysis.id)).scalar() or 0
        completed_analyses = (
            db.query(func.count(Analysis.id))
            .filter(Analysis.status == AnalysisStatus.COMPLETED)
            .scalar()
            or 0
        )
        failed_analyses = (
            db.query(func.count(Analysis.id))
            .filter(Analysis.status == AnalysisStatus.FAILED)
            .scalar()
            or 0
        )
        processing_analyses = (
            db.query(func.count(Analysis.id))
            .filter(Analysis.status == AnalysisStatus.PROCESSING)
            .scalar()
            or 0
        )

        total_reports = db.query(func.count(Report.id)).scalar() or 0

        # Recent activities from audit logs (top 8)
        recent_logs = (
            db.query(AuditLog, User.email)
            .outerjoin(User, AuditLog.user_id == User.id)
            .order_by(AuditLog.created_at.desc())
            .limit(8)
            .all()
        )

        recent_activities = []
        for log, user_email in recent_logs:
            recent_activities.append(
                {
                    "id": log.id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "status": log.status,
                    "user_email": user_email or "System / Anonymous",
                    "created_at": log.created_at.isoformat(),
                }
            )

        return AdminSystemOverviewResponse(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            admin_users=admin_users,
            total_datasets=total_datasets,
            total_dataset_rows=total_dataset_rows,
            total_analyses=total_analyses,
            completed_analyses=completed_analyses,
            failed_analyses=failed_analyses,
            processing_analyses=processing_analyses,
            total_reports=total_reports,
            system_status="operational",
            database_connected=True,
            recent_activities=recent_activities,
        )

    @classmethod
    def list_users(
        cls,
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> AdminUserListResponse:
        """
        List platform users with operational metadata (zero credentials).
        """
        page = max(1, page)
        limit = max(1, min(100, limit))

        query = db.query(User)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.email.ilike(term),
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                )
            )

        if role and role.strip():
            query = query.filter(User.role == role.strip().lower())

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        total = query.count()
        total_pages = math.ceil(total / limit) if total > 0 else 1

        users = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        items: list[AdminUserListItem] = []
        for u in users:
            ds_count = db.query(func.count(Dataset.id)).filter(Dataset.owner_id == u.id).scalar() or 0
            an_count = db.query(func.count(Analysis.id)).filter(Analysis.owner_id == u.id).scalar() or 0

            items.append(
                AdminUserListItem(
                    id=u.id,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    email=u.email,
                    role=u.role,
                    is_active=u.is_active,
                    is_verified=u.is_verified,
                    auth_provider=u.auth_provider,
                    dataset_count=ds_count,
                    analysis_count=an_count,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
            )

        return AdminUserListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    @classmethod
    def update_user_status(
        cls,
        db: Session,
        target_user_id: int,
        is_active: bool,
        admin_user: User,
    ) -> AdminUserListItem:
        """
        Activate or deactivate a user account with admin self-deactivation protection.
        """
        # Guard: Admin cannot deactivate their own account
        if target_user_id == admin_user.id and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot deactivate their own account.",
            )

        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        target_user.is_active = is_active
        db.commit()
        db.refresh(target_user)

        action_name = "ACCOUNT_ACTIVATED" if is_active else "ACCOUNT_DEACTIVATED"
        AuditService.log_event(
            db=db,
            action=action_name,
            resource_type="user",
            resource_id=str(target_user.id),
            user_id=admin_user.id,
            status="SUCCESS",
            metadata={
                "target_user_id": target_user.id,
                "target_email": target_user.email,
                "is_active": is_active,
            },
        )

        ds_count = db.query(func.count(Dataset.id)).filter(Dataset.owner_id == target_user.id).scalar() or 0
        an_count = db.query(func.count(Analysis.id)).filter(Analysis.owner_id == target_user.id).scalar() or 0

        return AdminUserListItem(
            id=target_user.id,
            first_name=target_user.first_name,
            last_name=target_user.last_name,
            email=target_user.email,
            role=target_user.role,
            is_active=target_user.is_active,
            is_verified=target_user.is_verified,
            auth_provider=target_user.auth_provider,
            dataset_count=ds_count,
            analysis_count=an_count,
            created_at=target_user.created_at,
            updated_at=target_user.updated_at,
        )

    @classmethod
    def list_audit_logs(
        cls,
        db: Session,
        page: int = 1,
        limit: int = 20,
        action: str | None = None,
        resource_type: str | None = None,
        status_filter: str | None = None,
        user_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AdminAuditLogListResponse:
        """
        Retrieve paginated audit logs with search filters.
        """
        page = max(1, page)
        limit = max(1, min(100, limit))

        query = db.query(AuditLog, User.email).outerjoin(User, AuditLog.user_id == User.id)

        if action and action.strip():
            query = query.filter(AuditLog.action == action.strip().upper())

        if resource_type and resource_type.strip():
            query = query.filter(AuditLog.resource_type == resource_type.strip().lower())

        if status_filter and status_filter.strip():
            query = query.filter(AuditLog.status == status_filter.strip().upper())

        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        total = query.count()
        total_pages = math.ceil(total / limit) if total > 0 else 1

        results = (
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        items: list[AdminAuditLogListItem] = []
        for log, user_email in results:
            items.append(
                AdminAuditLogListItem(
                    id=log.id,
                    user_id=log.user_id,
                    user_email=user_email,
                    action=log.action,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    status=log.status,
                    ip_hash=log.ip_hash,
                    metadata_json=log.metadata_json,
                    created_at=log.created_at,
                )
            )

        return AdminAuditLogListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )
