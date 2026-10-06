"""
Academic IR System — BM25 Retriever (Baseline B)
=================================================
Implements BM25 (Okapi BM25) retrieval as a second lexical baseline,
with the same interface as SearchEngine for drop-in comparison.

Why BM25 instead of only TF-IDF?
  - BM25 includes document-length normalization (parameter b)
  - BM25 applies a different term-frequency saturation function (k1)
  - BM25 is the de-facto standard strong lexical retrieval baseline
  - Comparison answers RQ2: "Does BM25 improve academic document retrieval
    over TF-IDF?" (expert plan §6.2, §33)

Default parameters (Okapi BM25):
  k1 = 1.5  (term frequency saturation)
  b  = 0.75 (document length normalization)

Requirements:
  pip install rank-bm25

Expert plan references: §6.2, §28 Phase 4, §33 RQ2
"""

import logging
import joblib
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    BM25 (Okapi BM25) retriever with document-level aggregation.

    Provides the same search() interface as SearchEngine (TF-IDF)
    so they can be swapped transparently via retrieval_mode parameter.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term frequency saturation parameter (default 1.5)
            b:  Document length normalization parameter (default 0.75)
        """
        try:
            from rank_bm25 import BM25Okapi
            self._BM25Okapi = BM25Okapi
        except ImportError:
            raise ImportError(
                "rank-bm25 is required. Install with: pip install rank-bm25"
            )

        self.k1 = k1
        self.b = b
        self.bm25 = None
        self.chunk_ids: list = []
        self.chunk_meta: dict = {}
        self.is_fitted = False

    # ── Build ──────────────────────────────────────────────────────────────

    def build_index(self, chunks: list) -> dict:
        """
        Build BM25 index from a list of chunk dicts.

        Args:
            chunks: List of dicts with keys 'chunk_id' and 'clean_text'
                    plus any metadata fields.

        Returns:
            Dict with index statistics.
        """
        if not chunks:
            raise ValueError("No chunks provided for BM25 indexing.")

        logger.info(f"Building BM25 index from {len(chunks)} chunks...")

        self.chunk_ids = [c['chunk_id'] for c in chunks]
        self.chunk_meta = {c['chunk_id']: c for c in chunks}

        # Tokenize: BM25 expects list of token lists
        tokenized = [
            (c.get('clean_text') or '').split()
            for c in chunks
        ]

        self.bm25 = self._BM25Okapi(tokenized, k1=self.k1, b=self.b)
        self.is_fitted = True

        logger.info(
            f"BM25 index built: {len(self.chunk_ids)} chunks, "
            f"k1={self.k1}, b={self.b}"
        )
        return {
            "chunk_count": len(self.chunk_ids),
            "k1": self.k1,
            "b": self.b,
        }

    # ── Search ─────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10,
               language: str = None,
               document_type: str = None,
               source: str = None,
               year_from: int = None,
               year_to: int = None,
               course: str = None,
               aggregation_strategy: str = "max+2nd",
               candidate_k: int = 500) -> list:
        """
        Search with BM25 and return document-level aggregated results.

        Args:
            query: Raw search query string
            top_k: Number of documents to return after aggregation
            language: Filter by language ('en', 'id')
            document_type: Filter by type ('MATERIAL', 'RESEARCH', 'THESIS')
            source: Filter by source name
            year_from: Minimum publication year
            year_to: Maximum publication year
            course: Filter by course name
            aggregation_strategy: "max" | "max+2nd" | "topN_avg"
            candidate_k: Size of candidate pool before filtering (default 500)

        Returns:
            List of document-level result dicts sorted by score descending.
        """
        if not self.is_fitted:
            raise RuntimeError("BM25 index not built. Call build_index() or load() first.")

        if not query or not query.strip():
            return []

        # Tokenize query
        query_tokens = query.lower().split()

        # Get BM25 scores for all chunks
        scores = self.bm25.get_scores(query_tokens)

        # Get top candidate_k by score (before filtering)
        pool_size = min(candidate_k, len(scores))
        top_indices = np.argpartition(scores, -pool_size)[-pool_size:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        # Build candidate list with metadata filtering
        candidates = []
        for i in top_indices:
            score = float(scores[i])
            if score <= 0:
                continue

            chunk_id = self.chunk_ids[i]
            meta = self.chunk_meta.get(chunk_id)
            if meta is None:
                continue

            # Apply metadata filters within candidate pool
            if document_type and meta.get('document_type') != document_type:
                continue
            if language and meta.get('language') != language:
                continue
            if source and meta.get('source') != source:
                continue
            if year_from and meta.get('year') and meta['year'] < year_from:
                continue
            if year_to and meta.get('year') and meta['year'] > year_to:
                continue
            if course and meta.get('course') != course:
                continue

            candidates.append({
                'chunk_id': chunk_id,
                'document_id': meta.get('document_id', ''),
                'document_type': meta.get('document_type', ''),
                'title': meta.get('title', ''),
                'abstract': meta.get('abstract', ''),
                'authors': meta.get('authors', ''),
                'course': meta.get('course', ''),
                'year': meta.get('year'),
                'language': meta.get('language', ''),
                'source': meta.get('source', ''),
                'institution': meta.get('institution', ''),
                'keywords': meta.get('keywords', ''),
                'doi': meta.get('doi', ''),
                'page': meta.get('page_start'),
                'page_start': meta.get('page_start'),
                'page_end': meta.get('page_end'),
                'score': score,
                'raw_text': meta.get('raw_text', ''),
                'source_url': meta.get('source_url', ''),
                'local_path': meta.get('local_path', ''),
                'snippet': (meta.get('raw_text') or '')[:250],
            })

        if not candidates:
            return []

        # Document-level aggregation
        from .aggregation import aggregate_by_document
        doc_results = aggregate_by_document(candidates, strategy=aggregation_strategy)

        return doc_results[:top_k]

    # ── Persistence ────────────────────────────────────────────────────────

    def save(self, output_dir: str) -> None:
        """Save BM25 index and metadata to disk."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        joblib.dump({
            'bm25': self.bm25,
            'chunk_ids': self.chunk_ids,
            'chunk_meta': self.chunk_meta,
            'k1': self.k1,
            'b': self.b,
        }, Path(output_dir) / "bm25_index.pkl")
        logger.info(f"BM25 index saved to {output_dir}")

    def load(self, output_dir: str) -> None:
        """Load BM25 index from disk."""
        index_path = Path(output_dir) / "bm25_index.pkl"
        if not index_path.exists():
            raise FileNotFoundError(f"BM25 index not found at {index_path}")
        data = joblib.load(index_path)
        self.bm25 = data['bm25']
        self.chunk_ids = data['chunk_ids']
        self.chunk_meta = data['chunk_meta']
        self.k1 = data.get('k1', self.k1)
        self.b = data.get('b', self.b)
        self.is_fitted = True
        logger.info(
            f"BM25 index loaded from {output_dir}: "
            f"{len(self.chunk_ids)} chunks, k1={self.k1}, b={self.b}"
        )
