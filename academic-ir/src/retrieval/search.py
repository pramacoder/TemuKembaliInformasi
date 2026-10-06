"""
Academic IR System — Unified Search Engine
============================================
Chunk-level search with cosine similarity over unified TF-IDF index,
followed by document-level aggregation.

Changes from baseline:
  - FIXED (P0.5): Filters now applied on a large candidate pool (candidate_k)
    BEFORE final ranking, not after iterating every scored chunk.
  - FIXED (P0.2): Replaced simple seen_docs dedup with proper document-level
    aggregation via src.retrieval.aggregation module.
  - Added support for aggregation_strategy parameter.
  - Added candidate_k parameter (default 500) for pre-filter pool size.

Expert plan references: §P0.2, §P0.5, §8
"""

import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .aggregation import aggregate_by_document

logger = logging.getLogger(__name__)

# Default candidate pool size — fetch this many chunks before filtering/aggregating.
# Larger = better recall for filtered queries, but slightly higher memory use.
DEFAULT_CANDIDATE_K = 500


class SearchEngine:
    """
    Unified search engine that searches across all corpus types.

    Features:
    - Chunk-level TF-IDF retrieval with cosine similarity scoring
    - Large candidate pool before metadata filtering (fixes P0.5)
    - Document-level aggregation with configurable strategy (fixes P0.2)
    - Document type, language, source, year, course filtering
    """

    def __init__(self, tfidf_index, db, preprocessing_pipeline):
        """
        Args:
            tfidf_index: Fitted TFIDFIndex instance
            db: Database instance
            preprocessing_pipeline: PreprocessingPipeline instance
        """
        self.index = tfidf_index
        self.db = db
        self.pipeline = preprocessing_pipeline
        self._chunk_metadata_cache = None

    def _load_chunk_metadata(self):
        """Load and cache chunk-to-document mapping."""
        if self._chunk_metadata_cache is None:
            conn = self.db.get_connection()
            try:
                rows = conn.execute("""
                    SELECT c.chunk_id, c.document_id, c.page_start, c.page_end,
                           c.chunk_index, c.raw_text,
                           d.document_type, d.title, d.abstract, d.authors,
                           d.course, d.year, d.language, d.source,
                           d.source_url, d.local_path, d.institution,
                           d.keywords, d.doi
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.document_id
                    WHERE c.clean_text IS NOT NULL AND c.clean_text != ''
                    ORDER BY c.chunk_id
                """).fetchall()
                self._chunk_metadata_cache = {
                    row['chunk_id']: dict(row) for row in rows
                }
            finally:
                conn.close()
        return self._chunk_metadata_cache

    def search(self, query: str, top_k: int = 10,
               language: str = None,
               document_type: str = None,
               source: str = None,
               year_from: int = None,
               year_to: int = None,
               course: str = None,
               aggregation_strategy: str = "max+2nd",
               candidate_k: int = DEFAULT_CANDIDATE_K) -> list:
        """
        Search the unified index with document-level aggregation.

        Args:
            query: Raw search query
            top_k: Number of DOCUMENTS to return (after aggregation)
            language: Filter by language code ('en', 'id')
            document_type: Filter by type ('MATERIAL', 'RESEARCH', 'THESIS')
            source: Filter by source ('OCW_UI', 'CORE', 'DOAJ', 'REPOSITORY')
            year_from: Minimum year filter
            year_to: Maximum year filter
            course: Filter by course name (for MATERIAL)
            aggregation_strategy: How to merge chunk scores into a document score.
                One of "max", "max+2nd", "topN_avg". Default: "max+2nd".
            candidate_k: Size of initial chunk candidate pool before filtering.
                Larger values improve recall for filtered queries at small cost.
                Default: 500. Set to 0 for "all chunks with score > 0".

        Returns:
            List of document-level result dicts, sorted by document_score desc.
            Each result includes best evidence page, snippet, and matched_chunks.
        """
        if not query or not query.strip():
            return []

        # ── 1. Preprocess query ──────────────────────────────────────────────
        processed_query = self.pipeline.process_query(query)
        if not processed_query:
            processed_query = query.lower()

        # ── 2. Transform query to TF-IDF vector ─────────────────────────────
        query_vec = self.index.transform([processed_query])

        # ── 3. Compute cosine similarity against ALL chunks ──────────────────
        scores = cosine_similarity(query_vec, self.index.tfidf_matrix).flatten()

        # ── 4. Get top candidate_k chunk indices (BEFORE any metadata filter)
        #       This is the key fix for P0.5: we never filter before building
        #       the candidate pool. We only filter WITHIN the candidate pool.
        if candidate_k > 0:
            # Use argpartition for efficiency, then sort
            pool_size = min(candidate_k, len(scores))
            # Get indices of top pool_size scores
            top_indices = np.argpartition(scores, -pool_size)[-pool_size:]
            # Sort within the partition by score descending
            top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        else:
            # All chunks with score > 0
            top_indices = np.where(scores > 0)[0]
            top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

        # ── 5. Load metadata, build candidate list ───────────────────────────
        chunk_meta = self._load_chunk_metadata()
        candidates = []

        for i in top_indices:
            score = float(scores[i])
            if score <= 0:
                continue

            chunk_id = self.index.chunk_ids[i]
            meta = chunk_meta.get(chunk_id)
            if meta is None:
                continue

            # ── 6. Apply metadata filters WITHIN the candidate pool ──────────
            #       (FIXED from baseline — filters happen here, not after scoring)
            if document_type and meta['document_type'] != document_type:
                continue
            if language and meta['language'] != language:
                continue
            if source and meta['source'] != source:
                continue
            if year_from and meta['year'] and meta['year'] < year_from:
                continue
            if year_to and meta['year'] and meta['year'] > year_to:
                continue
            if course and meta['course'] != course:
                continue

            candidates.append({
                'chunk_id': chunk_id,
                'document_id': meta['document_id'],
                'document_type': meta['document_type'],
                'title': meta['title'],
                'abstract': meta.get('abstract', ''),
                'authors': meta.get('authors', ''),
                'course': meta['course'],
                'year': meta['year'],
                'language': meta['language'],
                'source': meta['source'],
                'institution': meta['institution'],
                'keywords': meta.get('keywords', ''),
                'doi': meta.get('doi', ''),
                'page': meta['page_start'],
                'page_start': meta['page_start'],
                'page_end': meta.get('page_end'),
                'score': score,
                'raw_text': meta.get('raw_text', ''),
                'source_url': meta.get('source_url'),
                'local_path': meta.get('local_path'),
            })

        if not candidates:
            return []

        # ── 7. Add snippets to each candidate chunk ──────────────────────────
        from .snippet import generate_snippet
        for chunk in candidates:
            chunk['snippet'] = generate_snippet(
                chunk.get('raw_text', ''), query, max_length=250
            )

        # ── 8. Document-level aggregation ────────────────────────────────────
        #       Groups chunks by document_id and computes a single document score
        doc_results = aggregate_by_document(candidates, strategy=aggregation_strategy)

        # ── 9. Return top_k documents ────────────────────────────────────────
        return doc_results[:top_k]
