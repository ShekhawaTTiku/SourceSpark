"""Read CSV/Excel rows and compute summaries over every loaded data row."""

import csv
from datetime import date, datetime
from io import BytesIO, StringIO
import math
import re

from openpyxl import load_workbook
import pandas as pd

from config import settings
from config.settings import TABLE_PREVIEW_ROWS
from documents.extraction import ExtractionError, ExtractionResult, check_office_archive


def _display(value: object) -> str:
    if value is None or pd.isna(value) or (isinstance(value, str) and not value.strip()):
        return "(missing)"
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float):
        return format(value, ".12g")
    return str(value).strip()


def _headers(values: list[object]) -> list[str]:
    """Keep labels recognizable and make duplicate/blank labels unambiguous."""
    used: set[str] = set()
    headers = []
    for index, value in enumerate(values, start=1):
        base = str(value).strip() if value is not None and str(value).strip() else f"Column {index}"
        label, occurrence = base, 1
        while label in used:
            occurrence += 1
            label = f"{base} ({occurrence})"
        used.add(label)
        headers.append(label)
    return headers


def _is_identifier(label: str) -> bool:
    words = set(re.findall(r"[a-z]+", label.lower()))
    normalized = " ".join(re.findall(r"[a-z]+", label.lower()))
    return (
        bool(words & {"id", "identifier", "code", "zip", "postal", "phone", "telephone", "year"})
        or normalized in {"no", "number", "serial", "room", "classroom", "ward", "index"}
        or normalized.endswith((" number", " no"))
    )


def _add_table(
    result: ExtractionResult,
    label: str,
    header_values: list[object],
    rows: list[tuple[int, list[object]]],
    header_row: int,
) -> None:
    if not rows:
        result.warnings.append(f"{label} contains labels but no nonempty data rows; no table evidence was included.")
        return
    headers = _headers(header_values)
    frame = pd.DataFrame([values for _, values in rows], columns=headers)
    description = [
        f"Data rows: {len(rows)}. Columns: {len(headers)}. Header row: {header_row}.",
        f"Column labels: {', '.join(headers)}.",
        f"Row preview: first {min(TABLE_PREVIEW_ROWS, len(rows))} of {len(rows)} data rows. "
        "The summaries below use all loaded data rows, including those beyond the preview.",
        "Statistics describe the recorded values; they do not establish causes or unstated units.",
    ]
    for column in headers:
        series = frame[column]
        empty = series.map(lambda value: value is None or pd.isna(value) or str(value).strip() == "")
        observed = series[~empty]
        prefix = f"{column}: nonempty={len(observed)}, missing={int(empty.sum())}"
        if observed.empty:
            description.append(prefix + ".")
            continue
        if _is_identifier(column):
            description.append(prefix + "; identifier/date-label column, no numeric aggregate calculated.")
            continue
        # Text labels and mixed numeric/text values do not become invented zeroes.
        if observed.map(lambda value: isinstance(value, (date, datetime, bool))).any():
            description.append(prefix + "; nonnumeric/date/boolean values, no numeric aggregate calculated.")
            continue
        numeric = pd.to_numeric(observed, errors="coerce")
        if numeric.notna().all() and all(math.isfinite(float(value)) for value in numeric):
            description.append(
                prefix + f"; min={_display(numeric.min())}, max={_display(numeric.max())}, "
                f"sum={_display(numeric.sum())}, mean={_display(numeric.mean())}."
            )
        else:
            description.append(prefix + "; nonnumeric or mixed values, no numeric aggregate calculated.")
    result.add_location(f"{label}, full-table summary", "\n".join(description))
    for row_number, values in rows[:TABLE_PREVIEW_ROWS]:
        result.add_location(f"{label}, row {row_number}", "; ".join(
            f"{column}={_display(value)}" for column, value in zip(headers, values)
        ))
    if len(rows) > TABLE_PREVIEW_ROWS:
        result.warnings.append(
            f"{label}: only the first {TABLE_PREVIEW_ROWS} data rows are included individually. "
            f"All {len(rows)} data rows contribute to full-table summaries; later individual rows cannot be cited."
        )


def _decode_csv(file_bytes: bytes) -> tuple[str, list[str]]:
    warnings: list[str] = []
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            if file_bytes.startswith((b"\xff\xfe", b"\xfe\xff")):
                text = file_bytes.decode("utf-16")
                warnings.append("CSV was decoded using UTF-16 from its byte-order mark rather than UTF-8.")
            else:
                text = file_bytes.decode("cp1252")
                warnings.append("CSV used Windows-1252 fallback decoding because it was not UTF-8. Check accented characters in the preview.")
        except UnicodeDecodeError as exc:
            raise ExtractionError("CSV text could not be decoded. Export the file as UTF-8 CSV and try again.") from exc
    bad = sum(ord(character) < 32 and character not in "\r\n\t" for character in text)
    if "\x00" in text or "\ufffd" in text or bad or not text.strip():
        raise ExtractionError("CSV is empty or contains unreadable/binary characters. Export readable UTF-8 CSV.")
    return text, warnings


