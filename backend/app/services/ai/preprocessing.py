import re
import html
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd


@dataclass
class PreprocessedItem:
    row_index: int
    raw_text: str
    clean_text: str
    text_length: int
    is_valid: bool
    skip_reason: Optional[str] = None


@dataclass
class PreprocessingResult:
    items: List[PreprocessedItem]
    valid_items: List[PreprocessedItem]
    total_rows: int
    usable_rows: int
    invalid_rows: int


_URL_REGEX = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_HTML_REGEX = re.compile(r"<.*?>")
_WHITESPACE_REGEX = re.compile(r"\s+")
_CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text_content(text: str, max_length: int = 512) -> str:
    """
    Cleans raw customer feedback text:
    - Decodes HTML entities
    - Removes HTML tags
    - Strips URLs
    - Strips control characters
    - Normalizes multiple whitespaces/newlines to a single space
    - Truncates to max_length
    """
    if not text:
        return ""

    # Decode HTML entities (&amp;, &lt;, etc.)
    text = html.unescape(text)

    # Remove HTML tags
    text = _HTML_REGEX.sub(" ", text)

    # Remove URLs
    text = _URL_REGEX.sub(" ", text)

    # Remove control characters
    text = _CONTROL_CHAR_REGEX.sub(" ", text)

    # Normalize whitespace
    text = _WHITESPACE_REGEX.sub(" ", text).strip()

    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rstrip()

    return text


def preprocess_feedback_dataset(
    df: pd.DataFrame,
    feedback_column: str,
    max_length: int = 512,
    min_length: int = 2,
) -> PreprocessingResult:
    """
    Preprocesses feedback text from the specified DataFrame column.
    Maintains 0-based stable row indexing.
    Returns PreprocessingResult containing all items and valid items for ML inference.
    """
    items: List[PreprocessedItem] = []
    valid_items: List[PreprocessedItem] = []

    for row_idx, row_val in enumerate(df[feedback_column]):
        # Handle missing or non-string values
        if pd.isna(row_val) or row_val is None:
            item = PreprocessedItem(
                row_index=row_idx,
                raw_text="",
                clean_text="",
                text_length=0,
                is_valid=False,
                skip_reason="Missing or null feedback text",
            )
            items.append(item)
            continue

        raw_str = str(row_val)
        cleaned = clean_text_content(raw_str, max_length=max_length)
        length = len(cleaned)

        if length < min_length:
            item = PreprocessedItem(
                row_index=row_idx,
                raw_text=raw_str,
                clean_text="",
                text_length=0,
                is_valid=False,
                skip_reason=f"Feedback text too short (< {min_length} chars)",
            )
            items.append(item)
            continue

        item = PreprocessedItem(
            row_index=row_idx,
            raw_text=raw_str,
            clean_text=cleaned,
            text_length=length,
            is_valid=True,
            skip_reason=None,
        )
        items.append(item)
        valid_items.append(item)

    total_rows = len(items)
    usable_rows = len(valid_items)
    invalid_rows = total_rows - usable_rows

    return PreprocessingResult(
        items=items,
        valid_items=valid_items,
        total_rows=total_rows,
        usable_rows=usable_rows,
        invalid_rows=invalid_rows,
    )
