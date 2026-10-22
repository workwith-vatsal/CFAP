import re
from typing import Any
import pandas as pd
import numpy as np


FEEDBACK_NAME_PATTERNS = [
    r"review",
    r"feedback",
    r"comment",
    r"description",
    r"opinion",
    r"remarks",
    r"complaint",
    r"text",
    r"message",
    r"summary",
    r"content",
    r"body",
    r"response",
    r"critique",
    r"testimonial",
    r"customer_feedback",
    r"customer_comment",
    r"feedback_text",
    r"user_review",
]

RATING_NAME_PATTERNS = [
    r"rating",
    r"score",
    r"stars",
    r"grade",
    r"rank",
    r"evaluation",
]

DATE_NAME_PATTERNS = [
    r"date",
    r"time",
    r"timestamp",
    r"created_at",
    r"datetime",
    r"submitted_at",
    r"posted_on",
    r"day",
    r"month",
    r"year",
]

CATEGORY_NAME_PATTERNS = [
    r"category",
    r"type",
    r"class",
    r"segment",
    r"group",
    r"genre",
    r"department",
    r"topic",
    r"channel",
    r"tag",
]

PRODUCT_NAME_PATTERNS = [
    r"product",
    r"item",
    r"sku",
    r"service",
    r"model",
    r"asin",
    r"article",
    r"goods",
    r"brand",
    r"device",
]

CUSTOMER_ID_NAME_PATTERNS = [
    r"customer_id",
    r"user_id",
    r"client_id",
    r"account_id",
    r"buyer_id",
    r"cust_id",
    r"member_id",
    r"author_id",
]

SENSITIVE_NAME_PATTERNS = [
    r"email",
    r"e-mail",
    r"phone",
    r"mobile",
    r"tel",
    r"telephone",
    r"ssn",
    r"passport",
    r"address",
    r"ip_address",
    r"credit_card",
    r"password",
]


def _matches_any_pattern(text: str, patterns: list[str]) -> bool:
    clean = text.lower().replace("-", "_").replace(" ", "_")
    for pat in patterns:
        if re.search(pat, clean):
            return True
    return False


def classify_column(series: pd.Series, col_name: str) -> tuple[str, float]:
    """
    Classify a single dataframe column into a semantic category.
    Returns (detected_category, confidence).
    """
    total_count = len(series)
    non_null_series = series.dropna()
    non_null_count = len(non_null_series)

    if non_null_count == 0:
        return "unknown", 0.0

    raw_dtype_str = str(series.dtype).lower()

    # Check for sensitive/PII column name
    if _matches_any_pattern(col_name, SENSITIVE_NAME_PATTERNS):
        return "sensitive", 0.90

    # Check for Customer ID
    if _matches_any_pattern(col_name, CUSTOMER_ID_NAME_PATTERNS):
        return "customer_id", 0.85

    # Check for Date column
    if _matches_any_pattern(col_name, DATE_NAME_PATTERNS):
        return "date", 0.85
    if "datetime" in raw_dtype_str or "date" in raw_dtype_str:
        return "date", 0.95

    # Try parsing sample strings as date if column name has date clues
    if raw_dtype_str in ["object", "str", "string"] or "str" in raw_dtype_str:
        sample = non_null_series.head(20).astype(str)
        date_parsed_count = 0
        for val in sample:
            if len(val.strip()) in range(8, 30):
                try:
                    pd.to_datetime(val)
                    date_parsed_count += 1
                except (ValueError, TypeError):
                    pass
        if date_parsed_count >= 15:
            return "date", 0.80

    # Check for Rating
    if _matches_any_pattern(col_name, RATING_NAME_PATTERNS):
        if pd.api.types.is_numeric_dtype(series):
            min_val = non_null_series.min()
            max_val = non_null_series.max()
            if min_val >= 0 and max_val <= 10:
                return "rating", 0.95
            return "rating", 0.80
        return "rating", 0.70

    # Check for Boolean
    if pd.api.types.is_bool_dtype(series):
        return "boolean", 1.0
    if raw_dtype_str in ["object", "str", "string"] or "str" in raw_dtype_str:
        unique_vals = set(non_null_series.astype(str).str.strip().str.lower().unique())
        if unique_vals.issubset({"true", "false", "yes", "no", "0", "1", "t", "f", "y", "n"}):
            return "boolean", 0.90

    # Check for Numeric
    if pd.api.types.is_numeric_dtype(series):
        return "numeric", 0.85

    # Check for Product / Brand
    if _matches_any_pattern(col_name, PRODUCT_NAME_PATTERNS):
        return "product", 0.80

    # Check for Category
    if _matches_any_pattern(col_name, CATEGORY_NAME_PATTERNS):
        return "category", 0.80

    # String / Text analysis
    if raw_dtype_str in ["object", "str", "string"] or "str" in raw_dtype_str or pd.api.types.is_string_dtype(series):
        str_series = non_null_series.astype(str)
        char_lengths = str_series.str.len()
        avg_len = float(char_lengths.mean())
        word_counts = str_series.str.split().str.len()
        avg_words = float(word_counts.mean())
        unique_ratio = len(str_series.unique()) / max(1, non_null_count)

        is_name_feedback = _matches_any_pattern(col_name, FEEDBACK_NAME_PATTERNS)

        # Content suggests rich natural language
        if avg_len >= 30 and avg_words >= 5:
            conf = 0.75 + (0.20 if is_name_feedback else 0.0)
            return "feedback", min(0.98, conf)
        elif avg_len >= 15 and avg_words >= 3 and unique_ratio > 0.4:
            conf = 0.60 + (0.25 if is_name_feedback else 0.0)
            return "feedback", min(0.95, conf)
        elif is_name_feedback and avg_len >= 8:
            return "feedback", 0.65

        # Short strings with low uniqueness suggest categories
        if unique_ratio < 0.2 and avg_len < 30:
            return "category", 0.70

    return "unknown", 0.50


