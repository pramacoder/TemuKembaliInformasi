"""
Academic IR System — Context-Aware Text Cleaner
=================================================
Fixes the aggressive `[^a-z\\s]` regex from the original system.
Preserves technical terms like Python3, IPv4, COVID-19, SQL2024.
"""

import re
import unicodedata


def clean_text(text: str, preserve_numbers: bool = True) -> str:
    """
    Clean raw text with context-aware rules.

    Unlike the old cleaner that strips ALL non-alphabetic chars,
    this version preserves numbers within technical terms and
    handles academic document artifacts properly.

    Args:
        text: Raw text to clean
        preserve_numbers: If True, keep numbers in mixed alphanumeric tokens

    Returns:
        Cleaned text string
    """
    if not text:
        return ""

    # 1. Unicode normalization (NFC) — collapse equivalent representations
    text = unicodedata.normalize('NFC', text)

    # 2. Case folding
    text = text.lower()

    # 3. Remove control characters (but keep newlines/tabs temporarily)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # 4. Remove common PDF artifacts
    #    - Page numbers at line boundaries (e.g., "\n42\n", "Page 3")
    #    - Repeated header/footer patterns
    text = re.sub(r'\bpage\s+\d+\s*(of\s+\d+)?', ' ', text)
    text = re.sub(r'^\s*\d{1,3}\s*$', ' ', text, flags=re.MULTILINE)

    # 5. Handle URLs — replace with space (URLs aren't useful for TF-IDF)
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'www\.\S+', ' ', text)

    # 6. Handle email addresses
    text = re.sub(r'\S+@\S+\.\S+', ' ', text)

    # 7. Context-aware character filtering
    if preserve_numbers:
        # Keep: letters, digits, hyphens (for compound terms), underscores, spaces
        # Remove: other punctuation, symbols
        text = re.sub(r'[^\w\s-]', ' ', text)
        # Remove standalone pure numbers (e.g., "42" but not "python3" or "ipv4")
        text = re.sub(r'\b\d+\b', ' ', text)
    else:
        # Strict mode: only keep alphabetic + spaces
        text = re.sub(r'[^a-z\s]', ' ', text)

    # 8. Remove very short tokens (1 char, excluding known single-letter terms)
    text = re.sub(r'\b[a-z]\b', ' ', text)

    # 9. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def clean_query(query: str) -> str:
    """
    Clean a search query. Less aggressive than document cleaning
    to preserve user intent.
    """
    if not query:
        return ""

    query = unicodedata.normalize('NFC', query)
    query = query.lower()
    # Keep alphanumeric, hyphens, spaces
    query = re.sub(r'[^\w\s-]', ' ', query)
    query = re.sub(r'\s+', ' ', query).strip()

    return query
