"""
Report Service for CFAP.
Manages report lifecycle, database transactions, background task orchestration,
and tenant-isolated PDF storage.
"""

from datetime import datetime
import logging
from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset
from backend.app.models.report import Report, ReportStatus, ReportType
from backend.app.models.user import User
from backend.app.services.reporting.pdf_generator import PDFReportGenerator
from backend.app.services.reporting.report_data import ReportDataBuilder
from backend.app.services.storage.local import LocalStorageService

logger = logging.getLogger(__name__)


class ReportService:
    """Orchestrates report lifecycle, validation, PDF compilation, and storage."""

    @classmethod
    def create_report(
        cls,
        user: User,
        dataset_id: int,
        analysis_id: int,
        report_type: str,
        db: Session,
    ) -> Report:
        """
        Validates ownership and completed status before queueing a report record.
        """
        # Validate dataset ownership
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id, Dataset.owner_id == user.id)
            .first()
        )
        if not dataset:
            raise ValueError("Dataset not found or access denied.")

        # Validate analysis association & completion
        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.id == analysis_id,
                Analysis.dataset_id == dataset.id,
            )
            .first()
        )
        if not analysis:
            raise ValueError("Analysis not found for the specified dataset.")

        # Verify completed status (case-insensitive check)
        status_val = str(analysis.status.value if hasattr(analysis.status, "value") else analysis.status).lower()
        if status_val != "completed":
            raise ValueError(f"Cannot generate report for analysis with status '{status_val}'. Analysis must be completed.")

        # Validate report type enum
        try:
            rtype_enum = ReportType[report_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid report type '{report_type}'. Must be one of: FULL, EXECUTIVE, ANALYSIS.")

        # Create Report entry in QUEUED state
        report = Report(
            user_id=user.id,
            dataset_id=dataset.id,
            analysis_id=analysis.id,
            report_type=rtype_enum,
            status=ReportStatus.QUEUED,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return report

    @classmethod
    def generate_and_store_report(
        cls,
        report_id: int,
        db: Session,
    ) -> Report:
        """
        Synchronous/task execution: Compiles analytics data, renders PDF, and stores file.
        """
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report ID {report_id} not found.")

        try:
            report.status = ReportStatus.PROCESSING
            db.commit()

            dataset = db.query(Dataset).filter(Dataset.id == report.dataset_id).first()
            analysis = db.query(Analysis).filter(Analysis.id == report.analysis_id).first()
            user = db.query(User).filter(User.id == report.user_id).first()

            if not dataset or not analysis or not user:
                raise ValueError("Associated dataset, analysis, or user record is missing.")

            rtype_str = report.report_type.value.lower() if hasattr(report.report_type, "value") else str(report.report_type).lower()

            # 1. Build verified report data payload
            report_data = ReportDataBuilder.build_report_data(
                analysis=analysis,
                dataset=dataset,
                current_user=user,
                db=db,
                report_type=rtype_str,
            )

            # 2. Render PDF with ReportLab
            pdf_bytes = PDFReportGenerator.generate_pdf(
                report_data=report_data,
                report_type=rtype_str,
            )

            if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
                raise ValueError("Generated PDF bytes are invalid or empty.")

            # 3. Store file with tenant-isolated path
            storage = LocalStorageService()
            unique_token = uuid4().hex[:12]
            relative_path = f"reports/users/{user.id}/analyses/{analysis.id}/report_{unique_token}_{rtype_str}.pdf"

            stored_path = storage.save_file(pdf_bytes, relative_path)
            file_size = len(pdf_bytes)

            # 4. Update Report record
            report.file_path = stored_path
            report.file_size_bytes = file_size
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            report.error_message = None
            db.commit()
            db.refresh(report)

            logger.info("Successfully generated report #%d (%s, %d bytes)", report.id, rtype_str, file_size)
            return report

        except Exception as e:
            logger.error("Failed to generate report #%d: %s", report_id, str(e), exc_info=True)
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            db.commit()
            db.refresh(report)
            raise e

    @classmethod
    def list_reports(
        cls,
        user: User,
        db: Session,
        dataset_id: Optional[int] = None,
        analysis_id: Optional[int] = None,
    ) -> List[Report]:
        """Lists reports owned by the current user."""
        query = db.query(Report).filter(Report.user_id == user.id)

        if dataset_id is not None:
            query = query.filter(Report.dataset_id == dataset_id)
        if analysis_id is not None:
            query = query.filter(Report.analysis_id == analysis_id)

        return query.order_by(Report.created_at.desc()).all()

    @classmethod
    def get_report(cls, report_id: int, user: User, db: Session) -> Optional[Report]:
        """Fetches a specific report enforcing tenant ownership."""
        return (
            db.query(Report)
            .filter(Report.id == report_id, Report.user_id == user.id)
            .first()
        )

    @classmethod
    def delete_report(cls, report_id: int, user: User, db: Session) -> bool:
        """Deletes a report and its underlying storage artifact."""
        report = cls.get_report(report_id, user, db)
        if not report:
            return False

        if report.file_path:
            storage = LocalStorageService()
            storage.delete_file(report.file_path)

        db.delete(report)
        db.commit()
        return True

    @classmethod
    def get_report_download(
        cls,
        report_id: int,
        user: User,
        db: Session,
    ) -> Tuple[str, bytes]:
        """
        Retrieves filename and raw PDF bytes for authenticated download.
        """
        report = cls.get_report(report_id, user, db)
        if not report:
            raise ValueError("Report not found or access denied.")

        if report.status != ReportStatus.COMPLETED or not report.file_path:
            raise ValueError("Report generation is not yet completed or file is missing.")

        storage = LocalStorageService()
        pdf_bytes = storage.get_file(report.file_path)

        # Generate clean human-readable download filename
        rtype_str = report.report_type.value.lower() if hasattr(report.report_type, "value") else str(report.report_type).lower()
        filename = f"CFAP_{rtype_str.capitalize()}_Report_Analysis_{report.analysis_id}.pdf"

        return filename, pdf_bytes
