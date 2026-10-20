import pandas as pd
import pytest
from backend.app.services.ai.preprocessing import (
    clean_text_content,
    preprocess_feedback_dataset,
)


def test_clean_text_content_html_and_urls():
    raw = "Check out <a href='https://example.com'>this link</a> for great service! http://test.org &amp; more."
    cleaned = clean_text_content(raw)
    assert "https://" not in cleaned
    assert "http://" not in cleaned
    assert "<a" not in cleaned
    assert "&" in cleaned  # Unescaped &amp;
    assert "this link for great service! & more." in cleaned


def test_clean_text_content_control_chars_and_whitespace():
    raw = "Great   service!\x00\x08\n\nReally  loved   it.   "
    cleaned = clean_text_content(raw)
    assert cleaned == "Great service! Really loved it."


def test_clean_text_content_truncation():
    raw = "A" * 1000
    cleaned = clean_text_content(raw, max_length=100)
    assert len(cleaned) == 100


def test_preprocess_feedback_dataset():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3, 4, 5],
        "feedback": [
            "The app is wonderful and very intuitive!",
            None,
            "x",  # Too short (< 2 chars)
            "   ",  # Whitespace only -> empty
            "Customer support was slow, but resolved the issue.",
        ],
    })

    result = preprocess_feedback_dataset(df, feedback_column="feedback", min_length=2)

    assert result.total_rows == 5
    assert result.usable_rows == 2
    assert result.invalid_rows == 3

    assert result.items[0].is_valid is True
    assert result.items[0].row_index == 0
    assert result.items[0].clean_text == "The app is wonderful and very intuitive!"

    assert result.items[1].is_valid is False
    assert result.items[1].row_index == 1
    assert "Missing" in result.items[1].skip_reason

    assert result.items[2].is_valid is False
    assert result.items[2].row_index == 2
    assert "too short" in result.items[2].skip_reason

    assert result.items[3].is_valid is False
    assert result.items[3].row_index == 3

    assert result.items[4].is_valid is True
    assert result.items[4].row_index == 4
