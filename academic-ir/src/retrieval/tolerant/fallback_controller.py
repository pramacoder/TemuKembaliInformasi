"""
Tolerant Retrieval — Fallback Controller
========================================
Implements the Exact-First prioritization strategy (Sections 3.2 & 17 of spec).
Evaluates initial retrieval quality before deciding whether to engage
Tolerant Retrieval normalization and recovery.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from .processor import TolerantAnalysisResult, TolerantQueryProcessor

logger = logging.getLogger(__name__)


class TolerantSearchMetadata:
    def __init__(
        self,
        applied: bool,
        mode: str,
        original_query: str,
        effective_query: str,
        did_you_mean: Optional[str] = None,
        corrections: Optional[List[Dict[str, any]]] = None,
        expanded_terms: Optional[List[str]] = None,
        fallback_triggered: bool = False,
        confidence: float = 1.0,
        explanation: str = "",
    ):
        self.applied = applied
        self.mode = mode
        self.original_query = original_query
        self.effective_query = effective_query
        self.did_you_mean = did_you_mean
        self.corrections = corrections or []
        self.expanded_terms = expanded_terms or []
        self.fallback_triggered = fallback_triggered
        self.confidence = round(confidence, 4)
        self.explanation = explanation

    def to_dict(self) -> Dict[str, any]:
        return {
            "applied": self.applied,
            "mode": self.mode,
            "original_query": self.original_query,
            "effective_query": self.effective_query,
            "did_you_mean": self.did_you_mean,
            "corrections": self.corrections,
            "expanded_terms": self.expanded_terms,
            "fallback_triggered": self.fallback_triggered,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


class FallbackController:
    """
    Manages the lifecycle between Exact Search and Tolerant Search.
    Guarantees that exact search is never degraded when results are already strong.
    """

    def __init__(
        self,
        processor: TolerantQueryProcessor,
        min_adequate_results: int = 3,
        min_top_score_bm25: float = 1.0,
        min_top_score_tfidf: float = 0.08,
    ):
        self.processor = processor
        self.min_adequate_results = min_adequate_results
        self.min_top_score_bm25 = min_top_score_bm25
        self.min_top_score_tfidf = min_top_score_tfidf

    def is_adequate(self, results: List[Dict[str, any]], retrieval_mode: str = "bm25") -> bool:
        """Evaluates whether exact retrieval results are satisfactory."""
        if not results:
            return False

        if len(results) < self.min_adequate_results:
            return False

        top_score = results[0].get("score") or results[0].get("document_score", 0.0)
        threshold = self.min_top_score_bm25 if retrieval_mode == "bm25" else self.min_top_score_tfidf
        return top_score >= threshold

    def execute_search(
        self,
        query: str,
        search_fn: Callable[[str], List[Dict[str, any]]],
        mode: str = "auto",
        retrieval_mode: str = "bm25",
    ) -> Tuple[List[Dict[str, any]], TolerantSearchMetadata]:
        """
        Executes search with exact-first and tolerant fallback logic.

        Args:
            query: User search query
            search_fn: Function that accepts a query string and returns ranked document list
            mode: 'auto' (fallback), 'always' (force normalization), 'off' (exact only)
            retrieval_mode: 'bm25' or 'tfidf'

        Returns:
            Tuple of (ranked_results, TolerantSearchMetadata)
        """
        raw_query = (query or "").strip()
        if not raw_query:
            return [], TolerantSearchMetadata(
                applied=False,
                mode=mode,
                original_query="",
                effective_query="",
            )

        # Pre-analyze query with tolerant processor
        analysis = self.processor.process(raw_query)

        # Case 1: Mode is 'off' — strict exact search only
        if mode == "off":
            results = search_fn(raw_query)
            meta = TolerantSearchMetadata(
                applied=False,
                mode="off",
                original_query=raw_query,
                effective_query=raw_query,
                did_you_mean=analysis.did_you_mean,
                corrections=[c.to_dict() for c in analysis.corrections],
                confidence=1.0,
                explanation="Pencarian eksak (Tolerant Retrieval dimatikan pengguna).",
            )
            return results, meta

        # Case 2: Mode is 'always' — force tolerant normalization
        if mode == "always":
            effective = analysis.normalized_query if analysis.is_modified else raw_query
            results = search_fn(effective)
            explanation = (
                f"Tolerant retrieval aktif: '{raw_query}' → '{effective}'"
                if analysis.is_modified
                else "Kueri sudah dalam bentuk baku."
            )
            meta = TolerantSearchMetadata(
                applied=analysis.is_modified,
                mode="always",
                original_query=raw_query,
                effective_query=effective,
                did_you_mean=analysis.did_you_mean,
                corrections=[c.to_dict() for c in analysis.corrections],
                expanded_terms=analysis.expanded_terms,
                confidence=analysis.confidence,
                explanation=explanation,
            )
            return results, meta

        # Case 3: Mode is 'auto' (Default — Exact First, Fallback on poor/zero results)
        # 1. Run exact search first
        exact_results = search_fn(raw_query)

        # Check if exact search is adequate
        if self.is_adequate(exact_results, retrieval_mode):
            meta = TolerantSearchMetadata(
                applied=False,
                mode="auto",
                original_query=raw_query,
                effective_query=raw_query,
                did_you_mean=analysis.did_you_mean,
                corrections=[c.to_dict() for c in analysis.corrections],
                expanded_terms=analysis.expanded_terms,
                fallback_triggered=False,
                confidence=1.0,
                explanation="Hasil pencarian eksak memadai. Tolerant fallback tidak dipicu.",
            )
            return exact_results, meta

        # 2. Exact search is poor or zero hits -> check if query can be recovered
        if analysis.is_modified and analysis.normalized_query.lower() != raw_query.lower():
            logger.info(
                f"[Tolerant Fallback] Exact query '{raw_query}' had {len(exact_results)} results. "
                f"Falling back to normalized query '{analysis.normalized_query}'"
            )
            normalized_results = search_fn(analysis.normalized_query)

            # If normalized search yielded better results, return them!
            if normalized_results:
                meta = TolerantSearchMetadata(
                    applied=True,
                    mode="auto",
                    original_query=raw_query,
                    effective_query=analysis.normalized_query,
                    did_you_mean=analysis.did_you_mean,
                    corrections=[c.to_dict() for c in analysis.corrections],
                    expanded_terms=analysis.expanded_terms,
                    fallback_triggered=True,
                    confidence=analysis.confidence,
                    explanation=(
                        f"Hasil pencarian awal minim ({len(exact_results)} dokumen). "
                        f"Toleransi typo/istilah aktif: '{raw_query}' dinormalisasi menjadi '{analysis.normalized_query}'."
                    ),
                )
                return normalized_results, meta

        # 3. If normalized also returned nothing, but we have abbreviation/expansion
        if analysis.expanded_terms and len(exact_results) == 0:
            expansion_candidate = f"{raw_query} {analysis.expanded_terms[0]}"
            expanded_results = search_fn(expansion_candidate)
            if expanded_results:
                meta = TolerantSearchMetadata(
                    applied=True,
                    mode="auto",
                    original_query=raw_query,
                    effective_query=expansion_candidate,
                    did_you_mean=analysis.did_you_mean,
                    corrections=[c.to_dict() for c in analysis.corrections],
                    expanded_terms=analysis.expanded_terms,
                    fallback_triggered=True,
                    confidence=analysis.confidence,
                    explanation=f"Pencarian diperluas dengan istilah: {analysis.expanded_terms[0]}.",
                )
                return expanded_results, meta

        # Fallback produced no improvement, return original exact results (even if 0 or few)
        meta = TolerantSearchMetadata(
            applied=False,
            mode="auto",
            original_query=raw_query,
            effective_query=raw_query,
            did_you_mean=analysis.did_you_mean,
            corrections=[c.to_dict() for c in analysis.corrections],
            expanded_terms=analysis.expanded_terms,
            fallback_triggered=False,
            confidence=1.0,
            explanation="Pencarian eksak dijalankan.",
        )
        return exact_results, meta
