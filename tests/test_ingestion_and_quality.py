import io
import os
import openpyxl
import pandas as pd
import pytest

from backend.app.services.column_detection.detector import (
    classify_column,
    detect_all_columns,
    detect_feedback_column,
)
from backend.app.services.data_quality.quality_engine import (
    calculate_data_quality,
    generate_sanitized_preview,
    mask_sensitive_value,
)
from backend.app.services.ingestion.file_validator import (
    FileValidationError,
    validate_upload_file,
)
from backend.app.services.ingestion.tabular_reader import (
    ingest_tabular_file,
    read_csv_file,
    read_xlsx_file,
)


def test_file_validator():
    # Valid
    assert validate_upload_file("feedback.csv", 1024) == "csv"
    assert validate_upload_file("feedback.xlsx", 2048) == "xlsx"

    # Unsupported extension
    with pytest.raises(FileValidationError, match="Unsupported file format"):
        validate_upload_file("feedback.pdf", 1024)

    # Empty file
    with pytest.raises(FileValidationError, match="empty"):
        validate_upload_file("feedback.csv", 0)

    # Empty filename
    with pytest.raises(FileValidationError, match="Filename cannot be empty"):
        validate_upload_file("", 1024)


def test_csv_ingestion_encodings_and_delimiters(tmp_path):
    # Standard comma UTF-8
    csv1 = tmp_path / "test1.csv"
    csv1.write_text("Review,Rating,Date\nGreat product!,5,2026-01-01\nBad support,1,2026-01-02", encoding="utf-8")
    df1 = ingest_tabular_file(str(csv1), "csv")
    assert len(df1) == 2
    assert list(df1.columns) == ["Review", "Rating", "Date"]

    # Semicolon delimited
    csv2 = tmp_path / "test2.csv"
    csv2.write_text("Customer_Comment;Score\nLoved the onboarding;10\nCould be faster;6", encoding="utf-8")
    df2 = ingest_tabular_file(str(csv2), "csv")
    assert len(df2) == 2
    assert "Customer_Comment" in df2.columns


def test_xlsx_ingestion(tmp_path):
    xlsx_path = tmp_path / "test.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "FeedbackSheet"
    ws.append(["Customer_Feedback", "Department", "Rating"])
    ws.append(["Excellent customer service and prompt delivery", "Support", 5])
    ws.append(["The app crashed repeatedly during checkout", "Mobile", 1])
    wb.save(str(xlsx_path))

    df = ingest_tabular_file(str(xlsx_path), "xlsx")
    assert len(df) == 2
    assert list(df.columns) == ["Customer_Feedback", "Department", "Rating"]


def test_column_detection_feedback_and_heuristics():
    df = pd.DataFrame({
        "Customer_Feedback": [
            "The product arrived damaged and customer support was unhelpful.",
            "Really enjoyed using this application, sleek interface!",
            "Average quality, could have been better.",
        ],
        "User_Rating": [1, 5, 3],
        "Submission_Date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "Customer_Email": ["alice@example.com", "bob@example.com", "carol@example.com"],
        "Is_Subscriber": [True, False, True],
    })

    fb_col, conf, reason = detect_feedback_column(df)
    assert fb_col == "Customer_Feedback"
    assert conf is not None and conf >= 0.70

    all_cols = detect_all_columns(df)
    assert all_cols["Customer_Feedback"]["detected_type"] == "feedback"
    assert all_cols["User_Rating"]["detected_type"] == "rating"
    assert all_cols["Submission_Date"]["detected_type"] == "date"
    assert all_cols["Customer_Email"]["detected_type"] == "sensitive"
    assert all_cols["Is_Subscriber"]["detected_type"] == "boolean"


def test_column_detection_no_feedback_column():
    df = pd.DataFrame({
        "Transaction_ID": [101, 102, 103],
        "Amount": [25.5, 99.0, 14.2],
        "Status": ["Completed", "Pending", "Failed"],
    })
    fb_col, conf, _ = detect_feedback_column(df)
    assert fb_col is None
    assert conf is None


def test_data_quality_metrics_exact_calculation():
    df = pd.DataFrame({
        "review": ["Awesome!", "Terrible", "Awesome!", "", None, "Good"],
        "rating": [5, 1, 5, 2, 4, 4],
        "email": ["user1@test.com", "user2@test.com", "user1@test.com", "user4@test.com", None, "user6@test.com"],
    })

    # Row 0: "Awesome!", 5, "user1@test.com"
    # Row 1: "Terrible", 1, "user2@test.com"
    # Row 2: "Awesome!", 5, "user1@test.com" -> duplicate of row 0
    # Row 3: "", 2, "user4@test.com" -> blank feedback
    # Row 4: None, 4, None -> missing feedback
    # Row 5: "Good", 4, "user6@test.com"

    quality = calculate_data_quality(df, feedback_column="review", feedback_confidence=0.95)

    assert quality["rows"] == 6
    assert quality["total_columns"] == 3
    assert len(quality["columns"]) == 3
    assert quality["duplicate_rows"] == 1
    assert quality["missing_feedback"] == 1
    assert quality["blank_feedback"] == 1
    # Usable rows = Row 0, Row 1, Row 5 = 3 rows
    assert quality["usable_rows"] == 3
    assert quality["invalid_rows"] == 3
    assert 0.0 <= quality["quality_score"] <= 100.0


def test_sanitized_preview_pii_masking():
    df = pd.DataFrame({
        "feedback": ["Great service!"],
        "email": ["john.doe@company.com"],
        "phone": ["+1-555-0199"],
    })
    detected = {
        "feedback": {"detected_type": "feedback"},
        "email": {"detected_type": "sensitive"},
        "phone": {"detected_type": "sensitive"},
    }

    preview = generate_sanitized_preview(df, detected, max_rows=5)
    row = preview["rows"][0]
    assert row["feedback"] == "Great service!"
    assert "@company.com" in row["email"]
    assert "john.doe" not in row["email"]  # Masked
    assert "0199" in row["phone"]
