"""
Academic IR System — Summarization Service Orchestrator
========================================================
Main facade orchestrating Document-level Summaries (TextRank + MMR)
and Query-Focused Cross-Lingual Summaries (Embeddings + MMR) with page attribution.
"""

import time
import logging
from typing import Optional, List, Dict, Any, Tuple

from ..database.models import Database
from .schemas import SummaryResponse, SentenceItem
from .lang_detect import detect_document_language
from .preprocessing import extract_candidate_sentences, clean_sentence_text
from .textrank import compute_textrank_scores, ScoredSentence
from .mmr import apply_mmr_selection
from .embeddings import get_multilingual_embedder
from .storage import SummaryStorage

logger = logging.getLogger(__name__)


class SummarizationService:
    """End-to-end summarization service for academic documents."""

    def __init__(self, db: Database):
        self.db = db
        self.storage = SummaryStorage(db)
        self.embedder = get_multilingual_embedder()

    def _fetch_document_content(self, document_id: str) -> Tuple[Optional[dict], List[dict]]:
        """Fetch document metadata and page text units from SQLite."""
        conn = self.db.get_connection()
        try:
            # 1. Fetch document metadata
            doc_row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?",
                (document_id,),
            ).fetchone()

            if not doc_row:
                return None, []

            doc_dict = dict(doc_row)

            # 2. Fetch page units ordered by physical page
            page_rows = conn.execute(
                """
                SELECT page_number, clean_text, raw_text, word_count
                FROM pages
                WHERE document_id = ?
                ORDER BY page_number ASC
                """,
                (document_id,),
            ).fetchall()

            content_units = []
            if page_rows:
                for r in page_rows:
                    raw_content = r["raw_text"] or r["clean_text"] or ""
                    if raw_content.strip():
                        content_units.append({
                            "page_number": r["page_number"],
                            "text": raw_content,
                        })

            # If no page rows found, check chunks
            if not content_units:
                chunk_rows = conn.execute(
                    """
                    SELECT chunk_index, page_start, clean_text, raw_text
                    FROM chunks
                    WHERE document_id = ?
                    ORDER BY chunk_index ASC
                    """,
                    (document_id,),
                ).fetchall()
                for c in chunk_rows:
                    raw_content = c["raw_text"] or c["clean_text"] or ""
                    if raw_content.strip():
                        content_units.append({
                            "page_number": c["page_start"] or 1,
                            "text": raw_content,
                        })

            # If still empty, use document abstract
            if not content_units and doc_dict.get("abstract"):
                content_units.append({
                    "page_number": 1,
                    "text": doc_dict["abstract"],
                })

            return doc_dict, content_units
        finally:
            conn.close()

    def summarize_document(
        self,
        document_id: str,
        max_sentences: int = 4,
        lambda_param: float = 0.70,
        force_refresh: bool = False,
    ) -> SummaryResponse:
        """
        Generate or retrieve extractive summary for a document in its source language.
        Pipeline: Page Text -> LangDetect -> TextRank -> MMR -> Source Page Citations.
        """
        start_time = time.perf_counter()

        # Check SQLite Cache first
        if not force_refresh:
            cached = self.storage.get_summary(document_id, summary_type="document")
            if cached is not None:
                return cached

        doc, content_units = self._fetch_document_content(document_id)
        if not doc:
            return SummaryResponse(
                document_id=document_id,
                title="",
                summary_type="document",
                language="en",
                algorithm="textrank_mmr",
                summary_text="Dokumen tidak ditemukan dalam basis data.",
                status="not_found",
                error_message=f"Document {document_id} not found in database.",
            )

        title = doc.get("title") or "Dokumen Akademik"

        # Check if text is present
        if not content_units:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return SummaryResponse(
                document_id=document_id,
                title=title,
                summary_type="document",
                language=doc.get("language") or "en",
                algorithm="textrank_mmr",
                summary_text="Dokumen tidak memiliki teks yang cukup untuk diringkas (mungkin berupa pindaian/scan tanpa OCR).",
                sentence_count=0,
                processing_time_ms=elapsed_ms,
                status="insufficient_text",
            )

        # Detect language
        sample_text = (doc.get("abstract") or "") + " " + " ".join(u["text"][:1000] for u in content_units[:3])
        language, _ = detect_document_language(sample_text, default_lang=doc.get("language"))

        # Extract candidate sentences with page numbers
        candidates = extract_candidate_sentences(content_units, max_sentences=120)

        if len(candidates) < 2:
            # If text is too short, return available candidate or abstract
            fallback_text = candidates[0].text if candidates else (doc.get("abstract") or title)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return SummaryResponse(
                document_id=document_id,
                title=title,
                summary_type="document",
                language=language,
                algorithm="textrank_mmr",
                summary_text=fallback_text,
                key_sentences=[SentenceItem(text=fallback_text, page=1, score=1.0, order_idx=0)],
                source_pages=[1],
                sentence_count=1,
                processing_time_ms=elapsed_ms,
                status="insufficient_text",
            )

        # Run TextRank Graph Solver
        scored_sentences, tfidf_matrix = compute_textrank_scores(
            candidates=candidates,
            language=language,
        )

        # Run MMR Redundancy Filter
        selected_sentences = apply_mmr_selection(
            scored_sentences=scored_sentences,
            sentence_vectors=tfidf_matrix,
            top_k=max_sentences,
            lambda_param=lambda_param,
            chronological_order=True,
        )

        # Format narrative summary text
        summary_text = " ".join(s.text for s in selected_sentences)
        source_pages = sorted(list(set(s.page for s in selected_sentences if s.page is not None)))
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        result = SummaryResponse(
            document_id=document_id,
            title=title,
            summary_type="document",
            query_text=None,
            language=language,
            algorithm="textrank_mmr",
            summary_text=summary_text,
            key_sentences=selected_sentences,
            source_pages=source_pages,
            sentence_count=len(selected_sentences),
            processing_time_ms=elapsed_ms,
            cached=False,
            status="success",
        )

        # Cache result
        self.storage.save_summary(result)
        return result

    def summarize_query_focused(
        self,
        document_id: str,
        query: str,
        max_sentences: int = 4,
        lambda_param: float = 0.70,
        force_refresh: bool = False,
    ) -> SummaryResponse:
        """
        Generate query-focused cross-lingual evidence summary matching the user's specific query.
        Pipeline: Page Text -> Multilingual Embeddings -> Query Similarity -> MMR.
        """
        start_time = time.perf_counter()
        clean_q = (query or "").strip()
        if not clean_q:
            return self.summarize_document(document_id, max_sentences=max_sentences, force_refresh=force_refresh)

        # Check Cache
        if not force_refresh:
            cached = self.storage.get_summary(document_id, summary_type="query_focused", query_text=clean_q)
            if cached is not None:
                return cached

        doc, content_units = self._fetch_document_content(document_id)
        if not doc:
            return SummaryResponse(
                document_id=document_id,
                title="",
                summary_type="query_focused",
                query_text=clean_q,
                language="en",
                algorithm="multilingual_embedding_mmr",
                summary_text="Dokumen tidak ditemukan dalam basis data.",
                status="not_found",
            )

        title = doc.get("title") or "Dokumen Akademik"

        if not content_units:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return SummaryResponse(
                document_id=document_id,
                title=title,
                summary_type="query_focused",
                query_text=clean_q,
                language=doc.get("language") or "en",
                algorithm="multilingual_embedding_mmr",
                summary_text="Dokumen tidak memiliki teks yang cukup untuk diekstraksi.",
                sentence_count=0,
                processing_time_ms=elapsed_ms,
                status="insufficient_text",
            )

        sample_text = (doc.get("abstract") or "") + " " + " ".join(u["text"][:1000] for u in content_units[:3])
        language, _ = detect_document_language(sample_text, default_lang=doc.get("language"))

        candidates = extract_candidate_sentences(content_units, max_sentences=120)
        if not candidates:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return SummaryResponse(
                document_id=document_id,
                title=title,
                summary_type="query_focused",
                query_text=clean_q,
                language=language,
                algorithm="multilingual_embedding_mmr",
                summary_text="Tidak ditemukan kalimat substantif dalam dokumen ini.",
                sentence_count=0,
                processing_time_ms=elapsed_ms,
                status="insufficient_text",
            )

        # Compute query-to-sentence semantic similarity
        candidate_texts = [c.text for c in candidates]
        similarity_scores, sentence_vecs = self.embedder.compute_query_similarity(clean_q, candidate_texts)

        max_sim = float(similarity_scores.max()) if len(similarity_scores) > 0 else 0.0
        # If no relevant content matches the query
        if max_sim < 0.10:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            msg = "Dokumen ini tidak memuat pembahasan spesifik yang cukup untuk menjawab kueri Anda."
            return SummaryResponse(
                document_id=document_id,
                title=title,
                summary_type="query_focused",
                query_text=clean_q,
                language=language,
                algorithm="multilingual_embedding_mmr",
                summary_text=msg,
                key_sentences=[],
                source_pages=[],
                sentence_count=0,
                processing_time_ms=elapsed_ms,
                status="success",
            )

        # Build scored sentences
        scored_candidates = [
            ScoredSentence(candidates[i], score=similarity_scores[i], vector_idx=i)
            for i in range(len(candidates))
        ]
        scored_candidates.sort(key=lambda s: s.score, reverse=True)

        # Apply MMR selection
        selected_sentences = apply_mmr_selection(
            scored_sentences=scored_candidates,
            sentence_vectors=sentence_vecs,
            top_k=max_sentences,
            lambda_param=lambda_param,
            chronological_order=True,
        )

        summary_text = " ".join(s.text for s in selected_sentences)
        source_pages = sorted(list(set(s.page for s in selected_sentences if s.page is not None)))
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        result = SummaryResponse(
            document_id=document_id,
            title=title,
            summary_type="query_focused",
            query_text=clean_q,
            language=language,
            algorithm="multilingual_embedding_mmr",
            summary_text=summary_text,
            key_sentences=selected_sentences,
            source_pages=source_pages,
            sentence_count=len(selected_sentences),
            processing_time_ms=elapsed_ms,
            cached=False,
            status="success",
        )

        self.storage.save_summary(result)
        return result


_service_instance: Optional[SummarizationService] = None


def get_summarization_service(db: Optional[Database] = None) -> SummarizationService:
    global _service_instance
    if _service_instance is None:
        if db is None:
            from ..database.models import Database
            db = Database()
        _service_instance = SummarizationService(db)
    return _service_instance
