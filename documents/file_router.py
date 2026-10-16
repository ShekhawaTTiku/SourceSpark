"""Validate source uploads and dispatch exactly one format reader."""

from hashlib import sha256
from pathlib import PurePosixPath, PureWindowsPath
import re

from config.settings import MAX_FILE_BYTES
from documents.docx_parser import parse_docx
from documents.extraction import ExtractionError
from documents.pdf_parser import parse_pdf
from documents.tabular_parser import parse_tabular
from models.workspace import DocumentRecord


SUPPORTED_EXTENSIONS = {"pdf", "docx", "xlsx", "csv"}


def parse_uploaded_file(filename: str, file_bytes: bytes) -> DocumentRecord:
    """Return extracted evidence, retaining the original safe filename, not bytes."""
    if not isinstance(filename, str) or not filename.strip() or len(filename) > 255:
        raise ExtractionError("Choose a source file with a readable filename of at most 255 characters.")
    if PureWindowsPath(filename).name != filename or PurePosixPath(filename).name != filename or re.search(r'[<>:"/\\|?*\x00-\x1f]', filename) or filename.endswith((".", " ")):
        raise ExtractionError("Source filenames must be simple filenames without folders or invalid characters. Rename the file and try again.")
    file_type = PurePosixPath(filename).suffix.lower().lstrip(".")
    if file_type not in SUPPORTED_EXTENSIONS:
        raise ExtractionError("Unsupported source type. Choose .pdf, .docx, .xlsx or .csv.")
    if not isinstance(file_bytes, bytes) or not file_bytes:
        raise ExtractionError("This source file is empty or could not be read.")
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ExtractionError(f"Source exceeds the {MAX_FILE_BYTES // (1024 * 1024)} MiB per-file limit. Split or reduce the file.")
    if file_type == "pdf":
        extracted = parse_pdf(file_bytes)
    elif file_type == "docx":
        extracted = parse_docx(file_bytes)
    else:
        extracted = parse_tabular(file_bytes, file_type)
    extracted.require_readable()
    return DocumentRecord(
        document_id=sha256(file_bytes).hexdigest(), filename=filename,
        file_type=file_type, size_bytes=len(file_bytes), content=extracted.content,
        locations=extracted.locations, warnings=extracted.warnings,
    )
