"""
Academic IR System — Language-Aware Stopwords
==============================================
Provides stopword lists for Indonesian and English.
"""

import logging

logger = logging.getLogger(__name__)

# ─── Lazy-loaded stopword sets ───────────────────────────────────────────

_english_stopwords = None
_indonesian_stopwords = None


def _get_english_stopwords() -> set:
    """Load English stopwords from NLTK."""
    global _english_stopwords
    if _english_stopwords is None:
        try:
            import nltk
            try:
                from nltk.corpus import stopwords as nltk_stopwords
                _english_stopwords = set(nltk_stopwords.words('english'))
            except LookupError:
                nltk.download('stopwords', quiet=True)
                from nltk.corpus import stopwords as nltk_stopwords
                _english_stopwords = set(nltk_stopwords.words('english'))
            logger.info(f"Loaded {len(_english_stopwords)} English stopwords.")
        except ImportError:
            logger.warning("NLTK not installed. Using minimal English stopword list.")
            _english_stopwords = {
                'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
                'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'shall',
                'can', 'this', 'that', 'these', 'those', 'it', 'its', 'not',
                'no', 'nor', 'so', 'if', 'then', 'than', 'too', 'very',
                'just', 'about', 'above', 'after', 'again', 'all', 'also',
                'any', 'because', 'before', 'between', 'both', 'each',
                'few', 'more', 'most', 'other', 'our', 'out', 'own',
                'same', 'some', 'such', 'only', 'into', 'over', 'under',
                'until', 'up', 'down', 'here', 'there', 'when', 'where',
                'which', 'while', 'who', 'whom', 'what', 'how', 'why',
                'i', 'me', 'my', 'we', 'he', 'she', 'they', 'them',
                'his', 'her', 'you', 'your',
            }
    return _english_stopwords


def _get_indonesian_stopwords() -> set:
    """Load Indonesian stopwords from Sastrawi."""
    global _indonesian_stopwords
    if _indonesian_stopwords is None:
        try:
            from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
            factory = StopWordRemoverFactory()
            _indonesian_stopwords = set(factory.get_stop_words())
            logger.info(f"Loaded {len(_indonesian_stopwords)} Indonesian stopwords.")
        except ImportError:
            logger.warning("Sastrawi not installed. Using minimal Indonesian stopword list.")
            _indonesian_stopwords = {
                'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'pada',
                'adalah', 'ini', 'itu', 'atau', 'juga', 'akan', 'dalam',
                'tidak', 'sudah', 'oleh', 'karena', 'ada', 'bisa', 'dapat',
                'telah', 'saya', 'kami', 'kita', 'mereka', 'dia', 'ia',
                'anda', 'tersebut', 'bahwa', 'secara', 'sebuah', 'satu',
                'seperti', 'jika', 'maka', 'namun', 'tetapi', 'lalu',
                'serta', 'antara', 'lebih', 'sangat', 'hanya', 'masih',
                'belum', 'sedang', 'harus', 'bagi', 'atas', 'bawah',
                'lain', 'semua', 'setiap', 'tanpa', 'melalui', 'tentang',
                'sebagai', 'ketika', 'hingga', 'setelah', 'sebelum',
                'sehingga', 'maupun', 'yakni', 'yaitu',
            }
    return _indonesian_stopwords


def get_stopwords(language: str = "en") -> set:
    """
    Get the stopword set for a given language.

    Args:
        language: ISO 639-1 code ('en' or 'id')

    Returns:
        Set of stopword strings
    """
    if language == "id":
        return _get_indonesian_stopwords()
    elif language == "en":
        return _get_english_stopwords()
    else:
        # Default to English
        return _get_english_stopwords()


def remove_stopwords(tokens: list, language: str = "en") -> list:
    """
    Remove stopwords from a list of tokens.

    Args:
        tokens: List of token strings
        language: ISO 639-1 code

    Returns:
        Filtered list of tokens
    """
    sw = get_stopwords(language)
    return [t for t in tokens if t not in sw]
