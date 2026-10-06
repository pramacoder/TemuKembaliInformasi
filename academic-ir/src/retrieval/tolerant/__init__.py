"""
Tolerant Retrieval Package
==========================
Query normalization, typo tolerance, fuzzy matching, abbreviation expansion,
and exact-first fallback control layer.
"""

from .constants import ABBREVIATIONS, DEFAULT_CONFIG, PROTECTED_TERMS, SPELLING_VARIATIONS
from .fallback_controller import FallbackController, TolerantSearchMetadata
from .fuzzy_matcher import FuzzyMatcher, damerau_levenshtein, string_similarity
from .processor import CorrectionItem, TolerantAnalysisResult, TolerantQueryProcessor
from .service import TolerantRetrievalService, get_tolerant_service

__all__ = [
    "TolerantRetrievalService",
    "get_tolerant_service",
    "TolerantQueryProcessor",
    "FallbackController",
    "TolerantSearchMetadata",
    "TolerantAnalysisResult",
    "CorrectionItem",
    "FuzzyMatcher",
    "damerau_levenshtein",
    "string_similarity",
    "DEFAULT_CONFIG",
    "PROTECTED_TERMS",
    "ABBREVIATIONS",
    "SPELLING_VARIATIONS",
]
