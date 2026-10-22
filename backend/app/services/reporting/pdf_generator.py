"""
Professional PDF Report Generator for CFAP.
Constructs publication-grade intelligence reports using ReportLab Platypus architecture,
server-side chart embedding, strict multi-tenant isolation, and two-pass canvas layout.
"""

import io
import logging
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.app.services.reporting.charts import ReportChartGenerator
from backend.app.services.reporting.styles import (
    COLOR_BG_LIGHT,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_PRIMARY_DARK,
    COLOR_PRIMARY_LIGHT,
    COLOR_SECONDARY,
    COLOR_SUCCESS,
    COLOR_TEXT_DARK,
    COLOR_TEXT_MUTED,
    COLOR_WARNING,
    COLOR_WHITE,
    NumberedCanvas,
    get_report_styles,
)

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Renders verified analytics data into publication-grade PDF documents.
    Supports FULL, EXECUTIVE, and ANALYSIS report templates.
    """

    PAGE_WIDTH = 612  # Letter width
    PAGE_HEIGHT = 792 # Letter height
    MARGIN = 36       # 0.5 inch margins
    PRINTABLE_WIDTH = PAGE_WIDTH - (MARGIN * 2) # 540pt

    @classmethod
    def generate_pdf(cls, report_data: Dict[str, Any], report_type: str = "full") -> bytes:
        """
        Builds and returns the PDF document as raw bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=cls.MARGIN,
            rightMargin=cls.MARGIN,
            topMargin=44,
            bottomMargin=44,
            title=f"CFAP Report - {report_data.get('metadata', {}).get('dataset_name', 'Analytics')}",
            author="Cognitive Feedback Analytics Platform",
        )

        styles = get_report_styles()
        story: List[Any] = []

        rtype = report_type.lower()

        # 1. Cover Page (Common to all reports)
        cls._build_cover_page(story, report_data, styles, rtype)

        # 2. Executive Summary & KPIs (Common to all reports)
        cls._build_executive_summary_section(story, report_data, styles)

        if rtype == "executive":
            # Executive Report: Compact overview
            cls._build_executive_compact_analytics(story, report_data, styles)
            cls._build_strategic_insights_section(story, report_data, styles)
            cls._build_data_quality_summary_section(story, report_data, styles)
            cls._build_governance_disclaimer(story, styles)
        elif rtype == "analysis":
            # Analysis Report: In-depth technical breakdown
            cls._build_sentiment_section(story, report_data, styles)
            cls._build_emotion_section(story, report_data, styles)
            cls._build_topics_section(story, report_data, styles)
            cls._build_cross_dimensional_section(story, report_data, styles)
            cls._build_temporal_section(story, report_data, styles)
            cls._build_categorical_section(story, report_data, styles)
            cls._build_explainability_section(story, report_data, styles)
            cls._build_methodology_section(story, report_data, styles)
            cls._build_governance_disclaimer(story, styles)
        else:
            # Full Report: Comprehensive analytical document
            cls._build_data_quality_section(story, report_data, styles)
            cls._build_methodology_section(story, report_data, styles)
            cls._build_sentiment_section(story, report_data, styles)
            cls._build_emotion_section(story, report_data, styles)
            cls._build_topics_section(story, report_data, styles)
            cls._build_cross_dimensional_section(story, report_data, styles)
            cls._build_temporal_section(story, report_data, styles)
            cls._build_categorical_section(story, report_data, styles)
            cls._build_strategic_insights_section(story, report_data, styles)
            cls._build_explainability_section(story, report_data, styles)
            cls._build_assistant_insights_section(story, report_data, styles)
            cls._build_governance_disclaimer(story, styles)

        # Build PDF using two-pass NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)

        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # -------------------------------------------------------------------------
    # Section Builders
    # -------------------------------------------------------------------------

    @classmethod
    def _build_cover_page(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any], rtype: str):
        meta = data.get("metadata", {})
        type_labels = {
            "full": "FULL COMPREHENSIVE REPORT",
            "executive": "EXECUTIVE SUMMARY REPORT",
            "analysis": "DEEP ANALYTICAL REPORT",
        }
        badge_text = type_labels.get(rtype, "INTELLIGENCE REPORT")

        # Top Branded Header Block
        header_table = Table(
            [
                [Paragraph("<b>COGNITIVE FEEDBACK ANALYTICS PLATFORM</b>", styles["CoverSubtitle"])],
                [Spacer(1, 8)],
                [Paragraph("Customer Feedback Intelligence &amp; Diagnostic Report", styles["CoverTitle"])],
                [Spacer(1, 10)],
                [Paragraph(f"<b>{badge_text}</b>", styles["CoverBadge"])],
            ],
            colWidths=[cls.PRINTABLE_WIDTH],
        )
        header_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARY_DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 28),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 28),
                ("LEFTPADDING", (0, 0), (-1, -1), 24),
                ("RIGHTPADDING", (0, 0), (-1, -1), 24),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ])
        )
        story.append(header_table)
        story.append(Spacer(1, 24))

        # Metadata Card
        meta_rows = [
            [
                Paragraph("<b>Dataset Name:</b>", styles["CoverMetaLabel"]),
                Paragraph(str(meta.get("dataset_name", "N/A")), styles["CoverMetaVal"]),
                Paragraph("<b>Analysis Run ID:</b>", styles["CoverMetaLabel"]),
                Paragraph(f"#{meta.get('analysis_id', 'N/A')}", styles["CoverMetaVal"]),
            ],
            [
                Paragraph("<b>Original File:</b>", styles["CoverMetaLabel"]),
                Paragraph(str(meta.get("original_filename", "N/A")), styles["CoverMetaVal"]),
                Paragraph("<b>Dataset Format:</b>", styles["CoverMetaLabel"]),
                Paragraph(str(meta.get("dataset_format", "CSV")), styles["CoverMetaVal"]),
            ],
            [
                Paragraph("<b>Total Feedback Rows:</b>", styles["CoverMetaLabel"]),
                Paragraph(f"{meta.get('total_rows', 0):,}", styles["CoverMetaVal"]),
                Paragraph("<b>Usable Rows:</b>", styles["CoverMetaLabel"]),
                Paragraph(f"{meta.get('usable_rows', 0):,}", styles["CoverMetaVal"]),
            ],
            [
                Paragraph("<b>Analyzed Text Column:</b>", styles["CoverMetaLabel"]),
                Paragraph(str(meta.get("feedback_column", "Feedback Text")), styles["CoverMetaVal"]),
                Paragraph("<b>Analysis Completed:</b>", styles["CoverMetaLabel"]),
                Paragraph(str(meta.get("analysis_completed_at", "N/A")), styles["CoverMetaVal"]),
            ],
            [
                Paragraph("<b>Report Generated:</b>", styles["CoverMetaLabel"]),
                Paragraph(str(meta.get("report_generated_at", "N/A")), styles["CoverMetaVal"]),
                Paragraph("<b>Prepared For:</b>", styles["CoverMetaLabel"]),
                Paragraph(str(meta.get("generated_by", "Authorized User")), styles["CoverMetaVal"]),
            ],
        ]

        meta_table = Table(meta_rows, colWidths=[120, 150, 120, 150])
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        story.append(meta_table)
        story.append(Spacer(1, 24))

        # Executive Notice Box
        notice_p = Paragraph(
            "<b>Notice:</b> This report contains automated diagnostic and natural language analytics computed by CFAP. "
            "All findings, sentiment distributions, discrete emotion categorizations, and topic representations are "
            "derived through state-of-the-art neural transformer models and verified algorithmic heuristics. "
            "Insights are strictly observational and non-causal.",
            styles["BodyMuted"],
        )
        notice_table = Table([[notice_p]], colWidths=[cls.PRINTABLE_WIDTH])
        notice_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARY_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C7D2FE")),
                ("PADDING", (0, 0), (-1, -1), 12),
            ])
        )
        story.append(notice_table)
        story.append(PageBreak())

    @classmethod
    def _build_executive_summary_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        exec_data = data.get("executive_summary", {})
        story.append(Paragraph("1. Executive Summary &amp; Key Performance Indicators", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        # 4 KPI Cards
        nss = exec_data.get("net_sentiment_score", 0.0)
        nss_str = f"{nss:+.1f}"
        health_score = exec_data.get("brand_health_score", 50.0)
        health_str = f"{health_score:.1f} / 100"

        kpi_table = Table(
            [
                [
                    Paragraph("USABLE FEEDBACK", styles["MetricLabel"]),
                    Paragraph("NET SENTIMENT (NSS)", styles["MetricLabel"]),
                    Paragraph("DOMINANT EMOTION", styles["MetricLabel"]),
                    Paragraph("BRAND HEALTH SCORE*", styles["MetricLabel"]),
                ],
                [
                    Paragraph(f"{exec_data.get('usable_feedback', 0):,}", styles["MetricValue"]),
                    Paragraph(nss_str, styles["MetricValue"]),
                    Paragraph(str(exec_data.get("dominant_emotion", "N/A")).capitalize(), styles["MetricValue"]),
                    Paragraph(health_str, styles["MetricValue"]),
                ],
                [
                    Paragraph(f"{exec_data.get('total_feedback', 0):,} Total Rows", styles["MetricSubtext"]),
                    Paragraph(f"{exec_data.get('positive_ratio', 0.0):.1f}% Positive Ratio", styles["MetricSubtext"]),
                    Paragraph(f"Avg Conf: {exec_data.get('average_confidence', 0.0)*100:.1f}%", styles["MetricSubtext"]),
                    Paragraph("CFAP Composite Metric", styles["MetricSubtext"]),
                ],
            ],
            colWidths=[130, 130, 130, 150],
        )
        kpi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 2),
                ("TOPPADDING", (0, 2), (-1, 2), 2),
                ("BOTTOMPADDING", (0, 2), (-1, 2), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ])
        )
        story.append(kpi_table)
        story.append(Spacer(1, 10))

        # Summary text
        summary_text = exec_data.get("summary_text", "Analysis completed successfully across all usable feedback items.")
        story.append(Paragraph(f"<b>Overview:</b> {summary_text}", styles["Body"]))
        story.append(Paragraph(
            "<font size='7.5' color='#64748B'>* Note: Brand Health Score is a CFAP-derived composite analytical metric combining net sentiment score, positive-to-negative ratio, and confidence weighting. It is not an industry-standard benchmark.</font>",
            styles["BodyMuted"],
        ))
        story.append(Spacer(1, 14))

    @classmethod
    def _build_executive_compact_analytics(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        story.append(Paragraph("2. High-Level Feedback Distributions", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        # Sentiment Donut & Emotion Bar in side-by-side table
        sentiment_chart = ReportChartGenerator.generate_sentiment_donut_chart(
            data.get("sentiment", {}).get("distribution", {}), width_pt=240, height_pt=130
        )
        emotion_chart = ReportChartGenerator.generate_emotion_bar_chart(
            data.get("emotion", {}).get("top_emotions", []), width_pt=260, height_pt=130
        )

        row_content = []
        if sentiment_chart and emotion_chart:
            row_content = [sentiment_chart, emotion_chart]
            chart_table = Table([row_content], colWidths=[265, 275])
            chart_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
            story.append(chart_table)
        elif sentiment_chart:
            story.append(sentiment_chart)
        elif emotion_chart:
            story.append(emotion_chart)

        story.append(Spacer(1, 14))

    @classmethod
    def _build_data_quality_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        dq = data.get("data_quality", {})
        story.append(Paragraph("2. Dataset Validation &amp; Data Quality Foundation", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        quality_score = dq.get("quality_score", 100.0)
        score_color = COLOR_SUCCESS if quality_score >= 80 else (COLOR_WARNING if quality_score >= 60 else COLOR_DANGER)

        # Overview Table
        dq_summary_table = Table(
            [
                [
                    Paragraph("<b>Quality Score</b>", styles["TableCellBold"]),
                    Paragraph(f"<b><font color='{score_color.hexval()}'>{quality_score:.1f}%</font></b>", styles["TableCell"]),
                    Paragraph("<b>Usable Rows</b>", styles["TableCellBold"]),
                    Paragraph(f"{dq.get('usable_rows', 0):,} / {dq.get('total_rows', 0):,}", styles["TableCell"]),
                ],
                [
                    Paragraph("<b>Missing Feedback</b>", styles["TableCellBold"]),
                    Paragraph(f"{dq.get('missing_feedback_count', 0):,}", styles["TableCell"]),
                    Paragraph("<b>Duplicate Rows</b>", styles["TableCellBold"]),
                    Paragraph(f"{dq.get('duplicate_rows', 0):,}", styles["TableCell"]),
                ],
            ],
            colWidths=[120, 150, 120, 150],
        )
        dq_summary_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(dq_summary_table)
        story.append(Spacer(1, 10))

        # Detected Columns Table
        columns = dq.get("columns", [])
        if columns:
            story.append(Paragraph("<b>Detected Schema &amp; Role Classifications:</b>", styles["SubSectionHeading"]))
            col_rows = [[
                Paragraph("Column Name", styles["TableHeader"]),
                Paragraph("Inferred Role", styles["TableHeader"]),
                Paragraph("Data Type", styles["TableHeader"]),
                Paragraph("Missing Count", styles["TableHeader"]),
                Paragraph("Missing %", styles["TableHeader"]),
            ]]
            for c in columns[:10]:
                col_rows.append([
                    Paragraph(c.get("name", ""), styles["TableCell"]),
                    Paragraph(c.get("role", ""), styles["TableCellBold"]),
                    Paragraph(c.get("type", ""), styles["TableCellMuted"]),
                    Paragraph(str(c.get("missing_count", 0)), styles["TableCell"]),
                    Paragraph(f"{c.get('missing_pct', 0.0):.1f}%", styles["TableCell"]),
                ])

            col_table = Table(col_rows, colWidths=[160, 100, 80, 100, 100])
            col_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(col_table)

        story.append(Spacer(1, 14))

    @classmethod
    def _build_data_quality_summary_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        dq = data.get("data_quality", {})
        story.append(Paragraph("4. Dataset &amp; Data Quality Summary", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=8))

        quality_score = dq.get("quality_score", 100.0)
        p = Paragraph(
            f"The analyzed dataset contains <b>{dq.get('total_rows', 0):,}</b> total records, of which "
            f"<b>{dq.get('usable_rows', 0):,}</b> ({dq.get('usable_rows', 0)/max(1, dq.get('total_rows', 1))*100:.1f}%) were validated "
            f"as usable for NLP processing. Overall data quality score: <b>{quality_score:.1f}%</b> with "
            f"{dq.get('missing_feedback_count', 0)} missing feedback values and {dq.get('duplicate_rows', 0)} duplicates removed.",
            styles["Body"],
        )
        story.append(p)
        story.append(Spacer(1, 10))

    @classmethod
    def _build_methodology_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        m = data.get("methodology", {})
        story.append(Paragraph("3. AI/NLP Pipeline Architecture &amp; Methodology", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        rows = [
            [
                Paragraph("<b>Component</b>", styles["TableHeader"]),
                Paragraph("<b>Model / Framework</b>", styles["TableHeader"]),
                Paragraph("<b>Specification &amp; Output Mapping</b>", styles["TableHeader"]),
            ],
            [
                Paragraph("<b>Sentiment Analysis</b>", styles["TableCellBold"]),
                Paragraph(m.get("sentiment_model", "BERT Multilingual"), styles["CodeText"]),
                Paragraph(m.get("sentiment_mapping", "5-star mapped to 3-class"), styles["TableCell"]),
            ],
            [
                Paragraph("<b>Emotion Detection</b>", styles["TableCellBold"]),
                Paragraph(m.get("emotion_model", "DistilRoBERTa"), styles["CodeText"]),
                Paragraph(m.get("emotion_categories", "7 Discrete Emotions"), styles["TableCell"]),
            ],
            [
                Paragraph("<b>Dense Embeddings</b>", styles["TableCellBold"]),
                Paragraph(m.get("embedding_model", "MiniLM-L6-v2"), styles["CodeText"]),
                Paragraph(m.get("embedding_dim", "384-dimensional dense vectors"), styles["TableCell"]),
            ],
            [
                Paragraph("<b>Topic Discovery</b>", styles["TableCellBold"]),
                Paragraph(f"BERTopic v{m.get('bertopic_version', '0.17.4')}", styles["CodeText"]),
                Paragraph(m.get("topic_modeling", "UMAP + HDBSCAN density clustering"), styles["TableCell"]),
            ],
            [
                Paragraph("<b>Explainability</b>", styles["TableCellBold"]),
                Paragraph("SHAP Tree/Linear Kernel", styles["CodeText"]),
                Paragraph(m.get("explainability", "Token-level attribution"), styles["TableCell"]),
            ],
        ]

        meth_table = Table(rows, colWidths=[130, 170, 240])
        meth_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY_DARK),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(meth_table)
        story.append(Spacer(1, 14))

    @classmethod
    def _build_sentiment_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        s = data.get("sentiment", {})
        dist = s.get("distribution", {})
        story.append(Paragraph("4. Sentiment Analysis &amp; Polarity Distribution", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        # Donut chart
        chart = ReportChartGenerator.generate_sentiment_donut_chart(dist, width_pt=250, height_pt=140)

        # Distribution Table
        def _extract_count(val: Any) -> int:
            if isinstance(val, dict):
                return int(val.get("count", 0))
            if isinstance(val, (int, float)):
                return int(val)
            return 0

        pos = _extract_count(dist.get("positive"))
        neu = _extract_count(dist.get("neutral"))
        neg = _extract_count(dist.get("negative"))
        total = max(1, pos + neu + neg)

        dist_table = Table(
            [
                [
                    Paragraph("Sentiment", styles["TableHeader"]),
                    Paragraph("Count", styles["TableHeader"]),
                    Paragraph("Share (%)", styles["TableHeader"]),
                ],
                [
                    Paragraph("<font color='#10B981'><b>Positive</b></font>", styles["TableCell"]),
                    Paragraph(f"{pos:,}", styles["TableCell"]),
                    Paragraph(f"{pos/total*100:.1f}%", styles["TableCell"]),
                ],
                [
                    Paragraph("<font color='#64748B'><b>Neutral</b></font>", styles["TableCell"]),
                    Paragraph(f"{neu:,}", styles["TableCell"]),
                    Paragraph(f"{neu/total*100:.1f}%", styles["TableCell"]),
                ],
                [
                    Paragraph("<font color='#EF4444'><b>Negative</b></font>", styles["TableCell"]),
                    Paragraph(f"{neg:,}", styles["TableCell"]),
                    Paragraph(f"{neg/total*100:.1f}%", styles["TableCell"]),
                ],
                [
                    Paragraph("<b>Net Sentiment Score (NSS)</b>", styles["TableCellBold"]),
                    Paragraph(f"<b>{s.get('net_sentiment_score', 0.0):+.1f}</b>", styles["TableCellBold"]),
                    Paragraph("(-100 to +100)", styles["TableCellMuted"]),
                ],
            ],
            colWidths=[140, 60, 70],
        )
        dist_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )

        if chart:
            container = Table([[chart, dist_table]], colWidths=[260, 280])
            container.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            story.append(container)
        else:
            story.append(dist_table)

        story.append(Spacer(1, 14))

    @classmethod
    def _build_emotion_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        e = data.get("emotion", {})
        top_emotions = e.get("top_emotions", [])
        story.append(Paragraph("5. Discrete Emotion Spectrum", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        chart = ReportChartGenerator.generate_emotion_bar_chart(top_emotions, width_pt=260, height_pt=140)

        # Emotion Table
        emo_rows = [[
            Paragraph("Emotion", styles["TableHeader"]),
            Paragraph("Volume", styles["TableHeader"]),
            Paragraph("Percentage", styles["TableHeader"]),
        ]]
        for item in top_emotions[:7]:
            emo_rows.append([
                Paragraph(item.get("emotion", "").capitalize(), styles["TableCellBold"]),
                Paragraph(f"{item.get('count', 0):,}", styles["TableCell"]),
                Paragraph(f"{item.get('percentage', 0.0):.1f}%", styles["TableCell"]),
            ])

        emo_table = Table(emo_rows, colWidths=[120, 65, 75])
        emo_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )

        if chart:
            container = Table([[chart, emo_table]], colWidths=[270, 270])
            container.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            story.append(container)
        else:
            story.append(emo_table)

        story.append(Spacer(1, 14))

    @classmethod
    def _build_topics_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        t = data.get("topics", {})
        top_topics = t.get("top_topics", [])
        story.append(Paragraph("6. Discovered Topic Clusters &amp; Semantic Groupings", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        chart = ReportChartGenerator.generate_topic_distribution_chart(top_topics, width_pt=cls.PRINTABLE_WIDTH, height_pt=150)
        if chart:
            story.append(chart)
            story.append(Spacer(1, 8))

        # Topics Table
        topic_rows = [[
            Paragraph("Topic ID", styles["TableHeader"]),
            Paragraph("Semantic Cluster Representation", styles["TableHeader"]),
            Paragraph("Feedback Count", styles["TableHeader"]),
            Paragraph("Share (%)", styles["TableHeader"]),
        ]]

        valid_topics = [item for item in top_topics if item.get("topic_id") != -1]
        outliers = [item for item in top_topics if item.get("topic_id") == -1]

        for item in valid_topics[:8]:
            topic_rows.append([
                Paragraph(f"Topic {item.get('topic_id')}", styles["TableCellBold"]),
                Paragraph(item.get("label", "N/A"), styles["TableCell"]),
                Paragraph(f"{item.get('count', 0):,}", styles["TableCell"]),
                Paragraph(f"{item.get('percentage', 0.0):.1f}%", styles["TableCell"]),
            ])

        if outliers:
            o = outliers[0]
            topic_rows.append([
                Paragraph("Outliers (-1)", styles["TableCellMuted"]),
                Paragraph("Unclustered noise / diverse items", styles["TableCellMuted"]),
                Paragraph(f"{o.get('count', 0):,}", styles["TableCellMuted"]),
                Paragraph(f"{o.get('percentage', 0.0):.1f}%", styles["TableCellMuted"]),
            ])

        if len(topic_rows) > 1:
            t_table = Table(topic_rows, colWidths=[70, 310, 80, 80])
            t_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(t_table)

        story.append(Spacer(1, 14))

    @classmethod
    def _build_cross_dimensional_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        matrices = data.get("cross_matrices", {})
        story.append(Paragraph("7. Cross-Dimensional Analytics", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        if not matrices:
            story.append(Paragraph("<i>Cross-dimensional matrix data is not available for this analysis.</i>", styles["UnavailableNotice"]))
            story.append(Spacer(1, 14))
            return

        # 1. Sentiment x Emotion Matrix
        se_data = matrices.get("sentiment_emotion", {})
        se_rows = se_data.get("rows", []) if isinstance(se_data, dict) else (se_data if isinstance(se_data, list) else [])
        if se_rows:
            story.append(Paragraph("<b>Sentiment × Emotion Intersection:</b>", styles["SubSectionHeading"]))
            emotions = ["joy", "surprise", "neutral", "sadness", "fear", "anger", "disgust"]
            headers = [Paragraph("Sentiment", styles["TableHeader"])] + [Paragraph(e.capitalize(), styles["TableHeader"]) for e in emotions]

            rows = [headers]
            for row in se_rows:
                s_key = row.get("sentiment", "neutral")
                row_cells = [Paragraph(f"<b>{s_key.capitalize()}</b>", styles["TableCellBold"])]
                emo_dict = row.get("emotions", {})
                for emo in emotions:
                    val = emo_dict.get(emo, {})
                    cnt = val.get("count", 0) if isinstance(val, dict) else int(val or 0)
                    row_cells.append(Paragraph(str(cnt), styles["TableCellCenter"]))
                rows.append(row_cells)

            se_table = Table(rows, colWidths=[90, 64, 64, 64, 64, 64, 64, 64])
            se_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(se_table)
            story.append(Spacer(1, 10))

        # 2. Sentiment x Topic Matrix
        st_data = matrices.get("sentiment_topic", {})
        st_topics = st_data.get("topics", []) if isinstance(st_data, dict) else (st_data if isinstance(st_data, list) else [])
        if st_topics:
            story.append(Paragraph("<b>Sentiment × Discovered Topics Intersection (Top Clusters):</b>", styles["SubSectionHeading"]))
            st_rows = [[
                Paragraph("Topic ID", styles["TableHeader"]),
                Paragraph("Cluster Label", styles["TableHeader"]),
                Paragraph("Positive", styles["TableHeader"]),
                Paragraph("Neutral", styles["TableHeader"]),
                Paragraph("Negative", styles["TableHeader"]),
                Paragraph("Total", styles["TableHeader"]),
            ]]
            for item in st_topics[:8]:
                lbl = str(item.get("topic_label", item.get("label", "N/A")))
                if len(lbl) > 32:
                    lbl = lbl[:29] + "..."
                st_rows.append([
                    Paragraph(str(item.get("topic_id", "")), styles["TableCellBold"]),
                    Paragraph(lbl, styles["TableCell"]),
                    Paragraph(str(item.get("positive_count", item.get("positive", 0))), styles["TableCellCenter"]),
                    Paragraph(str(item.get("neutral_count", item.get("neutral", 0))), styles["TableCellCenter"]),
                    Paragraph(str(item.get("negative_count", item.get("negative", 0))), styles["TableCellCenter"]),
                    Paragraph(str(item.get("total_count", item.get("total", 0))), styles["TableCellCenter"]),
                ])

            st_table = Table(st_rows, colWidths=[60, 240, 60, 60, 60, 60])
            st_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(st_table)

        story.append(Spacer(1, 14))

    @classmethod
    def _build_temporal_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        trends = data.get("temporal_trends", {})
        story.append(Paragraph("8. Temporal Analytics &amp; Volume Trends", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        if not trends or not trends.get("has_temporal_data"):
            story.append(Paragraph(
                "<i>Temporal Analytics is not available for this dataset because no valid timestamp or date column was detected.</i>",
                styles["UnavailableNotice"],
            ))
            story.append(Spacer(1, 14))
            return

        chart = ReportChartGenerator.generate_temporal_trend_chart(trends, width_pt=cls.PRINTABLE_WIDTH, height_pt=140)
        if chart:
            story.append(chart)
            story.append(Spacer(1, 8))

        points = trends.get("data_points", [])
        if points:
            t_rows = [[
                Paragraph("Period", styles["TableHeader"]),
                Paragraph("Total Volume", styles["TableHeader"]),
                Paragraph("Positive", styles["TableHeader"]),
                Paragraph("Negative", styles["TableHeader"]),
                Paragraph("NSS", styles["TableHeader"]),
            ]]
            for p in points[:8]:
                t_rows.append([
                    Paragraph(p.get("period", ""), styles["TableCellBold"]),
                    Paragraph(str(p.get("total_count", 0)), styles["TableCellCenter"]),
                    Paragraph(str(p.get("positive_count", 0)), styles["TableCellCenter"]),
                    Paragraph(str(p.get("negative_count", 0)), styles["TableCellCenter"]),
                    Paragraph(f"{p.get('nss', 0.0):+.1f}", styles["TableCellCenter"]),
                ])

            t_table = Table(t_rows, colWidths=[120, 105, 105, 105, 105])
            t_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(t_table)

        story.append(Spacer(1, 14))

    @classmethod
    def _build_categorical_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        cats = data.get("categorical_breakdowns", {})
        story.append(Paragraph("9. Categorical Dimension Breakdowns", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        dimensions = cats.get("dimensions", []) if isinstance(cats, dict) else []
        if not dimensions:
            story.append(Paragraph(
                "<i>Categorical Dimension Analytics is not available because no secondary categorical columns (e.g., product tier, region, segment) were identified in the dataset schema.</i>",
                styles["UnavailableNotice"],
            ))
            story.append(Spacer(1, 14))
            return

        for dim in dimensions[:3]:
            col_name = dim.get("column_name", "Dimension")
            story.append(Paragraph(f"<b>Breakdown by {col_name}:</b>", styles["SubSectionHeading"]))
            values = dim.get("values", [])
            cat_rows = [[
                Paragraph("Category Value", styles["TableHeader"]),
                Paragraph("Feedback Volume", styles["TableHeader"]),
                Paragraph("Positive %", styles["TableHeader"]),
                Paragraph("Negative %", styles["TableHeader"]),
                Paragraph("Net Sentiment (NSS)", styles["TableHeader"]),
            ]]
            for val in values[:6]:
                cat_rows.append([
                    Paragraph(str(val.get("name", "")), styles["TableCellBold"]),
                    Paragraph(str(val.get("count", 0)), styles["TableCellCenter"]),
                    Paragraph(f"{val.get('positive_pct', 0.0):.1f}%", styles["TableCellCenter"]),
                    Paragraph(f"{val.get('negative_pct', 0.0):.1f}%", styles["TableCellCenter"]),
                    Paragraph(f"{val.get('nss', 0.0):+.1f}", styles["TableCellCenter"]),
                ])

            cat_table = Table(cat_rows, colWidths=[140, 100, 100, 100, 100])
            cat_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(cat_table)
            story.append(Spacer(1, 8))

        story.append(Spacer(1, 14))

    @classmethod
    def _build_strategic_insights_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        insights_data = data.get("insights", {})
        findings = insights_data.get("findings", [])
        recommendations = insights_data.get("recommendations", [])

        story.append(Paragraph("10. Deterministic Strategic Insights &amp; Recommendations", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        if not findings and not recommendations:
            story.append(Paragraph("<i>No deterministic business anomalies or automated recommendations were triggered for this dataset.</i>", styles["UnavailableNotice"]))
            story.append(Spacer(1, 14))
            return

        # Findings
        if findings:
            story.append(Paragraph("<b>Key Analytical Findings:</b>", styles["SubSectionHeading"]))
            for f in findings[:5]:
                severity = f.get("severity", "info").lower()
                sev_color = COLOR_DANGER if severity == "critical" else (COLOR_WARNING if severity in ["high", "warning"] else COLOR_INFO)
                card_table = Table(
                    [
                        [
                            Paragraph(f"<b><font color='{sev_color.hexval()}'>[{f.get('type', 'OBSERVATION').upper()}]</font> {f.get('title', 'Finding')}</b>", styles["CalloutTitle"]),
                        ],
                        [
                            Paragraph(f.get("description", ""), styles["CalloutBody"]),
                        ],
                    ],
                    colWidths=[cls.PRINTABLE_WIDTH],
                )
                card_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                        ("PADDING", (0, 0), (-1, -1), 7),
                    ])
                )
                story.append(card_table)
                story.append(Spacer(1, 5))

        # Recommendations
        if recommendations:
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>Actionable Recommendations:</b>", styles["SubSectionHeading"]))
            for r in recommendations[:4]:
                rec_table = Table(
                    [
                        [Paragraph(f"<b>Focus Area: {r.get('focus_area', 'General')}</b>", styles["CalloutTitle"])],
                        [Paragraph(r.get("action", ""), styles["CalloutBody"])],
                    ],
                    colWidths=[cls.PRINTABLE_WIDTH],
                )
                rec_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARY_LIGHT),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#C7D2FE")),
                        ("PADDING", (0, 0), (-1, -1), 7),
                    ])
                )
                story.append(rec_table)
                story.append(Spacer(1, 5))

        story.append(Spacer(1, 14))

    @classmethod
    def _build_explainability_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        exp = data.get("explainability", {})
        story.append(Paragraph("11. SHAP Model Explainability &amp; Feature Attribution", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

        story.append(Paragraph(
            exp.get("methodology", "SHAP evaluates token-level feature attributions towards neural sentiment predictions."),
            styles["Body"],
        ))
        story.append(Spacer(1, 6))

        sample = exp.get("sample")
        if sample and isinstance(sample, dict):
            story.append(Paragraph("<b>Representative SHAP Explanation Sample:</b>", styles["SubSectionHeading"]))
            meta_box = Table(
                [
                    [
                        Paragraph(f"<b>Predicted Sentiment:</b> {str(sample.get('predicted_sentiment', 'N/A')).capitalize()}", styles["TableCellBold"]),
                        Paragraph(f"<b>Confidence:</b> {sample.get('confidence', 0.0)*100:.1f}%", styles["TableCell"]),
                        Paragraph(f"<b>Base Value:</b> {sample.get('base_value', 0.0):.3f}", styles["TableCellMuted"]),
                    ]
                ],
                colWidths=[180, 180, 180],
            )
            meta_box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT), ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER), ("PADDING", (0, 0), (-1, -1), 6)]))
            story.append(meta_box)
            story.append(Spacer(1, 6))

            tokens = sample.get("tokens", [])
            values = sample.get("values", [])
            if tokens and values:
                t_rows = [[
                    Paragraph("Token / Subword", styles["TableHeader"]),
                    Paragraph("SHAP Attribution", styles["TableHeader"]),
                    Paragraph("Attribution Direction", styles["TableHeader"]),
                ]]
                # Sort tokens by magnitude of attribution
                paired = sorted(zip(tokens, values), key=lambda x: abs(x[1]), reverse=True)[:10]
                for tok, val in paired:
                    direction_str = "<font color='#10B981'>Pushes Positive</font>" if val > 0 else "<font color='#EF4444'>Pushes Negative</font>"
                    t_rows.append([
                        Paragraph(str(tok), styles["CodeText"]),
                        Paragraph(f"{val:+.4f}", styles["TableCellBold"]),
                        Paragraph(direction_str, styles["TableCell"]),
                    ])

                token_table = Table(t_rows, colWidths=[180, 180, 180])
                token_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
                        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                        ("PADDING", (0, 0), (-1, -1), 5),
                    ])
                )
                story.append(token_table)
        else:
            story.append(Paragraph("<i>No sample SHAP explainability record was pre-cached for this analysis run.</i>", styles["UnavailableNotice"]))

        story.append(Spacer(1, 14))

    @classmethod
    def _build_assistant_insights_section(cls, story: List[Any], data: Dict[str, Any], styles: Dict[str, Any]):
        insights = data.get("assistant_insights", [])
        if not insights:
            return

        story.append(Paragraph("12. Grounded AI Assistant Highlights", styles["SectionHeading"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))
        story.append(Paragraph(
            "The following natural-language questions were answered by the dataset-grounded assistant, validated strictly against authoritative analysis results:",
            styles["Body"],
        ))
        story.append(Spacer(1, 6))

        for item in insights:
            card_table = Table(
                [
                    [Paragraph(f"<b>Q: {item.get('question', '')}</b>", styles["CalloutTitle"])],
                    [Paragraph(f"<b>A:</b> {item.get('answer', '')}", styles["CalloutBody"])],
                ],
                colWidths=[cls.PRINTABLE_WIDTH],
            )
            card_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(card_table)
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 14))

    @classmethod
    def _build_governance_disclaimer(cls, story: List[Any], styles: Dict[str, Any]):
        story.append(KeepTogether([
            Paragraph("Governance, Limitations &amp; Non-Causal Analytics Disclaimer", styles["SubSectionHeading"]),
            HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=2, spaceAfter=6),
            Paragraph(
                "<b>Observational Analytics:</b> CFAP analytical outputs, sentiment polarities, discrete emotions, and topic representations "
                "are probabilistic observations derived from customer feedback text. They reflect correlations and patterns in the provided "
                "dataset and do not assert direct causality.<br/>"
                "<b>Confidentiality:</b> This document contains proprietary analysis. Distribution should be restricted according to internal governance policies.",
                styles["BodyMuted"],
            ),
        ]))
