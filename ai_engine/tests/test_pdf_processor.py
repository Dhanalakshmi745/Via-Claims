import pymupdf
import pytest

from claimvision_ai.pdf_processor import PdfProcessingError, extract_text_from_pdf


def build_pdf(pages: list[str]) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_extracts_text_from_pdf():
    result = extract_text_from_pdf(build_pdf(["Vehicle TN01AB1234 damaged at signal"]))

    assert result.page_count == 1
    assert result.has_text
    assert "TN01AB1234" in result.text


def test_multi_page_pdf():
    result = extract_text_from_pdf(build_pdf(["Page one text", "Page two text"]))

    assert result.page_count == 2
    assert result.pages_with_text == 2
    assert "Page one" in result.text
    assert "Page two" in result.text


def test_blank_pdf_has_no_text():
    result = extract_text_from_pdf(build_pdf([""]))

    assert result.page_count == 1
    assert not result.has_text
    assert result.text == ""


def test_garbage_bytes_raise_error():
    with pytest.raises(PdfProcessingError):
        extract_text_from_pdf(b"this is not a pdf")