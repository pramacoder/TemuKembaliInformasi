"""
Academic IR System — Language Detector for Summarization
=========================================================
Determines whether document text is Indonesian ('id'), English ('en'),
or Mixed ('mixed') to configure language-aware stopword filtering
and evaluation groups.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def detect_document_language(
    text: str,
    default_lang: Optional[str] = None,
    min_chars: int = 60,
) -> Tuple[str, float]:
    """
    Detect language of academic text with support for 'mixed' code-switching.

    Args:
        text: Text content to evaluate.
        default_lang: Optional fallback language from database metadata.
        min_chars: Minimum character length for statistical confidence.

    Returns:
        Tuple of (language_code, confidence_score)
        where language_code is 'id', 'en', or 'mixed'.
    """
    cleaned = (text or "").strip()
    if len(cleaned) < min_chars:
        # Fallback to metadata or English default
        fallback = (default_lang or "en").lower()
        if fallback not in ("id", "en", "mixed"):
            fallback = "en"
        return fallback, 0.50

    try:
        from langdetect import detect_langs, DetectorFactory
        DetectorFactory.seed = 42

        # Use up to first 6,000 characters for high precision with low latency
        sample = cleaned[:6000]
        predictions = detect_langs(sample)

        if not predictions:
            fallback = (default_lang or "en").lower()
            return fallback, 0.50

        # Create mapping of language -> probability
        lang_probs = {p.lang: p.prob for p in predictions}
        id_prob = lang_probs.get("id", 0.0)
        en_prob = lang_probs.get("en", 0.0)

        # Check for mixed bilingual material (common in slides & Indonesian papers with English abstracts)
        if (id_prob >= 0.25 and en_prob >= 0.25) or (0.20 <= id_prob <= 0.80 and 0.20 <= en_prob <= 0.80):
            return "mixed", round(max(id_prob, en_prob), 4)

        best = predictions[0]
        if best.lang == "id":
            return "id", round(best.prob, 4)
        elif best.lang == "en":
            return "en", round(best.prob, 4)
        else:
            # If langdetect identified something else (e.g. nl, de, fr due to small sample or latin names),
            # check if default_lang provides a better clue
            if default_lang and default_lang.lower() in ("id", "en", "mixed"):
                return default_lang.lower(), 0.60
            return "en", round(best.prob, 4)

    except Exception as exc:
        logger.warning(f"Summarization langdetect failed: {exc}. Using fallback.")
        fallback = (default_lang or "en").lower()
        if fallback not in ("id", "en", "mixed"):
            fallback = "en"
        return fallback, 0.50
