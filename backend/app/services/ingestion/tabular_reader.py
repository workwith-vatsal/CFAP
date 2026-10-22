import csv
import io
import os
import openpyxl
import pandas as pd
import numpy as np

from backend.app.core.config import settings
from backend.app.services.ingestion.file_validator import FileValidationError


def _deduplicate_columns(columns: list[str]) -> list[str]:
    """Ensure unique column names by appending incrementing index to duplicates."""
    seen: dict[str, int] = {}
    deduped = []
    for col in columns:
        col_clean = str(col).strip()
        if not col_clean:
            col_clean = "unnamed_column"

        if col_clean in seen:
            seen[col_clean] += 1
            deduped.append(f"{col_clean}_{seen[col_clean]}")
        else:
            seen[col_clean] = 0
            deduped.append(col_clean)
    return deduped


def read_csv_file(file_path: str) -> pd.DataFrame:
    """
    Read and parse a CSV file with automatic encoding and delimiter detection.
    Raises FileValidationError on empty or unparseable CSV.
    """
    encodings_to_try = ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]
    df: pd.DataFrame | None = None
    last_error: Exception | None = None

    for enc in encodings_to_try:
        try:
            # First sniff sample for delimiter
            with open(file_path, "r", encoding=enc, errors="replace") as f:
                sample = f.read(8192)

            if not sample.strip():
                raise FileValidationError("CSV file is empty or contains only whitespace.")

            # Try sniffing delimiter
            delimiter = ","
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                if dialect.delimiter in [",", ";", "\t", "|"]:
                    delimiter = dialect.delimiter
            except Exception:
                delimiter = ","

            # Read CSV with pandas
            df = pd.read_csv(
                file_path,
                encoding=enc,
                sep=delimiter,
                on_bad_lines="skip",
                low_memory=False,
            )
            break
        except FileValidationError:
            raise
        except Exception as e:
            last_error = e
            continue

    if df is None:
        raise FileValidationError(
            f"Failed to parse CSV file. Ensure the file contains valid tabular data. ({last_error})"
        )

    return df


def read_xlsx_file(file_path: str) -> pd.DataFrame:
    """
    Read and parse an XLSX file using openpyxl, selecting the first non-empty worksheet.
    Raises FileValidationError on corrupt or empty spreadsheets.
    """
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    except Exception as e:
        raise FileValidationError(f"Invalid or corrupted Excel file: {str(e)}")

    sheet_names = wb.sheetnames
    if not sheet_names:
        wb.close()
        raise FileValidationError("Excel workbook contains no worksheets.")

    target_sheet = None
    for name in sheet_names:
        sheet = wb[name]
        # Check if sheet has at least one cell
        if sheet.max_row and sheet.max_row > 0 and sheet.max_column and sheet.max_column > 0:
            target_sheet = name
            break

    wb.close()

    if not target_sheet:
        target_sheet = sheet_names[0]

    try:
        df = pd.read_excel(
            file_path,
            sheet_name=target_sheet,
            engine="openpyxl",
        )
    except Exception as e:
        raise FileValidationError(f"Failed to read Excel worksheet: {str(e)}")

    return df


def ingest_tabular_file(file_path: str, file_type: str) -> pd.DataFrame:
    """
    Ingest and normalize CSV or XLSX file into a clean pandas DataFrame.
    Enforces maximum row and column thresholds.
    """
    if not os.path.isfile(file_path):
        raise FileValidationError("File not found on storage.")

    if file_type == "csv":
        df = read_csv_file(file_path)
    elif file_type == "xlsx":
        df = read_xlsx_file(file_path)
    else:
        raise FileValidationError(f"Unsupported file type: {file_type}")

    # Validate non-empty columns
    if df.shape[1] == 0:
        raise FileValidationError("Dataset contains no columns.")

    # Clean & deduplicate column names
    clean_cols = _deduplicate_columns([str(c) for c in df.columns])
    df.columns = clean_cols

    # Enforce column limit
    if df.shape[1] > settings.max_dataset_columns:
        raise FileValidationError(
            f"Dataset has {df.shape[1]} columns, exceeding the maximum allowed limit of {settings.max_dataset_columns} columns."
        )

    # Validate non-empty rows
    if df.shape[0] == 0:
        raise FileValidationError("Dataset contains column headers but no data rows.")

    # Enforce row limit
    if df.shape[0] > settings.max_dataset_rows:
        raise FileValidationError(
            f"Dataset has {df.shape[0]} rows, exceeding the maximum allowed limit of {settings.max_dataset_rows} rows."
        )

    return df
