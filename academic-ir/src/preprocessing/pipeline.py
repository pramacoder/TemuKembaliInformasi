"""
Academic IR System — Unified Preprocessing Pipeline
=====================================================
Language-aware pipeline that consistently processes both
documents and queries through the same steps.

Pipeline:
    Raw Text → Unicode Norm → Case Folding → Cleaning
    → Tokenization → Stopword Removal → Stemming → Clean Text
"""

import logging
from .cleaner import clean_text, clean_query
from .tokenizer import tokenize, detokenize
from .stopwords import remove_stopwords
from .stemmer import stem_tokens

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """
    Language-aware preprocessing pipeline.

    Ensures documents and queries go through the same steps
    so that TF-IDF vectors are comparable.
    """

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language

    def process_document(self, text: str, language: str = None) -> str:
        """
        Full preprocessing pipeline for a document/chunk.

        Args:
            text: Raw text
            language: ISO 639-1 language code ('en', 'id')
                      If None, uses default_language.

        Returns:
            Preprocessed text string
        """
        if not text or not text.strip():
            return ""

        lang = language or self.default_language

        # 1. Clean (unicode norm, case fold, remove noise, preserve technical terms)
        cleaned = clean_text(text, preserve_numbers=True)

        # 2. Tokenize
        tokens = tokenize(cleaned, min_length=2)

        if not tokens:
            return ""

        # 3. Remove stopwords (language-aware)
        tokens = remove_stopwords(tokens, language=lang)

        if not tokens:
            return ""

        # 4. Stem (language-aware)
        tokens = stem_tokens(tokens, language=lang)

        # 5. Final token validation — remove empty tokens
        tokens = [t for t in tokens if t and len(t) >= 2]

        return detokenize(tokens)

    def process_query(self, query: str, language: str = None) -> str:
        """
        Preprocess a search query.
        Uses the same pipeline as documents to ensure consistency.

        Args:
            query: Raw query string
            language: ISO 639-1 language code

        Returns:
            Preprocessed query string
        """
        if not query or not query.strip():
            return ""

        lang = language or self.default_language

        # 1. Clean query (less aggressive than document cleaning)
        cleaned = clean_query(query)

        # 2. Tokenize
        tokens = tokenize(cleaned, min_length=2)

        if not tokens:
            return ""

        # 3. Remove stopwords
        tokens = remove_stopwords(tokens, language=lang)

        if not tokens:
            # If all tokens are stopwords, return the original cleaned tokens
            return clean_query(query)

        # 4. Stem
        tokens = stem_tokens(tokens, language=lang)

        tokens = [t for t in tokens if t and len(t) >= 2]

        return detokenize(tokens)


# ─── Convenience singleton ───────────────────────────────────────────────

_pipeline = None


def get_pipeline(default_language: str = "en") -> PreprocessingPipeline:
    """Get or create the singleton preprocessing pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = PreprocessingPipeline(default_language)
    return _pipeline
