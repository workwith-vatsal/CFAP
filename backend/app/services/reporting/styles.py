"""
CFAP Reporting Styles and Canvas Engine.
Defines publication-grade typography, color palettes, spacing metrics,
and the NumberedCanvas for dynamic two-pass total page numbering and running headers/footers.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from typing import Dict, Any


# ---------------------------------------------------------
# CFAP Official Color Palette
# ---------------------------------------------------------
COLOR_PRIMARY = colors.HexColor("#4338CA")       # Indigo-700
COLOR_PRIMARY_DARK = colors.HexColor("#312E81")  # Indigo-900
COLOR_PRIMARY_LIGHT = colors.HexColor("#EEF2FF") # Indigo-50
COLOR_SECONDARY = colors.HexColor("#0F172A")     # Slate-900
COLOR_TEXT_DARK = colors.HexColor("#1E293B")     # Slate-800
COLOR_TEXT_MUTED = colors.HexColor("#64748B")    # Slate-500
COLOR_BORDER = colors.HexColor("#E2E8F0")        # Slate-200
COLOR_BG_LIGHT = colors.HexColor("#F8FAFC")      # Slate-50
COLOR_WHITE = colors.HexColor("#FFFFFF")

# Accents for Analytics
COLOR_SUCCESS = colors.HexColor("#10B981")       # Emerald-500
COLOR_DANGER = colors.HexColor("#EF4444")        # Rose-500
COLOR_WARNING = colors.HexColor("#F59E0B")       # Amber-500
COLOR_INFO = colors.HexColor("#3B82F6")          # Blue-500


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas for dynamic total page numbering ('Page X of Y')
    and professional running headers and footers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        # Omit headers and footers on the cover page (Page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_TEXT_MUTED)

        # ---------------------------------------------------------
        # Running Header
        # ---------------------------------------------------------
        header_y = self._pagesize[1] - 36
        self.drawString(54, header_y, "CFAP — Cognitive Feedback Analytics Platform")
        self.drawRightString(self._pagesize[0] - 54, header_y, "Intelligence & Diagnostic Report")

        # Top border rule
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.75)
        self.line(54, header_y - 6, self._pagesize[0] - 54, header_y - 6)

        # ---------------------------------------------------------
        # Running Footer
        # ---------------------------------------------------------
        footer_y = 36
        # Bottom border rule
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.75)
        self.line(54, footer_y + 14, self._pagesize[0] - 54, footer_y + 14)

        self.drawString(54, footer_y, "CONFIDENTIAL & PROPRIETARY | FOR INTERNAL USE ONLY")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(self._pagesize[0] - 54, footer_y, page_str)

        self.restoreState()


def get_report_styles() -> Dict[str, ParagraphStyle]:
    """
    Builds and returns the comprehensive dictionary of ReportLab paragraph styles
    configured with CFAP brand typography, leading, and colors.
    """
    base = getSampleStyleSheet()

    styles = {
        # Cover Styles
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=COLOR_WHITE,
            alignment=TA_LEFT,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=14,
            leading=20,
            textColor=COLOR_PRIMARY_LIGHT,
            alignment=TA_LEFT,
        ),
        "CoverBadge": ParagraphStyle(
            "CoverBadge",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=COLOR_PRIMARY,
            alignment=TA_CENTER,
        ),
        "CoverMetaLabel": ParagraphStyle(
            "CoverMetaLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=COLOR_TEXT_MUTED,
        ),
        "CoverMetaVal": ParagraphStyle(
            "CoverMetaVal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=COLOR_TEXT_DARK,
        ),

        # Section Headings
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=COLOR_PRIMARY_DARK,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "SubSectionHeading": ParagraphStyle(
            "SubSectionHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=COLOR_SECONDARY,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),

        # Body & Content
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=COLOR_TEXT_DARK,
            spaceAfter=6,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=14,
            textColor=COLOR_TEXT_DARK,
        ),
        "BodyMuted": ParagraphStyle(
            "BodyMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=COLOR_TEXT_MUTED,
        ),
        "CodeText": ParagraphStyle(
            "CodeText",
            parent=base["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            textColor=COLOR_TEXT_DARK,
        ),

        # KPI & Metric Card Styles
        "MetricLabel": ParagraphStyle(
            "MetricLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=COLOR_TEXT_MUTED,
            alignment=TA_CENTER,
        ),
        "MetricValue": ParagraphStyle(
            "MetricValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=COLOR_PRIMARY_DARK,
            alignment=TA_CENTER,
        ),
        "MetricSubtext": ParagraphStyle(
            "MetricSubtext",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=COLOR_TEXT_MUTED,
            alignment=TA_CENTER,
        ),

        # Tables
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_WHITE,
            alignment=TA_LEFT,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_DARK,
            alignment=TA_LEFT,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_DARK,
            alignment=TA_LEFT,
        ),
        "TableCellMuted": ParagraphStyle(
            "TableCellMuted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=COLOR_TEXT_MUTED,
            alignment=TA_LEFT,
        ),
        "TableCellCenter": ParagraphStyle(
            "TableCellCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_DARK,
            alignment=TA_CENTER,
        ),

        # Callouts & Notices
        "CalloutTitle": ParagraphStyle(
            "CalloutTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=COLOR_PRIMARY_DARK,
        ),
        "CalloutBody": ParagraphStyle(
            "CalloutBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=COLOR_TEXT_DARK,
        ),
        "UnavailableNotice": ParagraphStyle(
            "UnavailableNotice",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=13,
            textColor=COLOR_TEXT_MUTED,
            alignment=TA_LEFT,
        ),
    }

    return styles
