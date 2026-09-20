"""
Academic IR System — Language-Aware Stemmer
============================================
Supports both Indonesian (Sastrawi) and English (NLTK SnowballStemmer).
Selects the appropriate stemmer based on detected language.
"""

import logging

logger = logging.getLogger(__name__)

# ─── Lazy-loaded singletons & word caches ────────────────────────────────
_indonesian_stemmer = None
_english_stemmer = None
_id_stem_cache = {}
_en_stem_cache = {}


def _get_indonesian_stemmer():
    """Lazy-load Sastrawi stemmer (heavy initialization)."""
    global _indonesian_stemmer
    if _indonesian_stemmer is None:
        try:
            from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
            factory = StemmerFactory()
            _indonesian_stemmer = factory.create_stemmer()
            logger.info("Indonesian stemmer (Sastrawi) loaded.")
        except ImportError:
            logger.warning("Sastrawi not installed. Indonesian stemming disabled.")
            _indonesian_stemmer = None
    return _indonesian_stemmer


def _get_english_stemmer():
    """Lazy-load NLTK SnowballStemmer."""
    global _english_stemmer
    if _english_stemmer is None:
        try:
            from nltk.stem import SnowballStemmer
            _english_stemmer = SnowballStemmer("english")
            logger.info("English stemmer (NLTK Snowball) loaded.")
        except ImportError:
            logger.warning("NLTK not installed. English stemming disabled.")
            _english_stemmer = None
    return _english_stemmer


def stem_tokens(tokens: list, language: str = "en") -> list:
    """
    Stem a list of tokens with dictionary caching for speed.

    Args:
        tokens: List of token strings
        language: ISO 639-1 code

    Returns:
        List of stemmed tokens
    """
    if not tokens:
        return []

    if language == "id":
        stemmer = _get_indonesian_stemmer()
        if stemmer:
            result = []
            for t in tokens:
                if t not in _id_stem_cache:
                    _id_stem_cache[t] = stemmer.stem(t)
                result.append(_id_stem_cache[t])
            return result
        return tokens

    elif language == "en":
        stemmer = _get_english_stemmer()
        if stemmer:
            result = []
            for t in tokens:
                if t not in _en_stem_cache:
                    _en_stem_cache[t] = stemmer.stem(t)
                result.append(_en_stem_cache[t])
            return result
        return tokens

    else:
        return stem_tokens(tokens, "en")


def stem_text(text: str, language: str = "en") -> str:
    """
    Stem text using the appropriate stemmer for the given language.

    Args:
        text: Pre-tokenized text (space-separated tokens)
        language: ISO 639-1 code ('en', 'id')

    Returns:
        Stemmed text
    """
    if not text:
        return ""
    tokens = text.split()
    stemmed = stem_tokens(tokens, language=language)
    return " ".join(stemmed)

