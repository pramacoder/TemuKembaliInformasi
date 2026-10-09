"""
Academic IR System — Text Summarization Module
==============================================
Language-aware, extractive & query-focused summarization for academic documents.
Supports:
- Document-level extractive summary via TextRank + TF-IDF + MMR
- Query-focused evidence summarization via Multilingual Embeddings + MMR
- Traceable source page attribution
- SQLite-backed result caching
"""

from .schemas import SentenceItem, SummaryResponse, QuerySummaryRequest
from .service import SummarizationService, get_summarization_service

__all__ = [
    "SentenceItem",
    "SummaryResponse",
    "QuerySummaryRequest",
    "SummarizationService",
    "get_summarization_service",
]