def detect_feedback_column(df: pd.DataFrame) -> tuple[str | None, float | None, str | None]:
    """
    Dynamically detect the primary customer feedback / review text column.
    Evaluates both column naming and natural language content characteristics.
    Returns (feedback_column_name, confidence, reason).
    """
    candidates = []

    for col in df.columns:
        series = df[col]
        non_null_series = series.dropna()
        non_null_count = len(non_null_series)
        if non_null_count == 0:
            continue

        raw_dtype = str(series.dtype).lower()
        if not (raw_dtype in ["object", "str", "string"] or "str" in raw_dtype or pd.api.types.is_string_dtype(series)):
            continue

        str_series = non_null_series.astype(str).str.strip()
        str_series = str_series[str_series != ""]
        if len(str_series) == 0:
            continue

        char_lens = str_series.str.len()
        avg_char_len = float(char_lens.mean())
        median_char_len = float(char_lens.median())
        word_counts = str_series.str.split().str.len()
        avg_words = float(word_counts.mean())
        unique_count = len(str_series.unique())
        unique_ratio = unique_count / max(1, len(str_series))

        # Signals
        name_matched = _matches_any_pattern(col, FEEDBACK_NAME_PATTERNS)
        name_score = 1.0 if name_matched else 0.0

        # Reject obvious non-feedback identifiers or dates
        if _matches_any_pattern(col, SENSITIVE_NAME_PATTERNS) or _matches_any_pattern(col, CUSTOMER_ID_NAME_PATTERNS):
            continue

        # Length score (saturates around 120 characters)
        length_score = min(1.0, avg_char_len / 100.0)

        # Word count score (saturates around 15 words)
        word_score = min(1.0, avg_words / 12.0)

        # Diversity score
        diversity_score = min(1.0, unique_ratio * 1.2)

        # Combined composite confidence score
        if name_matched:
            confidence = (
                0.35 * name_score
                + 0.35 * length_score
                + 0.15 * word_score
                + 0.15 * diversity_score
            )
        else:
            # Without name match, content must be strong natural language text
            if avg_char_len < 20 or avg_words < 4:
                continue
            confidence = (
                0.50 * length_score
                + 0.30 * word_score
                + 0.20 * diversity_score
            ) * 0.90  # slight discount for unnamed column

        # Extra penalty if average length is tiny (< 10 chars)
        if avg_char_len < 10:
            confidence *= 0.3

        if confidence >= 0.35:
            reason = (
                f"Classified based on {('keyword matching and ' if name_matched else '')}"
                f"average text length of {avg_char_len:.1f} characters and {avg_words:.1f} words."
            )
            candidates.append((col, round(confidence, 2), reason, avg_char_len))

    if not candidates:
        return None, None, "No suitable natural language feedback column was identified."

    # Sort candidates by confidence descending, then by avg length
    candidates.sort(key=lambda x: (x[1], x[3]), reverse=True)
    best_col, best_conf, best_reason, _ = candidates[0]

    return best_col, best_conf, best_reason


def detect_all_columns(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    Run full column detection on entire DataFrame.
    Returns dictionary mapping column_name -> {detected_type, confidence, raw_dtype}.
    """
    primary_feedback_col, _, _ = detect_feedback_column(df)
    results = {}

    for col in df.columns:
        series = df[col]
        if col == primary_feedback_col:
            results[col] = {
                "detected_type": "feedback",
                "confidence": 0.95,
                "raw_dtype": str(series.dtype),
            }
        else:
            cat, conf = classify_column(series, col)
            results[col] = {
                "detected_type": cat,
                "confidence": round(conf, 2),
                "raw_dtype": str(series.dtype),
            }

    return results
