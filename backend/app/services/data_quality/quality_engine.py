import re
from typing import Any
import pandas as pd
import numpy as np

from backend.app.services.column_detection.detector import detect_all_columns, detect_feedback_column


def mask_sensitive_value(value: Any, col_type: str) -> str:
    """Mask obvious PII strings for preview privacy."""
    if pd.isna(value) or value is None:
        return ""
    val_str = str(value).strip()
    if not val_str:
        return ""

    if col_type == "sensitive":
        # Email masking
        if "@" in val_str and "." in val_str:
            parts = val_str.split("@")
            name = parts[0]
            domain = parts[1] if len(parts) > 1 else ""
            masked_name = name[0] + "***" if len(name) > 1 else "***"
            return f"{masked_name}@{domain}"
        # Phone masking
        digits = re.sub(r"\D", "", val_str)
        if len(digits) >= 7:
            return f"***-***-{digits[-4:]}"
        return "***MASKED***"

    return val_str


def calculate_data_quality(
    df: pd.DataFrame,
    detected_columns: dict[str, dict[str, Any]] | None = None,
    feedback_column: str | None = None,
    feedback_confidence: float | None = None,
) -> dict[str, Any]:
    """
    Compute comprehensive, deterministic data quality metrics for the dataset.
    Does NOT store raw customer feedback records in the report.
    """
    total_rows = int(len(df))
    total_columns = int(len(df.columns))

    if detected_columns is None:
        detected_columns = detect_all_columns(df)

    if feedback_column is None:
        feedback_column, feedback_confidence, _ = detect_feedback_column(df)

    # 1. Cell-level missingness
    null_matrix = df.isna()
    total_cells = max(1, total_rows * total_columns)
    missing_values = int(null_matrix.sum().sum())

    # Check for empty string cells in object/string columns as missing
    blank_cell_count = 0
    for col in df.columns:
        series = df[col]
        raw_dtype = str(series.dtype).lower()
        if raw_dtype in ["object", "str", "string"] or "str" in raw_dtype or pd.api.types.is_string_dtype(series):
            str_series = series.dropna().astype(str).str.strip()
            blank_cell_count += int((str_series == "").sum())

    total_missing_or_blank_cells = missing_values + blank_cell_count
    completeness_ratio = max(0.0, 1.0 - (total_missing_or_blank_cells / total_cells))

    # 2. Duplicate rows
    duplicate_rows = int(df.duplicated().sum())
    uniqueness_ratio = max(0.0, 1.0 - (duplicate_rows / max(1, total_rows)))

    # 3. Feedback column metrics
    missing_feedback = 0
    blank_feedback = 0
    usable_rows = 0
    invalid_rows = total_rows

    if feedback_column and feedback_column in df.columns:
        fb_series = df[feedback_column]
        is_na = fb_series.isna()
        missing_feedback = int(is_na.sum())

        str_vals = fb_series.dropna().astype(str).str.strip()
        blank_feedback = int((str_vals == "").sum())

        # Valid feedback rows are not NA, not blank, and not complete row duplicates
        valid_fb_mask = (~is_na) & (fb_series.astype(str).str.strip() != "")
        usable_mask = valid_fb_mask & (~df.duplicated())
        usable_rows = int(usable_mask.sum())
        invalid_rows = total_rows - usable_rows
        usable_feedback_ratio = usable_rows / max(1, total_rows)
    else:
        usable_feedback_ratio = 0.0
        usable_rows = 0
        invalid_rows = total_rows

    # 4. Structural health score
    structure_score = 1.0
    if total_columns < 2:
        structure_score *= 0.7
    if total_rows < 5:
        structure_score *= 0.6

    # 5. Deterministic Quality Score calculation (0.0 - 100.0)
    # Weights: Usable Feedback (40%), Completeness (25%), Uniqueness (20%), Structure (15%)
    weighted_score = (
        40.0 * usable_feedback_ratio
        + 25.0 * completeness_ratio
        + 20.0 * uniqueness_ratio
        + 15.0 * structure_score
    )
    quality_score = round(min(100.0, max(0.0, weighted_score)), 1)

    # 6. Column-level quality analysis
    columns_report = []
    for col in df.columns:
        series = df[col]
        col_meta = detected_columns.get(col, {})
        detected_type = col_meta.get("detected_type", "unknown")
        raw_dtype = str(series.dtype).lower()

        col_nulls = int(series.isna().sum())
        if raw_dtype in ["object", "str", "string"] or "str" in raw_dtype or pd.api.types.is_string_dtype(series):
            col_blanks = int((series.dropna().astype(str).str.strip() == "").sum())
            total_col_missing = col_nulls + col_blanks
        else:
            total_col_missing = col_nulls

        col_null_pct = round((total_col_missing / max(1, total_rows)) * 100.0, 1)
        unique_count = int(series.nunique(dropna=True))

        columns_report.append({
            "name": col,
            "detected_type": detected_type,
            "raw_dtype": str(series.dtype),
            "null_count": total_col_missing,
            "null_percentage": col_null_pct,
            "unique_count": unique_count,
            "is_sensitive": detected_type == "sensitive",
        })

    return {
        "rows": total_rows,
        "total_columns": total_columns,
        "columns_count": total_columns,
        "usable_rows": usable_rows,
        "invalid_rows": invalid_rows,
        "duplicate_rows": duplicate_rows,
        "missing_values": missing_values,
        "feedback_column": feedback_column,
        "feedback_confidence": feedback_confidence,
        "missing_feedback": missing_feedback,
        "blank_feedback": blank_feedback,
        "quality_score": quality_score,
        "score_breakdown": {
            "usable_feedback_score": round(40.0 * usable_feedback_ratio, 1),
            "completeness_score": round(25.0 * completeness_ratio, 1),
            "uniqueness_score": round(20.0 * uniqueness_ratio, 1),
            "structure_score": round(15.0 * structure_score, 1),
        },
        "columns": columns_report,
        "columns_detail": columns_report,
    }


def generate_sanitized_preview(
    df: pd.DataFrame,
    detected_columns: dict[str, dict[str, Any]] | None = None,
    max_rows: int = 15,
) -> dict[str, Any]:
    """
    Generate privacy-sanitized tabular preview of the first N rows (max 15).
    Masks PII/sensitive columns to prevent accidental data leakage.
    """
    if detected_columns is None:
        detected_columns = detect_all_columns(df)

    preview_df = df.head(min(max_rows, 15)).copy()
    sanitized_rows = []

    for _, row in preview_df.iterrows():
        row_dict = {}
        for col in df.columns:
            val = row[col]
            col_type = detected_columns.get(col, {}).get("detected_type", "unknown")
            if col_type == "sensitive":
                row_dict[col] = mask_sensitive_value(val, col_type)
            else:
                if pd.isna(val) or val is None:
                    row_dict[col] = None
                elif isinstance(val, (int, float, bool)):
                    row_dict[col] = val
                else:
                    # Limit very long string cell previews to 200 chars
                    str_val = str(val).strip()
                    row_dict[col] = (str_val[:200] + "...") if len(str_val) > 200 else str_val
        sanitized_rows.append(row_dict)

    return {
        "columns": list(df.columns),
        "total_preview_rows": len(sanitized_rows),
        "rows": sanitized_rows,
    }