def _parse_csv(file_bytes: bytes) -> ExtractionResult:
    text, warnings = _decode_csv(file_bytes)
    try:
        # Delimiter detection supports common CSV exports while never treating a
        # prose document without a delimiter as a successfully read data table.
        try:
            dialect = csv.Sniffer().sniff(text[:65536], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(StringIO(text, newline=""), dialect=dialect, strict=True)
        records = []
        cell_count = 0
        previous_line = 0
        for row in reader:
            number = previous_line + 1
            previous_line = reader.line_num
            cell_count += len(row)
            if cell_count > settings.MAX_TABLE_CELLS:
                raise ExtractionError("CSV exceeds the table-cell extraction limit. Split it into smaller tables.")
            if any(cell.strip() for cell in row):
                records.append((number, row))
        if len(records) < 2:
            raise ExtractionError("CSV needs a header and at least one nonempty data row.")
        header_row, header = records[0]
        if not any(cell.strip() for cell in header):
            raise ExtractionError("CSV has no readable column labels.")
        for row_number, row in records[1:]:
            if len(row) != len(header):
                raise ExtractionError(f"CSV record {row_number} has {len(row)} fields; expected {len(header)}. Correct the malformed row and try again.")
        # pandas is the tabular processing engine; csv validates ragged input and
        # preserves physical record locations rather than silently skipping it.
        frame = pd.read_csv(StringIO(text), dialect=dialect, dtype=object, keep_default_na=False, skip_blank_lines=True)
        if frame.shape != (len(records) - 1, len(header)):
            raise ExtractionError("CSV structure could not be read consistently. Re-export a rectangular CSV table.")
    except ExtractionError:
        raise
    except (csv.Error, pd.errors.ParserError, ValueError) as exc:
        raise ExtractionError("CSV is malformed or its delimiter could not be identified. Use a rectangular comma-separated table with a header row.") from exc
    result = ExtractionResult({}, warnings)
    _add_table(result, "CSV", header, records[1:], header_row)
    return result.require_readable()


def _parse_xlsx(file_bytes: bytes) -> ExtractionResult:
    check_office_archive(file_bytes)
    values_book = formulas_book = None
    try:
        values_book = load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
        formulas_book = load_workbook(BytesIO(file_bytes), read_only=True, data_only=False)
        result = ExtractionResult({})
        for sheet in values_book:
            label = f"Sheet '{sheet.title}'"
            try:
                if sheet.max_row * sheet.max_column > settings.MAX_TABLE_CELLS:
                    raise ExtractionError(f"{label} exceeds the table-cell extraction limit. Remove unused formatted rows/columns or split the sheet.")
                data_rows: list[tuple[int, list[object]]] = []
                formula_rows = formulas_book[sheet.title].iter_rows()
                missing_cache = formula_count = 0
                for row_number, (cells, formulas) in enumerate(zip(sheet.iter_rows(), formula_rows), start=1):
                    values = [cell.value for cell in cells]
                    for cell, formula in zip(cells, formulas):
                        if formula.data_type == "f":
                            formula_count += 1
                            if cell.value is None:
                                missing_cache += 1
                    if any(value is not None and str(value).strip() for value in values) or any(cell.data_type == "f" for cell in formulas):
                        data_rows.append((row_number, values))
                if formula_count:
                    result.warnings.append(f"{label}: {formula_count} formula cells were read using stored results. This app does not calculate Excel formulas; cached values may be stale.")
                if missing_cache:
                    result.warnings.append(f"{label}: {missing_cache} formula cells have no stored result and are treated as missing, never as zero. Recalculate and save in Excel before uploading for complete evidence.")
                if not data_rows:
                    result.warnings.append(f"{label} is empty or has no readable cached cell values; it was skipped.")
                    continue
                header_row, header = data_rows[0]
                # Ignore only genuinely blank trailing columns, preserving every
                # column containing a label or any data in later rows.
                width = max(index + 1 for _, row in data_rows for index, value in enumerate(row) if value is not None and str(value).strip())
                _add_table(result, label, header[:width], [(n, row[:width]) for n, row in data_rows[1:]], header_row)
                if sheet.sheet_state != "visible":
                    result.warnings.append(f"{label} is hidden in Excel but was included in extraction.")
            except ExtractionError:
                raise
            except Exception:
                result.warnings.append(f"{label} could not be completely read; this sheet is not included as evidence.")
                for key in list(result.locations):
                    if key.startswith(label + ","):
                        del result.locations[key]
                result._characters = len(result.content)
        result.warnings.append("Excel reads cell values and cached formula results. Charts, images, formatting-derived units and embedded objects are not interpreted.")
        return result.require_readable()
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("This Excel file could not be opened. Upload a valid, unencrypted .xlsx workbook.") from exc
    finally:
        if values_book is not None:
            values_book.close()
        if formulas_book is not None:
            formulas_book.close()


def parse_tabular(file_bytes: bytes, file_type: str) -> ExtractionResult:
    """Extract CSV or XLSX with explicit preview and computation limitations."""
    extension = file_type.lower().lstrip(".")
    if extension == "csv":
        return _parse_csv(file_bytes)
    if extension == "xlsx":
        return _parse_xlsx(file_bytes)
    raise ExtractionError("The tabular reader supports .csv and .xlsx files only.")
