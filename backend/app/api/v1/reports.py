"""
FastAPI router for Report generation, metadata, history, and PDF download endpoints.
Strictly enforces tenant isolation and ownership authorization.
"""

import logging
import threading
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_verified_user
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.report import ReportCreateRequest, ReportListResponse, ReportResponse
from backend.app.services.reporting.report_service import ReportService
from backend.app.tasks.report_tasks import execute_report_generation, generate_pdf_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reporting & Export"])


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new intelligence report",
)
def create_report(
    req: ReportCreateRequest,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Creates and enqueues a new PDF intelligence report (FULL, EXECUTIVE, or ANALYSIS).
    Enforces that the user owns the dataset and the analysis is completed.
    """
    try:
        report = ReportService.create_report(
            user=current_user,
            dataset_id=req.dataset_id,
            analysis_id=req.analysis_id,
            report_type=req.report_type,
            db=db,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )

    # Dispatch to Celery background worker with fallback to background thread
    try:
        generate_pdf_report.delay(report.id)
        logger.info("Dispatched Report #%d to Celery worker.", report.id)
    except Exception as celery_err:
        logger.warning(
            "Celery dispatch failed (%s), starting background thread fallback for report #%d.",
            celery_err,
            report.id,
        )
        thread = threading.Thread(
            target=execute_report_generation,
            args=(report.id,),
            daemon=True,
        )
        thread.start()

    return report


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List all reports for the current user",
)
def list_reports(
    dataset_id: Optional[int] = Query(None, description="Filter by dataset ID"),
    analysis_id: Optional[int] = Query(None, description="Filter by analysis ID"),
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Lists all generated and queued reports belonging to the authenticated user.
    """
    reports = ReportService.list_reports(
        user=current_user,
        db=db,
        dataset_id=dataset_id,
        analysis_id=analysis_id,
    )
    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=len(reports),
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report metadata and status by ID",
)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the status, metadata, and file size of a specific report.
    """
    report = ReportService.get_report(report_id, current_user, db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or access denied.",
        )
    return report


@router.get(
    "/{report_id}/download",
    summary="Download the generated PDF report",
)
def download_report_pdf(
    report_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Downloads the verified PDF report binary with appropriate Content-Disposition headers.
    Enforces tenant authorization and completed status.
    """
    try:
        filename, pdf_bytes = ReportService.get_report_download(report_id, current_user, db)
    except ValueError as err:
        err_msg = str(err)
        if "not found" in err_msg.lower() or "denied" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.delete(
    "/{report_id}",
    summary="Delete a report",
)
def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_active_verified_user),
    db: Session = Depends(get_db),
):
    """
    Deletes the report database record and removes the persisted PDF artifact.
    """
    success = ReportService.delete_report(report_id, current_user, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or access denied.",
        )
    return {"message": "Report deleted successfully", "id": report_id}
