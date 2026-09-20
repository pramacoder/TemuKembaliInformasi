"""
Academic IR System — Unified Search Engine
============================================
Chunk-level search with cosine similarity over unified TF-IDF index.
"""

import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Unified search engine that searches across all corpus types.

    Features:
    - Chunk-level retrieval (not document-level)
    - Cosine similarity scoring
    - Document type filtering
    - Language filtering
    - Source filtering
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
                           d.source_url, d.local_path, d.institution
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
               course: str = None) -> list:
        """
        Search the unified index.

        Args:
            query: Raw search query
            top_k: Number of results to return
            language: Filter by language code ('en', 'id')
            document_type: Filter by type ('MATERIAL', 'RESEARCH', 'THESIS')
            source: Filter by source ('OCW_UI', 'CORE', 'DOAJ', 'REPOSITORY')
            year_from: Minimum year filter
            year_to: Maximum year filter
            course: Filter by course name (for MATERIAL)

        Returns:
            List of result dicts with rank, score, document info, page, and snippet
        """
        if not query or not query.strip():
            return []

        # 1. Preprocess query
        processed_query = self.pipeline.process_query(query)
        if not processed_query:
            # If preprocessing removes everything, try with less aggressive cleaning
            processed_query = query.lower()

        # 2. Transform query to TF-IDF vector
        query_vec = self.index.transform([processed_query])

        # 3. Compute cosine similarity against all chunks
        scores = cosine_similarity(query_vec, self.index.tfidf_matrix).flatten()

        # 4. Get chunk metadata
        chunk_meta = self._load_chunk_metadata()

        # 5. Build results with filtering
        results = []
        for i, chunk_id in enumerate(self.index.chunk_ids):
            score = float(scores[i])
            if score <= 0:
                continue

            meta = chunk_meta.get(chunk_id)
            if meta is None:
                continue

            # Apply filters
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

            results.append({
                'chunk_id': chunk_id,
                'document_id': meta['document_id'],
                'document_type': meta['document_type'],
                'title': meta['title'],
                'course': meta['course'],
                'year': meta['year'],
                'language': meta['language'],
                'source': meta['source'],
                'institution': meta['institution'],
                'page': meta['page_start'],
                'page_start': meta['page_start'],
                'page_end': meta.get('page_end'),
                'score': score,
                'raw_text': meta.get('raw_text', ''),
                'source_url': meta.get('source_url'),
                'local_path': meta.get('local_path'),
            })

        # 6. Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)

        # 7. Deduplicate: keep best chunk per document
        seen_docs = set()
        deduplicated = []
        for r in results:
            if r['document_id'] not in seen_docs:
                seen_docs.add(r['document_id'])
                deduplicated.append(r)
            if len(deduplicated) >= top_k:
                break

        # 8. Add rank and snippet
        from .snippet import generate_snippet
        for rank, result in enumerate(deduplicated, 1):
            result['rank'] = rank
            result['snippet'] = generate_snippet(
                result.get('raw_text', ''), query, max_length=200
            )

        return deduplicated

