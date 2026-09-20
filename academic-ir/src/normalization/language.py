"""
Academic IR System — Language Detection
=========================================
Detects document language using langdetect.
"""

import logging

logger = logging.getLogger(__name__)


def detect_language(text: str, min_length: int = 50) -> dict:
    """
    Detect the language of a text.

    Args:
        text: Text to analyze
        min_length: Minimum text length for reliable detection

    Returns:
        dict with 'language' (ISO 639-1 code) and 'confidence' (float 0-1)
    """
    if not text or len(text.strip()) < min_length:
        return {'language': None, 'confidence': 0.0}

    try:
        from langdetect import detect_langs, DetectorFactory
        # Set seed for reproducibility
        DetectorFactory.seed = 42

        results = detect_langs(text[:5000])  # use first 5000 chars for speed

        if results:
            best = results[0]
            return {
                'language': best.lang,
                'confidence': round(best.prob, 4),
            }
        return {'language': None, 'confidence': 0.0}

    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return {'language': None, 'confidence': 0.0}
