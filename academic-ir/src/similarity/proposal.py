"""
Academic IR System — Proposal Similarity
==========================================
Mode 2: Upload a proposal PDF and find the most similar documents in the corpus.

This is NOT a plagiarism detector — it measures topic/document similarity
using the same TF-IDF representation as the search engine.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ProposalSimilarity:
    """
    Compares a new proposal PDF against the existing corpus.

    Key principle: uses vectorizer.transform() (NOT fit_transform)
    to ensure the new proposal is mapped into the existing vocabulary.
    """

    def __init__(self, tfidf_index, db, preprocessing_pipeline):
        """
        Args:
            tfidf_index: Fitted TFIDFIndex instance (same as search)
            db: Database instance
            preprocessing_pipeline: PreprocessingPipeline instance
        """
        self.index = tfidf_index
        self.db = db
        self.pipeline = preprocessing_pipeline

    def check_similarity(self, pdf_path: str, top_k: int = 10) -> dict:
        """
        Compare a proposal PDF against the corpus.

        Pipeline:
            Upload PDF → Extract text → Preprocess → Transform (not fit!)
            → Cosine similarity → Top-K similar documents

        Args:
            pdf_path: Path to the proposal PDF
            top_k: Number of similar documents to return

        Returns:
            dict with proposal info and list of similar documents
        """
        from ..extraction.pdf import extract_pdf
        from ..normalization.language import detect_language
        from sklearn.metrics.pairwise import cosine_similarity

        # 1. Extract text from proposal
        extraction = extract_pdf(pdf_path)
        if not extraction.is_valid():
            return {
                'status': 'FAILED',
                'error': f"Cannot extract text: {extraction.error_message}",
                'similar_documents': [],
            }

        full_text = extraction.full_text

        # 2. Detect language
        lang_result = detect_language(full_text)
        language = lang_result.get('language', 'en') or 'en'

        # 3. Preprocess
        processed_text = self.pipeline.process_document(full_text, language=language)
        if not processed_text:
            return {
                'status': 'FAILED',
                'error': "Preprocessing produced empty text",
                'similar_documents': [],
            }

        # 4. Transform using existing vocabulary (NOT fit_transform!)
        proposal_vec = self.index.transform([processed_text])

        # 5. Compute similarity against all chunks
        scores = cosine_similarity(proposal_vec, self.index.tfidf_matrix).flatten()

        # 6. Map chunks back to documents (best score per document)
        doc_scores = {}
        chunk_meta = self._load_chunk_metadata()

        for i, chunk_id in enumerate(self.index.chunk_ids):
            score = float(scores[i])
            if score <= 0:
                continue

            meta = chunk_meta.get(chunk_id)
            if meta is None:
                continue

            doc_id = meta['document_id']
            if doc_id not in doc_scores or score > doc_scores[doc_id]['score']:
                doc_scores[doc_id] = {
                    'document_id': doc_id,
                    'document_type': meta['document_type'],
                    'title': meta['title'],
                    'course': meta.get('course'),
                    'year': meta.get('year'),
                    'source': meta['source'],
                    'language': meta.get('language'),
                    'score': score,
                    'best_chunk_page': meta.get('page_start'),
                }

        # 7. Sort and return top-K
        similar = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)
        similar = similar[:top_k]

        for rank, doc in enumerate(similar, 1):
            doc['rank'] = rank

        return {
            'status': 'SUCCESS',
            'proposal_file': os.path.basename(pdf_path),
            'proposal_pages': extraction.page_count,
            'proposal_words': extraction.total_words,
            'proposal_language': language,
            'similar_documents': similar,
            'similar_chunks': similar,
            'max_similarity': similar[0]['score'] if similar else 0.0,
            'mean_top_k_similarity': sum(d['score'] for d in similar) / len(similar) if similar else 0.0,
        }

    def check_text_similarity(self, text: str, top_k: int = 10, language: str = None) -> dict:
        """
        Compare a raw proposal text against the corpus.
        """
        from ..normalization.language import detect_language
        from sklearn.metrics.pairwise import cosine_similarity

        if not text or not text.strip():
            return {
                'status': 'FAILED',
                'error': 'Text is empty',
                'similar_documents': [],
                'similar_chunks': [],
                'max_similarity': 0.0,
                'mean_top_k_similarity': 0.0,
            }

        if not language:
            lang_res = detect_language(text)
            language = lang_res.get('language') or 'id'

        processed_text = self.pipeline.process_document(text, language=language)
        if not processed_text:
            processed_text = text.lower()

        proposal_vec = self.index.transform([processed_text])
        scores = cosine_similarity(proposal_vec, self.index.tfidf_matrix).flatten()

        doc_scores = {}
        chunk_meta = self._load_chunk_metadata()

        for i, chunk_id in enumerate(self.index.chunk_ids):
            score = float(scores[i])
            if score <= 0:
                continue

            meta = chunk_meta.get(chunk_id)
            if meta is None:
                continue

            doc_id = meta['document_id']
            if doc_id not in doc_scores or score > doc_scores[doc_id]['score']:
                doc_scores[doc_id] = {
                    'document_id': doc_id,
                    'document_type': meta['document_type'],
                    'title': meta['title'],
                    'course': meta.get('course'),
                    'institution': meta.get('institution', 'Universitas Indonesia'),
                    'year': meta.get('year'),
                    'source': meta['source'],
                    'language': meta.get('language'),
                    'raw_text': meta.get('raw_text', ''),
                    'score': score,
                    'page_start': meta.get('page_start', 1),
                    'best_chunk_page': meta.get('page_start', 1),
                }

        similar = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)[:top_k]
        for rank, doc in enumerate(similar, 1):
            doc['rank'] = rank

        max_sim = similar[0]['score'] if similar else 0.0
        mean_sim = sum(d['score'] for d in similar) / len(similar) if similar else 0.0

        return {
            'status': 'SUCCESS',
            'proposal_file': 'Direct Text Input',
            'proposal_pages': 1,
            'proposal_words': len(text.split()),
            'proposal_language': language,
            'similar_documents': similar,
            'similar_chunks': similar,
            'max_similarity': max_sim,
            'mean_top_k_similarity': mean_sim,
        }

    def analyze_text(self, text: str, top_k: int = 10) -> dict:
        """Alias for check_text_similarity."""
        return self.check_text_similarity(text, top_k=top_k)

    def _load_chunk_metadata(self) -> dict:
        """Load chunk-to-document mapping."""
        conn = self.db.get_connection()
        try:
            rows = conn.execute("""
                SELECT c.chunk_id, c.document_id, c.page_start, c.raw_text,
                       d.document_type, d.title, d.course, d.institution, d.year,
                       d.source, d.language
                FROM chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE c.clean_text IS NOT NULL
            """).fetchall()
            return {row['chunk_id']: dict(row) for row in rows}
        finally:
            conn.close()


# Alias for backwards/forward compatibility
ProposalSimilarityEngine = ProposalSimilarity

