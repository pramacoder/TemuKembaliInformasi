"""
Academic IR System — PDF Text Extraction (Page-Level)
======================================================
Extracts text from PDF files page-by-page using PyMuPDF.
Supports quality assessment and OCR fallback detection.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Lazy PyMuPDF import ─────────────────────────────────────────────────

_fitz = None

def _get_fitz():
    """Lazy-load PyMuPDF."""
    global _fitz
    if _fitz is None:
        try:
            import pymupdf as fitz
            _fitz = fitz
        except ImportError:
            try:
                import fitz
                _fitz = fitz
            except ImportError:
                raise ImportError(
                    "PyMuPDF is required for PDF extraction. "
                    "Install with: pip install pymupdf"
                )
    return _fitz


class PDFExtractionResult:
    """Container for PDF extraction results."""

    def __init__(self):
        self.pages = []         # list of {page_number, raw_text, word_count}
        self.page_count = 0
        self.total_words = 0
        self.total_chars = 0
        self.extraction_method = "pymupdf"
        self.extraction_status = "SUCCESS"
        self.error_message = None

    @property
    def full_text(self) -> str:
        """Concatenated text from all pages."""
        return "\n\n".join(p['raw_text'] for p in self.pages if p['raw_text'])

    def is_valid(self) -> bool:
        """Check if extraction produced usable text."""
        return self.total_words >= 10 and self.extraction_status != "FAILED"


def extract_pdf(file_path: str, min_words_per_page: int = 5) -> PDFExtractionResult:
    """
    Extract text from a PDF file, page by page.

    Args:
        file_path: Path to the PDF file
        min_words_per_page: Minimum words to consider a page as having text

    Returns:
        PDFExtractionResult with page-level text and quality metrics
    """
    fitz = _get_fitz()
    result = PDFExtractionResult()

    try:
        doc = fitz.open(file_path)
        result.page_count = len(doc)

        ocr_needed_pages = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            # Clean minimal whitespace issues
            text = text.strip() if text else ""
            word_count = len(text.split()) if text else 0

            result.pages.append({
                'page_number': page_num + 1,  # 1-indexed
                'raw_text': text,
                'word_count': word_count,
            })

            result.total_words += word_count
            result.total_chars += len(text)

            if word_count < min_words_per_page:
                ocr_needed_pages += 1

        doc.close()

        # Determine extraction status
        if result.total_words == 0:
            result.extraction_status = "OCR_REQUIRED"
        elif ocr_needed_pages > result.page_count * 0.5:
            result.extraction_status = "PARTIAL"
        else:
            result.extraction_status = "SUCCESS"

        logger.info(
            f"Extracted {file_path}: {result.page_count} pages, "
            f"{result.total_words} words, status={result.extraction_status}"
        )

    except Exception as e:
        result.extraction_status = "FAILED"
        result.error_message = str(e)
        logger.error(f"PDF extraction failed for {file_path}: {e}")

    return result


def validate_pdf(file_path: str) -> dict:
    """
    Validate that a file is a valid, readable PDF.

    Returns:
        dict with: valid (bool), page_count, file_size, error
    """
    fitz = _get_fitz()
    result = {
        'valid': False,
        'page_count': 0,
        'file_size': 0,
        'error': None,
    }

    path = Path(file_path)

    # Check file exists
    if not path.exists():
        result['error'] = "File not found"
        return result

    # Check file size
    result['file_size'] = path.stat().st_size
    if result['file_size'] < 1024:
        result['error'] = f"File too small ({result['file_size']} bytes)"
        return result

    # Try to open as PDF
    try:
        doc = fitz.open(file_path)
        result['page_count'] = len(doc)

        if result['page_count'] == 0:
            result['error'] = "PDF has 0 pages"
            doc.close()
            return result

        doc.close()
        result['valid'] = True

    except Exception as e:
        result['error'] = f"Cannot open PDF: {e}"

    return result
