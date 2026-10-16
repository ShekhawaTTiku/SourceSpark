"""Word fixtures verify sequence and real evidence rather than file headings."""

from io import BytesIO

from docx import Document
import pytest

from config import settings
from documents.docx_parser import parse_docx
from documents.extraction import ExtractionError, canonical_content


def word_bytes(document: Document) -> bytes:
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def test_body_paragraph_table_sequence_and_empty_cells() -> None:
    document = Document()
    document.add_paragraph("Fictional Greenfield School report")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Classrooms"
    table.cell(0, 1).text = "Labelled bins"
    table.cell(1, 0).text = "A"
    table.cell(1, 1).text = "12"
    document.add_paragraph("Collection information appears on the noticeboard.")
    result = parse_docx(word_bytes(document))
    assert list(result.locations) == ["Paragraph 1", "Table 1, row 1", "Table 1, row 2", "Paragraph 2"]
    assert "A | 12" in result.locations["Table 1, row 2"]
    assert result.content == canonical_content(result.locations)
    assert "headers" in result.warnings[0]


def test_header_only_is_not_body_evidence() -> None:
    document = Document()
    document.sections[0].header.paragraphs[0].text = "Hidden in the header only"
    with pytest.raises(ExtractionError, match="No readable"):
        parse_docx(word_bytes(document))


@pytest.mark.parametrize("content", [b"", b"not a document", b"PKinvalid"])
def test_corrupt_word_is_a_useful_error(content: bytes) -> None:
    with pytest.raises(ExtractionError):
        parse_docx(content)


def test_incremental_extraction_character_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    document = Document()
    document.add_paragraph("Fictional text " * 20)
    monkeypatch.setattr(settings, "MAX_CONTEXT_CHARACTERS", 100)
    with pytest.raises(ExtractionError, match="stopped rather than truncated"):
        parse_docx(word_bytes(document))


def test_office_archive_expansion_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    document = Document()
    document.add_paragraph("Fictional school report")
    monkeypatch.setattr(settings, "MAX_ARCHIVE_UNCOMPRESSED_BYTES", 100)
    with pytest.raises(ExtractionError, match="expands beyond"):
        parse_docx(word_bytes(document))
