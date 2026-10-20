"""
Celery asynchronous task handlers for PDF report generation.
Supports both async background worker execution and direct synchronous execution.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.celery_app import celery_app
from backend.app.db.database import SessionLocal
from backend.app.services.reporting.report_service import ReportService

logger = logging.getLogger(__name__)


def execute_report_generation(report_id: int, db: Optional[Session] = None) -> bool:
    """
    Executes report data collection and PDF rendering.
    Can be run directly or within a Celery background worker.
    """
    close_db_when_done = False
    if db is None:
        db = SessionLocal()
        close_db_when_done = True

    try:
        logger.info("Starting report generation for Report ID: %d", report_id)
        report = ReportService.generate_and_store_report(report_id, db)
        logger.info("Report #%d completed successfully. Size: %d bytes", report.id, report.file_size_bytes or 0)
        return True
    except Exception as e:
        logger.error("Error executing report generation for Report ID %d: %s", report_id, str(e), exc_info=True)
        return False
    finally:
        if close_db_when_done:
            db.close()


@celery_app.task(bind=True, name="generate_pdf_report")
def generate_pdf_report(self, report_id: int):
    """
    Celery background worker entrypoint for generating PDF reports.
    """
    logger.info("Celery worker processing PDF report #%d", report_id)
    return execute_report_generation(report_id)
