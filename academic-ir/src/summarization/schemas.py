"""
Academic IR System — Summarization Data Schemas
================================================
Pydantic schemas for text summarization requests, responses, and citations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SentenceItem(BaseModel):
    """A single sentence extracted for the summary with page citation."""
    text: str = Field(..., description="Sentence text")
    page: Optional[int] = Field(None, description="Original physical page number in source document")
    score: float = Field(..., description="Importance or relevance score")
    order_idx: int = Field(0, description="Appearance index in the document for chronological order")


class SummaryResponse(BaseModel):
    """Complete summarization output returned to the client and stored in cache."""
    document_id: str
    title: str = ""
    summary_type: str = "document"  # "document" or "query_focused"
    query_text: Optional[str] = None
    language: str = "en"           # "id", "en", "mixed"
    algorithm: str = "textrank_mmr"
    summary_text: str
    key_sentences: List[SentenceItem] = []
    source_pages: List[int] = []
    sentence_count: int = 0
    processing_time_ms: float = 0.0
    cached: bool = False
    status: str = "success"        # "success", "insufficient_text", "not_found", "error"
    error_message: Optional[str] = None


class QuerySummaryRequest(BaseModel):
    """Request payload for query-focused evidence summarization."""
    query: str = Field(..., min_length=2, description="User search query to focus the summary on")
    max_sentences: int = Field(4, ge=1, le=10, description="Target number of key sentences")
    lambda_param: float = Field(0.70, ge=0.0, le=1.0, description="MMR diversity trade-off (higher = more relevant, lower = more novel)")
