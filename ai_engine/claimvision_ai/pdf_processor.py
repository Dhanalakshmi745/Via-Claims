from dataclasses import dataclass

import pymupdf


class PdfProcessingError(Exception):
    """Raised when a PDF cannot be read."""


@dataclass
class PdfExtractionResult:
    page_count: int
    pages_with_text: int
    text: str

    @property
    def has_text(self) -> bool:
        return self.pages_with_text > 0


def extract_text_from_pdf(pdf_bytes: bytes) -> PdfExtractionResult:
    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.needs_pass:
                raise PdfProcessingError("PDF is password protected")
            if doc.page_count == 0:
                raise PdfProcessingError("PDF has no pages")
            page_texts = [page.get_text().strip() for page in doc]
    except PdfProcessingError:
        raise
    except Exception as exc:
        raise PdfProcessingError("File could not be read as a PDF") from exc

    return PdfExtractionResult(
        page_count=len(page_texts),
        pages_with_text=sum(1 for text in page_texts if text),
        text="\n\n".join(page_texts).strip(),
    )