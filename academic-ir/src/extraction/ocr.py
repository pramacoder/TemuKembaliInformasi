"""
Academic IR System — OCR Fallback
==================================
Uses pytesseract for scanned PDFs where PyMuPDF cannot extract text.
Optional module — only loaded when needed.
"""

import logging

logger = logging.getLogger(__name__)


def ocr_extract_page(pdf_path: str, page_number: int) -> str:
    """
    Extract text from a single PDF page using OCR.

    Args:
        pdf_path: Path to the PDF file
        page_number: 0-indexed page number

    Returns:
        Extracted text string
    """
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    try:
        import pytesseract
        from PIL import Image
        import io
    except ImportError:
        logger.error(
            "pytesseract and Pillow are required for OCR. "
            "Install with: pip install pytesseract Pillow"
        )
        return ""

    try:
        doc = fitz.open(pdf_path)
        page = doc[page_number]

        # Render page to image at 300 DPI
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        # Run OCR
        text = pytesseract.image_to_string(img)

        doc.close()
        return text.strip()

    except Exception as e:
        logger.error(f"OCR failed for {pdf_path} page {page_number}: {e}")
        return ""


def ocr_extract_pdf(pdf_path: str) -> list:
    """
    Extract text from all pages of a PDF using OCR.

    Returns:
        List of dicts: [{'page_number': 1, 'raw_text': '...', 'word_count': N}, ...]
    """
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
    except Exception as e:
        logger.error(f"Cannot open PDF for OCR: {e}")
        return []

    pages = []
    for i in range(page_count):
        text = ocr_extract_page(pdf_path, i)
        word_count = len(text.split()) if text else 0
        pages.append({
            'page_number': i + 1,
            'raw_text': text,
            'word_count': word_count,
        })

    return pages
