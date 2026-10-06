"""
Tolerant Retrieval — Query Processor
====================================
Orchestrates technical term preservation, abbreviation expansion, spelling
variation normalization, typo correction, and cross-lingual phrase detection.
Produces normalized query, did-you-mean suggestion, and explainability audit logs.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .constants import (
    ABBREVIATIONS,
    DEFAULT_CONFIG,
    MORPHOLOGICAL_VARIANTS,
    PROTECTED_TERMS,
    SPELLING_VARIATIONS,
    TECHNICAL_PHRASES,
)
from .fuzzy_matcher import FuzzyMatcher

logger = logging.getLogger(__name__)


class CorrectionItem:
    def __init__(self, source: str, target: str, correction_type: str, confidence: float, note: str = ""):
        self.source = source
        self.target = target
        self.type = correction_type
        self.confidence = round(confidence, 4)
        self.note = note

    def to_dict(self) -> Dict[str, any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "confidence": self.confidence,
            "note": self.note,
        }


class TolerantAnalysisResult:
    def __init__(
        self,
        original_query: str,
        normalized_query: str,
        did_you_mean: Optional[str] = None,
        expanded_terms: Optional[List[str]] = None,
        corrections: Optional[List[CorrectionItem]] = None,
        confidence: float = 1.0,
        is_modified: bool = False,
    ):
        self.original_query = original_query
        self.normalized_query = normalized_query
        self.did_you_mean = did_you_mean
        self.expanded_terms = expanded_terms or []
        self.corrections = corrections or []
        self.confidence = round(confidence, 4)
        self.is_modified = is_modified

    def to_dict(self) -> Dict[str, any]:
        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "did_you_mean": self.did_you_mean,
            "expanded_terms": self.expanded_terms,
            "corrections": [c.to_dict() for c in self.corrections],
            "confidence": self.confidence,
            "is_modified": self.is_modified,
        }


class TolerantQueryProcessor:
    """
    Query normalizer and recovery processor.
    Never alters BM25 internally; transforms queries prior to lexical search.
    """

    def __init__(
        self,
        fuzzy_matcher: Optional[FuzzyMatcher] = None,
        config: Optional[Dict[str, any]] = None,
        synonym_dict_path: Optional[str] = None,
    ):
        self.config = config or DEFAULT_CONFIG
        self.fuzzy_matcher = fuzzy_matcher or FuzzyMatcher()
        self.bilingual_synonyms: Dict[str, List[str]] = {}

        # Load bilingual synonyms if path given or default exists
        if synonym_dict_path and Path(synonym_dict_path).exists():
            try:
                with open(synonym_dict_path, encoding="utf-8") as f:
                    self.bilingual_synonyms = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load synonym dict: {e}")

    def normalize_technical_phrases(self, query: str) -> Tuple[str, List[CorrectionItem]]:
        """Normalizes multi-word technical phrases like 'tf idf' -> 'tf-idf'."""
        corrections = []
        normalized = query
        q_lower = query.lower()

        for phrase, canonical in TECHNICAL_PHRASES.items():
            pattern = r'\b' + re.escape(phrase) + r'\b'
            if re.search(pattern, q_lower):
                normalized = re.sub(pattern, canonical, normalized, flags=re.IGNORECASE)
                corrections.append(CorrectionItem(
                    source=phrase,
                    target=canonical,
                    correction_type="technical",
                    confidence=0.99,
                    note="Normalisasi frasa istilah teknis"
                ))
                q_lower = normalized.lower()

        return normalized, corrections

    def process(self, query: str) -> TolerantAnalysisResult:
        """
        Main query processing entry point.
        Analyzes query tokens, applies corrections, and builds explainability report.
        """
        raw_query = (query or "").strip()
        if not raw_query:
            return TolerantAnalysisResult(
                original_query="",
                normalized_query="",
                is_modified=False,
            )

        corrections: List[CorrectionItem] = []
        expanded_terms: List[str] = []

        # Step 1: Normalize compound technical phrases
        tech_normalized, tech_corrections = self.normalize_technical_phrases(raw_query)
        corrections.extend(tech_corrections)

        # Step 2: Tokenize while preserving protected terms (e.g. C++, .NET, BERT-base)
        # We split by whitespace but keep compound tokens
        tokens = tech_normalized.split()
        normalized_tokens: List[str] = []

        overall_confidence = 1.0

        for token in tokens:
            t_lower = token.lower()

            # Guard 1: Protected Technical Terms (Section 9)
            if t_lower in PROTECTED_TERMS:
                normalized_tokens.append(token)
                continue

            # Strip leading/trailing punctuation for analysis, keeping internal hyphens
            prefix = ""
            suffix = ""
            core = token
            while core and core[0] in '([{"\'':
                prefix += core[0]
                core = core[1:]
            while core and core[-1] in ')]}",.?!;:':
                suffix = core[-1] + suffix
                core = core[:-1]

            if not core:
                normalized_tokens.append(token)
                continue

            core_lower = core.lower()

            # Guard 2: Protected term on core token
            if core_lower in PROTECTED_TERMS:
                normalized_tokens.append(token)
                continue

            # Check 3: Abbreviation Handling (Section 8)
            if self.config.get("abbreviation", {}).get("enabled", True) and core_lower in ABBREVIATIONS:
                abbr_info = ABBREVIATIONS[core_lower]
                canonical = abbr_info["canonical"]
                conf = abbr_info["confidence"]

                # If uppercase (e.g. NLP), it's strongly an abbreviation
                if core.isupper() or len(core) <= 4:
                    corrections.append(CorrectionItem(
                        source=core,
                        target=canonical,
                        correction_type="abbreviation",
                        confidence=conf,
                        note=f"Ekspansi singkatan: {abbr_info.get('indonesian', '')}"
                    ))
                    expanded_terms.append(canonical)
                    # Keep core acronym in normalized query, expansion will be offered
                    normalized_tokens.append(f"{prefix}{core}{suffix}")
                    continue

            # Check 4: Spelling Variations (Section 7)
            if self.config.get("spelling_variation", {}).get("enabled", True) and core_lower in SPELLING_VARIATIONS:
                replacement = SPELLING_VARIATIONS[core_lower]
                corrections.append(CorrectionItem(
                    source=core,
                    target=replacement,
                    correction_type="spelling",
                    confidence=0.98,
                    note="Standarisasi variasi ejaan akademik"
                ))
                normalized_tokens.append(f"{prefix}{replacement}{suffix}")
                overall_confidence = min(overall_confidence, 0.98)
                continue

            # Check 5: Morphological Variants (Section 10)
            if self.config.get("morphology", {}).get("enabled", True) and core_lower in MORPHOLOGICAL_VARIANTS:
                # Only normalize if variant is widely accepted
                stemmed = MORPHOLOGICAL_VARIANTS[core_lower]
                # We record it but don't force replace if exact term exists in vocab
                if not self.fuzzy_matcher.contains(core_lower):
                    corrections.append(CorrectionItem(
                        source=core,
                        target=stemmed,
                        correction_type="morphology",
                        confidence=0.90,
                        note="Normalisasi bentuk morfologis kata"
                    ))
                    normalized_tokens.append(f"{prefix}{stemmed}{suffix}")
                    overall_confidence = min(overall_confidence, 0.90)
                    continue

            # Check 6: Exact vocabulary match (Section 3.2: Prioritize Exact)
            if self.fuzzy_matcher.contains(core_lower):
                normalized_tokens.append(token)
                continue

            # Check 7: Typo Correction & Fuzzy Term Matching (Section 5 & 6)
            if self.config.get("typo", {}).get("enabled", True) and len(core_lower) >= 3:
                candidates = self.fuzzy_matcher.find_candidates(
                    core_lower,
                    threshold=self.config.get("fuzzy", {}).get("similarity_threshold", 0.82),
                    max_results=1,
                )
                if candidates:
                    best = candidates[0]
                    # Accept if confidence meets threshold and candidate is distinct
                    if best["confidence"] >= self.config.get("typo", {}).get("min_confidence", 0.82) and best["candidate"] != core_lower:
                        target_word = best["candidate"]
                        corrections.append(CorrectionItem(
                            source=core,
                            target=target_word,
                            correction_type="typo",
                            confidence=best["confidence"],
                            note=f"Koreksi typo (jarak edit: {best['distance']})"
                        ))
                        normalized_tokens.append(f"{prefix}{target_word}{suffix}")
                        overall_confidence = min(overall_confidence, best["confidence"])
                        continue

            # Default: Keep token as-is
            normalized_tokens.append(token)

        normalized_query_str = " ".join(normalized_tokens)

        # Check 8: Cross-lingual phrase matching for expanded terms (Section 11)
        if self.config.get("cross_lingual", {}).get("enabled", True):
            norm_lower = normalized_query_str.lower()
            for id_phrase, en_syns in self.bilingual_synonyms.items():
                if id_phrase in norm_lower:
                    for syn in en_syns[:2]:
                        if syn not in expanded_terms:
                            expanded_terms.append(syn)
                            corrections.append(CorrectionItem(
                                source=id_phrase,
                                target=syn,
                                correction_type="cross_lingual",
                                confidence=0.92,
                                note="Padanan istilah dwibahasa (ID <-> EN)"
                            ))

        is_modified = (normalized_query_str.lower() != raw_query.lower()) or bool(expanded_terms)

        # Did-you-mean suggestion query
        did_you_mean = normalized_query_str if (normalized_query_str.lower() != raw_query.lower()) else None

        return TolerantAnalysisResult(
            original_query=raw_query,
            normalized_query=normalized_query_str,
            did_you_mean=did_you_mean,
            expanded_terms=expanded_terms,
            corrections=corrections,
            confidence=overall_confidence if is_modified else 1.0,
            is_modified=is_modified,
        )
