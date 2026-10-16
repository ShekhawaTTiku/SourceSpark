"""Read Word body paragraphs and tables in their original sequence."""

from io import BytesIO

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from documents.extraction import ExtractionError, ExtractionResult, check_office_archive


def parse_docx(file_bytes: bytes) -> ExtractionResult:
    """Read supported body content; never mistake image placeholders for text."""
    check_office_archive(file_bytes)
    try:
        document = Document(BytesIO(file_bytes))
    except Exception as exc:
        raise ExtractionError("This Word file could not be opened. Upload a valid .docx file.") from exc

    result = ExtractionResult(locations={})
    paragraph_number = table_number = 0
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            paragraph_number += 1
            text = Paragraph(child, document).text.strip()
            if text:
                result.add_location(f"Paragraph {paragraph_number}", text)
        elif child.tag == qn("w:tbl"):
            table_number += 1
            table = Table(child, document)
            for row_number, row in enumerate(table.rows, start=1):
                # A labelled row preserves empty columns without inventing values.
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    result.add_location(f"Table {table_number}, row {row_number}", " | ".join(cells))

    result.warnings.append(
        "Word extraction includes body paragraphs and table cells only. Images, headers, footers, "
        "text boxes and embedded objects are not read; table merging may repeat cell text."
    )
    return result.require_readable()
