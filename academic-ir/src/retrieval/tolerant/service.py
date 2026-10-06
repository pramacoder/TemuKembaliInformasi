"""
Tolerant Retrieval — Service & Engine Factory
=============================================
Manages initialization, vocabulary indexing, and query autocompletion suggestions.
Provides a singleton interface for FastAPI and other search callers.
"""

import logging
import pickle
import re
import sqlite3
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .constants import (
    ABBREVIATIONS,
    DEFAULT_CONFIG,
    PROTECTED_TERMS,
    SPELLING_VARIATIONS,
    TECHNICAL_PHRASES,
)
from .fallback_controller import FallbackController, TolerantSearchMetadata
from .fuzzy_matcher import FuzzyMatcher
from .processor import TolerantAnalysisResult, TolerantQueryProcessor

logger = logging.getLogger(__name__)


class TolerantRetrievalService:
    """
    Central service for Tolerant Retrieval in the Academic IR system.
    """

    def __init__(self, db_path: Optional[str] = None, models_dir: Optional[str] = None):
        self.project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.db_path = db_path or str(self.project_root / "database" / "academic_ir.db")
        self.models_dir = models_dir or str(self.project_root / "models")
        self.synonym_path = str(self.project_root / "data" / "synonym_dict_bilingual.json")

        self.fuzzy_matcher = FuzzyMatcher(
            similarity_threshold=DEFAULT_CONFIG["fuzzy"]["similarity_threshold"],
            max_candidates=DEFAULT_CONFIG["fuzzy"]["max_candidates"],
            max_edit_distance=DEFAULT_CONFIG["typo"]["max_edit_distance"],
        )

        self._load_vocabulary()

        self.processor = TolerantQueryProcessor(
            fuzzy_matcher=self.fuzzy_matcher,
            config=DEFAULT_CONFIG,
            synonym_dict_path=self.synonym_path,
        )

        self.fallback_controller = FallbackController(
            processor=self.processor,
            min_adequate_results=DEFAULT_CONFIG["fallback"]["min_adequate_results"],
            min_top_score_bm25=DEFAULT_CONFIG["fallback"]["min_top_score_bm25"],
            min_top_score_tfidf=DEFAULT_CONFIG["fallback"]["min_top_score_tfidf"],
        )

        logger.info(
            f"TolerantRetrievalService initialized with {len(self.fuzzy_matcher.vocabulary)} vocabulary terms."
        )

    def _load_vocabulary(self):
        """Builds vocabulary from SQLite documents metadata and BM25 index."""
        # 1. Add common Indonesian academic functional words & terms
        common_academic_words = [
            "analisis", "analisa", "sistem", "metode", "algoritma", "pembelajaran",
            "mesin", "jaringan", "komputer", "data", "penelitian", "skripsi", "tesis",
            "jurnal", "informasi", "perancangan", "implementasi", "evaluasi",
            "pengujian", "optimasi", "pengolahan", "citra", "klasifikasi", "prediksi",
            "model", "kinerja", "akurasi", "menggunakan", "berbasis", "terhadap",
            "dengan", "untuk", "pada", "dalam", "studi", "kasus", "antarmuka",
            "pengguna", "proses", "manajemen", "proyek", "struktur", "matriks",
            "relasional", "pencarian", "peringkat", "dokumen", "sentimen", "opini",
            "publik", "media", "sosial", "teks", "ruang", "vektor", "kemiripan",
            "kosinus", "kalkulus", "integral", "diferensial", "aljabar", "linier",
            "probabilitas", "statistika", "dasar", "pemrograman", "fungsional",
            "arsitektur", "pipelining", "memori", "rekayasa", "perangkat", "lunak",
            "aplikasi", "web", "basis", "database", "clustering", "classification",
            "machine", "learning", "deep", "neural", "network", "vision",
            "natural", "language", "processing", "retrieval", "artificial", "intelligence"
        ]
        for w in common_academic_words:
            self.fuzzy_matcher.add_term(w, frequency=50)

        # 2. Add terms from SQLite database metadata
        if Path(self.db_path).exists():
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                rows = cur.execute("SELECT title, course, keywords FROM documents").fetchall()
                for title, course, kws in rows:
                    text = f"{title or ''} {course or ''} {kws or ''}"
                    tokens = re.findall(r"[a-zA-Z0-9_\-\.\+]+", text.lower())
                    for token in tokens:
                        if len(token) >= 3 and not token.isdigit():
                            self.fuzzy_matcher.add_term(token, frequency=10)
                conn.close()
            except Exception as e:
                logger.warning(f"Could not load vocabulary from SQLite: {e}")

        # 3. Add top frequent terms from BM25 index if available
        bm25_path = Path(self.models_dir) / "bm25_v1" / "bm25_index.pkl"
        if bm25_path.exists():
            try:
                with open(bm25_path, "rb") as f:
                    data = pickle.load(f)
                bm25_obj = data.get("bm25")
                if bm25_obj and hasattr(bm25_obj, "idf"):
                    # idf is lower for more frequent terms: sort by idf ascending
                    sorted_terms = sorted(bm25_obj.idf.items(), key=lambda x: x[1])
                    for term, idf_val in sorted_terms[:25000]:
                        if len(term) >= 3 and not term.isdigit():
                            # Inverse idf as pseudo-frequency
                            freq = int(max(1, (10.0 - idf_val) * 10))
                            self.fuzzy_matcher.add_term(term, frequency=freq)
            except Exception as e:
                logger.warning(f"Could not load BM25 vocabulary: {e}")

        # 4. Add canonical targets from abbreviations and spelling variations
        for abbr, info in ABBREVIATIONS.items():
            for w in info["canonical"].split():
                self.fuzzy_matcher.add_term(w, frequency=100)
            for w in info.get("indonesian", "").split():
                self.fuzzy_matcher.add_term(w, frequency=100)

        for non_std, std in SPELLING_VARIATIONS.items():
            for w in std.split():
                self.fuzzy_matcher.add_term(w, frequency=100)

    def analyze_query(self, query: str) -> TolerantAnalysisResult:
        """Analyzes a query and produces tolerant analysis report."""
        return self.processor.process(query)

    def search(
        self,
        query: str,
        search_fn: Callable[[str], List[Dict[str, any]]],
        mode: str = "auto",
        retrieval_mode: str = "bm25",
    ) -> Tuple[List[Dict[str, any]], TolerantSearchMetadata]:
        """Runs search via FallbackController."""
        return self.fallback_controller.execute_search(
            query=query,
            search_fn=search_fn,
            mode=mode,
            retrieval_mode=retrieval_mode,
        )

    def get_suggestions(self, query: str, limit: int = 5) -> Dict[str, any]:
        """
        Fast autocompletion and interactive typo suggestion generator for the search bar.
        """
        raw = (query or "").strip()
        if not raw or len(raw) < 2:
            return {
                "query": raw,
                "did_you_mean": None,
                "suggestions": [],
                "corrections": [],
            }

        analysis = self.processor.process(raw)
        suggestions: List[str] = []

        # If normalized query is different from raw query, make it the #1 suggestion
        if analysis.did_you_mean:
            suggestions.append(analysis.did_you_mean)

        # Check abbreviation expansions
        raw_lower = raw.lower()
        if raw_lower in ABBREVIATIONS:
            canon = ABBREVIATIONS[raw_lower]["canonical"]
            if canon not in suggestions:
                suggestions.append(canon)

        # Prefix autocompletion from last token if user is actively typing
        tokens = raw.split()
        if tokens:
            last_token = tokens[-1].lower()
            prefix_base = " ".join(tokens[:-1]) + (" " if len(tokens) > 1 else "")
            if len(last_token) >= 2:
                # Find vocabulary terms starting with last_token
                matches = [
                    w for w in self.fuzzy_matcher.vocabulary
                    if w.startswith(last_token) and w != last_token
                ]
                # Sort by frequency
                matches.sort(key=lambda w: self.fuzzy_matcher.term_frequencies.get(w, 0), reverse=True)
                for m in matches[:3]:
                    sug = f"{prefix_base}{m}"
                    if sug not in suggestions and sug.lower() != raw_lower:
                        suggestions.append(sug)

        return {
            "query": raw,
            "did_you_mean": analysis.did_you_mean,
            "suggestions": suggestions[:limit],
            "corrections": [c.to_dict() for c in analysis.corrections],
            "expanded_terms": analysis.expanded_terms,
            "confidence": analysis.confidence,
        }


# Global singleton instance
_SERVICE_INSTANCE: Optional[TolerantRetrievalService] = None


def get_tolerant_service() -> TolerantRetrievalService:
    global _SERVICE_INSTANCE
    if _SERVICE_INSTANCE is None:
        _SERVICE_INSTANCE = TolerantRetrievalService()
    return _SERVICE_INSTANCE
