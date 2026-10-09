"""
Academic IR System — Summarization Cache Storage
================================================
SQLite persistence adapter for generated summaries in the document_summaries table.
"""

import json
import logging
from typing import Optional
from ..database.models import Database
from .schemas import SummaryResponse, SentenceItem

logger = logging.getLogger(__name__)


class SummaryStorage:
    """Manages SQLite read/write operations for summarization caching."""

    def __init__(self, db: Database):
        self.db = db

    def get_summary(
        self,
        document_id: str,
        summary_type: str = "document",
        query_text: Optional[str] = None,
    ) -> Optional[SummaryResponse]:
        """
        Retrieve a cached summary from SQLite.

        Args:
            document_id: Target document ID.
            summary_type: 'document' or 'query_focused'.
            query_text: Query string if summary_type is 'query_focused', else None.

        Returns:
            SummaryResponse or None if cache miss.
        """
        conn = self.db.get_connection()
        try:
            if summary_type == "document":
                cursor = conn.execute(
                    """
                    SELECT ds.*, d.title
                    FROM document_summaries ds
                    LEFT JOIN documents d ON ds.document_id = d.document_id
                    WHERE ds.document_id = ? AND ds.summary_type = 'document'
                    ORDER BY ds.id DESC LIMIT 1
                    """,
                    (document_id,),
                )
            else:
                norm_q = (query_text or "").strip().lower()
                cursor = conn.execute(
                    """
                    SELECT ds.*, d.title
                    FROM document_summaries ds
                    LEFT JOIN documents d ON ds.document_id = d.document_id
                    WHERE ds.document_id = ? AND ds.summary_type = 'query_focused' AND LOWER(ds.query_text) = ?
                    ORDER BY ds.id DESC LIMIT 1
                    """,
                    (document_id, norm_q),
                )

            row = cursor.fetchone()
            if not row:
                return None

            # Parse JSON fields
            try:
                sentences_data = json.loads(row["key_sentences_json"])
                key_sentences = [
                    SentenceItem(
                        text=s.get("text", ""),
                        page=s.get("page"),
                        score=s.get("score", 0.0),
                        order_idx=s.get("order_idx", idx),
                    )
                    for idx, s in enumerate(sentences_data)
                ]
            except Exception:
                key_sentences = []

            try:
                source_pages = json.loads(row["source_pages_json"])
            except Exception:
                source_pages = []

            return SummaryResponse(
                document_id=row["document_id"],
                title=row["title"] or "",
                summary_type=row["summary_type"],
                query_text=row["query_text"],
                language=row["language"],
                algorithm=row["algorithm"],
                summary_text=row["summary_text"],
                key_sentences=key_sentences,
                source_pages=source_pages,
                sentence_count=row["sentence_count"],
                processing_time_ms=row["processing_time_ms"],
                cached=True,
                status="success",
            )
        except Exception as exc:
            logger.error(f"Error reading summary cache for doc {document_id}: {exc}")
            return None
        finally:
            conn.close()

    def save_summary(self, summary: SummaryResponse) -> bool:
        """
        Save a freshly generated summary into the SQLite cache.
        Uses INSERT OR REPLACE to respect UNIQUE(document_id, summary_type, query_text).
        """
        conn = self.db.get_connection()
        try:
            sentences_json = json.dumps([
                {
                    "text": s.text,
                    "page": s.page,
                    "score": s.score,
                    "order_idx": s.order_idx,
                }
                for s in summary.key_sentences
            ], ensure_ascii=False)

            source_pages_json = json.dumps(summary.source_pages)
            norm_q = (summary.query_text.strip().lower() if summary.query_text else None)

            conn.execute(
                """
                INSERT OR REPLACE INTO document_summaries (
                    document_id,
                    summary_type,
                    query_text,
                    summary_text,
                    language,
                    algorithm,
                    key_sentences_json,
                    source_pages_json,
                    sentence_count,
                    processing_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.document_id,
                    summary.summary_type,
                    norm_q,
                    summary.summary_text,
                    summary.language,
                    summary.algorithm,
                    sentences_json,
                    source_pages_json,
                    summary.sentence_count,
                    summary.processing_time_ms,
                ),
            )
            conn.commit()
            return True
        except Exception as exc:
            logger.error(f"Error saving summary cache for doc {summary.document_id}: {exc}")
            return False
        finally:
            conn.close()
