"""
Academic IR System — Preprocessing for Summarization
====================================================
Language-aware sentence tokenization, academic abbreviation protection,
citation cleaning, and stopword management with source page tracking.
"""

import re
import logging
from typing import List, Tuple, Set, Optional

from ..preprocessing.stopwords import _get_indonesian_stopwords, _get_english_stopwords

logger = logging.getLogger(__name__)

# Academic abbreviations that should NOT trigger a sentence split
ABBREVIATIONS = [
    # English academic
    r"et\s+al\.", r"e\.g\.", r"i\.e\.", r"vs\.", r"approx\.", r"fig\.", r"tab\.",
    r"vol\.", r"no\.", r"pp\.", r"dept\.", r"univ\.", r"prof\.", r"dr\.", r"mr\.",
    r"mrs\.", r"ms\.", r"jr\.", r"sr\.", r"ed\.", r"eds\.", r"sec\.", r"ref\.",
    # Indonesian academic
    r"dkk\.", r"hlm\.", r"hal\.", r"jil\.", r"lamp\.", r"sdr\.", r"yth\.",
    r"drs\.", r"dra\.", r"ir\.", r"apt\.", r"skripsi\.", r"tesis\.",
]

ABBREV_PATTERN = re.compile(
    r"\b(" + "|".join(ABBREVIATIONS) + r")",
    re.IGNORECASE
)

# Reference patterns to clean from text without breaking sentence structure
CITATION_BRACKET_PATTERN = re.compile(r"\[\s*\d+(?:\s*[-–,]\s*\d+)*\s*\]")
CITATION_PAREN_PATTERN = re.compile(r"\((?:[A-Z][a-zA-Z\s]+(?:et al\.)?,\s*\d{4}[a-z]?(?:;\s*)?)+\)")

# Common noise patterns in extracted academic PDF pages
HEADER_FOOTER_NOISE = re.compile(
    r"(?:halaman\s+\d+|page\s+\d+|daftar pustaka|references|bibliography|issn|isbn|doi:\s*10\.\d+)",
    re.IGNORECASE
)


class RawSentence:
    """Represents an extracted sentence candidate with its origin metadata."""
    def __init__(self, text: str, page_number: Optional[int], order_idx: int):
        self.text = text.strip()
        self.page_number = page_number
        self.order_idx = order_idx

    def __repr__(self):
        return f"<RawSentence p={self.page_number} #{self.order_idx}: {self.text[:40]}...>"


def clean_sentence_text(text: str) -> str:
    """Remove inline citations, excessive whitespace, PDF artifacts, and hyphenated breaks."""
    # Fix hyphenated words across lines like 'construc- tion'
    t = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)
    # Fix PDF encoding replacements
    t = re.sub(r"[\ufffd]", "'", t)
    # Clean citations
    t = CITATION_BRACKET_PATTERN.sub("", t)
    t = CITATION_PAREN_PATTERN.sub("", t)
    # Normalize whitespaces
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def is_valid_summary_sentence(text: str) -> bool:
    """
    Check if a sentence is substantive and well-formed for inclusion in a summary.
    Discards headers, table rows, code lines, formulas, or short fragments.
    """
    clean = clean_sentence_text(text)
    # Strip leading bullet points or subsection numbers like '1.1 INTRODUCTION'
    clean_no_num = re.sub(r"^(\d+(\.\d+)*\s*|[•\-\*]\s*)", "", clean).strip()

    words = clean_no_num.split()
    word_count = len(words)

    # Discard too short or excessively long sentences
    if word_count < 6 or word_count > 95:
        return False

    # Discard if characters are fewer than 25
    if len(clean_no_num) < 25:
        return False

    # Discard bibliography / header remnants
    if HEADER_FOOTER_NOISE.search(clean_no_num) and word_count < 14:
        return False

    # Discard lines with abnormal ratio of numbers or symbols (e.g. table rows, math)
    num_digits = sum(c.isdigit() for c in clean_no_num)
    if num_digits / max(len(clean_no_num), 1) > 0.20:
        return False

    # Check if sentence looks like a header (e.g. all uppercase)
    if clean_no_num.isupper() and word_count < 10:
        return False

    return True


def split_sentences_safely(text: str) -> List[str]:
    """
    Split text into sentences while protecting academic abbreviations and decimal numbers.
    """
    if not text:
        return []

    # 1. Normalize line breaks and tabs into spaces
    normalized = re.sub(r"[\r\n]+", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # 2. Mask periods in known abbreviations and numbers
    # Temporarily replace period with a rare Unicode marker
    DOT_MASK = "\u2022_DOT_\u2022"

    def mask_abbrevs(match):
        return match.group(0).replace(".", DOT_MASK)

    masked = ABBREV_PATTERN.sub(mask_abbrevs, normalized)

    # Also mask periods between digits like 3.14 or 2.5
    masked = re.sub(r"(\d+)\.(\d+)", r"\1" + DOT_MASK + r"\2", masked)

    # 3. Sentence boundaries: split on period, exclamation, or question mark followed by space + uppercase/quote
    sentence_delimiters = re.compile(r'([.?!])\s+(?=[A-Z0-9"\'\(\[])')
    parts = sentence_delimiters.split(masked)

    reconstructed: List[str] = []
    # parts alternates [sentence_without_dot, dot, sentence_without_dot, dot, ...]
    i = 0
    while i < len(parts):
        chunk = parts[i]
        if i + 1 < len(parts):
            punct = parts[i + 1]
            full_sentence = chunk + punct
            i += 2
        else:
            full_sentence = chunk
            i += 1

        # Unmask dots
        unmasked = full_sentence.replace(DOT_MASK, ".").strip()
        if unmasked:
            reconstructed.append(unmasked)

    return reconstructed


def extract_candidate_sentences(
    pages_or_chunks: List[dict],
    max_sentences: int = 150,
) -> List[RawSentence]:
    """
    Extract and validate candidate sentences across pages, preserving page attribution.

    Args:
        pages_or_chunks: List of dicts containing 'page_number' and 'text' or 'clean_text'.
        max_sentences: Cap on candidate sentences to maintain fast processing.

    Returns:
        List of RawSentence instances.
    """
    candidates: List[RawSentence] = []
    seen_texts: Set[str] = set()
    global_idx = 0

    for item in pages_or_chunks:
        page_num = item.get("page_number") or item.get("page")
        raw_content = item.get("clean_text") or item.get("raw_text") or item.get("text") or ""
        if not raw_content.strip():
            continue

        raw_sentences = split_sentences_safely(raw_content)

        for s_text in raw_sentences:
            cleaned = clean_sentence_text(s_text)
            if not is_valid_summary_sentence(cleaned):
                continue

            normalized_key = cleaned.lower()
            if normalized_key in seen_texts:
                continue

            seen_texts.add(normalized_key)
            candidates.append(RawSentence(
                text=cleaned,
                page_number=page_num,
                order_idx=global_idx,
            ))
            global_idx += 1

            if len(candidates) >= max_sentences:
                break

        if len(candidates) >= max_sentences:
            break

    return candidates


def get_language_stopwords(language: str) -> Set[str]:
    """
    Retrieve stopwords tailored to the detected language.
    - 'id': Sastrawi Indonesian stopwords
    - 'en': NLTK English stopwords
    - 'mixed': Union of both
    """
    lang = (language or "en").lower()
    if lang == "id":
        return _get_indonesian_stopwords()
    elif lang == "en":
        return _get_english_stopwords()
    elif lang == "mixed":
        return _get_indonesian_stopwords().union(_get_english_stopwords())
    else:
        return _get_english_stopwords()
