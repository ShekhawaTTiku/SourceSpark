"""Extract selectable PDF text with page-level evidence provenance."""

import pymupdf

from documents.extraction import ExtractionError, ExtractionResult


def parse_pdf(file_bytes: bytes) -> ExtractionResult:
    """Skip unreadable pages with visible warnings; never apply implicit OCR."""
    try:
        document = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ExtractionError("This PDF could not be opened. Upload a valid, unencrypted PDF.") from exc

    result = ExtractionResult(locations={})
    try:
        if document.needs_pass:
            raise ExtractionError("This PDF is password-protected. Upload an unlocked copy.")
        for page_index in range(document.page_count):
            location = f"Page {page_index + 1}"
            try:
                text = document.load_page(page_index).get_text("text", sort=True).strip()
            except Exception:
                result.warnings.append(f"{location} could not be extracted and is not included as evidence.")
                continue
            if text:
                result.add_location(location, text)
            else:
                result.warnings.append(
                    f"{location} has no selectable text and is not included as evidence. "
                    "Scanned images require OCR, which is outside Version 1."
                )
    finally:
        document.close()
    if not result.locations:
        raise ExtractionError("This PDF has no readable selectable text. Scanned/image-only PDFs need OCR, which Version 1 does not provide.")
    result.warnings.append("PDF reading order may differ from the visual layout, especially in columns and tables. Review the extracted pages.")
    return result.require_readable()
