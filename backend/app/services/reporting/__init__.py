"""
CFAP Reporting Package.
Provides data assembly, style definitions, server-side charts, PDF generation,
and report service orchestration.
"""

from backend.app.services.reporting.report_data import ReportDataBuilder
from backend.app.services.reporting.styles import NumberedCanvas, get_report_styles
from backend.app.services.reporting.charts import ReportChartGenerator
from backend.app.services.reporting.pdf_generator import PDFReportGenerator
from backend.app.services.reporting.report_service import ReportService

__all__ = [
    "ReportDataBuilder",
    "NumberedCanvas",
    "get_report_styles",
    "ReportChartGenerator",
    "PDFReportGenerator",
    "ReportService",
]
