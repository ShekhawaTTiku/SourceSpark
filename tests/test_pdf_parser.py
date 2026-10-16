"""Selectable PDF text is evidence; blank and scanned pages are warnings."""

import pymupdf
import pytest

from documents.extraction import ExtractionError
from documents.pdf_parser import parse_pdf


def pdf_bytes(pages: list[str]) -> bytes:
    with pymupdf.open() as document:
        for text in pages:
            page = document.new_page()
            if text:
                page.insert_text((72, 72), text)
        return document.tobytes()


def test_pdf_multiple_pages_and_blank_page_warning() -> None:
    result = parse_pdf(pdf_bytes(["Fictional school report. There are 20 classrooms.", "", "12 classrooms have labelled sorting bins."]))
    assert list(result.locations) == ["Page 1", "Page 3"]
    assert "12 classrooms" in result.locations["Page 3"]
    assert any("Page 2 has no selectable text" in warning for warning in result.warnings)


def test_image_only_pdf_does_not_gain_fake_evidence() -> None:
    with pymupdf.open() as document:
        page = document.new_page()
        # A vector drawing supplies visible content without selectable words.
        page.draw_rect(pymupdf.Rect(72, 72, 200, 200), fill=(0, 0, 0))
        content = document.tobytes()
    with pytest.raises(ExtractionError, match="OCR"):
        parse_pdf(content)


@pytest.mark.parametrize("content", [b"", b"not a pdf", b"%PDF-corrupt"])
def test_corrupt_pdf_is_rejected(content: bytes) -> None:
    with pytest.raises(ExtractionError):
        parse_pdf(content)


def test_password_protected_pdf_is_rejected() -> None:
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), "Private fictional text")
        content = document.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="reader")
    with pytest.raises(ExtractionError, match="password-protected"):
        parse_pdf(content)


def test_page_extraction_failure_keeps_other_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    original = pymupdf.Page.get_text
    def fail_first(self: pymupdf.Page, *args: object, **kwargs: object) -> str:
        if self.number == 0:
            raise RuntimeError("simulated page extraction failure")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(pymupdf.Page, "get_text", fail_first)
    result = parse_pdf(pdf_bytes(["Unreadable test page", "Second page remains readable"]))
    assert list(result.locations) == ["Page 2"]
    assert any("Page 1 could not be extracted" in warning for warning in result.warnings)
