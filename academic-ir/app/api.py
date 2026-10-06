"""
Academic IR System — FastAPI REST API
======================================
Exposes the existing SearchEngine, Database, and TFIDFIndex via HTTP.

Endpoints:
  GET  /api/health          — health check + index stats
  GET  /api/search          — search documents
  GET  /api/documents/{id}  — get document detail
  GET  /api/stats           — corpus statistics
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── Path setup ────────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.indexing.tfidf import TFIDFIndex
from src.preprocessing.pipeline import PreprocessingPipeline
from src.retrieval.search import SearchEngine
from src.retrieval.ranking import rank_results
from src.retrieval.snippet import generate_snippet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Academic IR API",
    description="Academic Information Retrieval REST API",
    version="1.0.0",
)

# Allow Next.js dev server (localhost:3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Startup: load DB + index ──────────────────────────────────────────────────
DB_PATH = PROJECT_ROOT / "database" / "academic_ir.db"
INDEX_DIR = PROJECT_ROOT / "models"

db: Optional[Database] = None
search_engine: Optional[SearchEngine] = None
index_loaded = False


@app.on_event("startup")
async def startup():
    global db, search_engine, index_loaded
    try:
        logger.info(f"Loading database from {DB_PATH}")
        db = Database(str(DB_PATH))

        logger.info(f"Loading TF-IDF index from {INDEX_DIR}")
        pipeline = PreprocessingPipeline()
        tfidf = TFIDFIndex()
        tfidf.load(str(INDEX_DIR))

        search_engine = SearchEngine(tfidf_index=tfidf, db=db, preprocessing_pipeline=pipeline)
        index_loaded = True
        logger.info(f"Search engine ready. Index has {tfidf.tfidf_matrix.shape[0]} chunks.")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        index_loaded = False


# ─── Response models ───────────────────────────────────────────────────────────
class SearchResultItem(BaseModel):
    id: str
    document_id: str
    document_type: str
    title: str
    authors: list[str]
    year: Optional[int]
    source: str
    institution: Optional[str]
    course: Optional[str]
    language: Optional[str]
    relevance_score: float
    rank: int
    snippet: str
    page: Optional[int]
    source_url: Optional[str]
    doi: Optional[str]
    keywords: list[str]
    # Document aggregation info
    best_page_start: Optional[int]
    best_page_end: Optional[int]
    chunk_count: Optional[int]
    aggregation_strategy: Optional[str]


class SearchResponse(BaseModel):
    query: str
    retrieval_mode: str
    aggregation_strategy: str
    total: int
    results: list[SearchResultItem]


class HealthResponse(BaseModel):
    status: str
    index_loaded: bool
    message: str


# ─── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse)
def health():
    if index_loaded:
        n_chunks = search_engine.index.tfidf_matrix.shape[0]
        return HealthResponse(
            status="ok",
            index_loaded=True,
            message=f"Index loaded with {n_chunks} chunks.",
        )
    return HealthResponse(
        status="degraded",
        index_loaded=False,
        message="Index not loaded. Check server logs.",
    )


@app.get("/api/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(10, ge=1, le=50),
    document_type: Optional[str] = Query(None, description="MATERIAL | RESEARCH | THESIS"),
    language: Optional[str] = Query(None, description="en | id"),
    source: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    course: Optional[str] = Query(None),
    retrieval_mode: str = Query("tfidf", description="tfidf | bm25"),
    aggregation_strategy: str = Query("max+2nd", description="max | max+2nd | topN_avg"),
    candidate_k: int = Query(500, ge=20, le=5000, description="Candidate pool size before filtering"),
):
    if not index_loaded or search_engine is None:
        raise HTTPException(status_code=503, detail="Search index not loaded. Try again later.")

    # BM25 mode: attempt to use BM25 retriever if available
    if retrieval_mode == "bm25":
        from .bm25_loader import get_bm25_retriever
        bm25 = get_bm25_retriever()
        if bm25 is not None:
            raw_results = bm25.search(
                query=q,
                top_k=top_k,
                document_type=document_type,
                language=language,
                source=source,
                year_from=year_from,
                year_to=year_to,
                course=course,
                aggregation_strategy=aggregation_strategy,
                candidate_k=candidate_k,
            )
        else:
            logger.warning("BM25 retriever not available, falling back to TF-IDF.")
            retrieval_mode = "tfidf"

    if retrieval_mode == "tfidf":
        raw_results = search_engine.search(
            query=q,
            top_k=top_k,
            language=language,
            document_type=document_type,
            source=source,
            year_from=year_from,
            year_to=year_to,
            course=course,
            aggregation_strategy=aggregation_strategy,
            candidate_k=candidate_k,
        )

    items = []
    for r in raw_results:
        # Parse authors from JSON string if needed
        authors_raw = r.get("title", "")  # placeholder
        try:
            doc_authors = json.loads(r.get("authors", "[]")) if r.get("authors") else []
        except (json.JSONDecodeError, TypeError):
            doc_authors = [r.get("authors", "")] if r.get("authors") else []

        # Parse keywords
        try:
            kws_raw = r.get("keywords", "[]")
            keywords = json.loads(kws_raw) if kws_raw else []
        except (json.JSONDecodeError, TypeError):
            keywords = []

        items.append(SearchResultItem(
            id=str(r.get("best_chunk_id") or r.get("chunk_id", "")),
            document_id=str(r["document_id"]),
            document_type=r.get("document_type", "RESEARCH"),
            title=r.get("title") or "Untitled",
            authors=doc_authors,
            year=r.get("year"),
            source=r.get("source") or "Unknown",
            institution=r.get("institution"),
            course=r.get("course"),
            language=r.get("language"),
            relevance_score=round(r.get("document_score", r.get("score", 0.0)), 6),
            rank=r["rank"],
            snippet=r.get("snippet", ""),
            page=r.get("best_page_start", r.get("page")),
            source_url=r.get("source_url"),
            doi=r.get("doi"),
            keywords=keywords,
            best_page_start=r.get("best_page_start"),
            best_page_end=r.get("best_page_end"),
            chunk_count=r.get("chunk_count"),
            aggregation_strategy=r.get("aggregation_strategy"),
        ))

    return SearchResponse(
        query=q,
        retrieval_mode=retrieval_mode,
        aggregation_strategy=aggregation_strategy,
        total=len(items),
        results=items
    )


@app.get("/api/stats")
def stats():
    if not db:
        raise HTTPException(status_code=503, detail="Database not loaded.")
    conn = db.get_connection()
    try:
        total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        by_type = conn.execute(
            "SELECT document_type, COUNT(*) as cnt FROM documents GROUP BY document_type"
        ).fetchall()
        by_source = conn.execute(
            "SELECT source, COUNT(*) as cnt FROM documents GROUP BY source"
        ).fetchall()
        total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "by_type": {row[0]: row[1] for row in by_type},
            "by_source": {row[0]: row[1] for row in by_source},
        }
    finally:
        conn.close()

@app.get("/api/provenance")
def provenance():
    """Return corpus provenance metadata (sources, access types, licenses)."""
    import json as _json
    from pathlib import Path
    provenance_path = PROJECT_ROOT / "data" / "provenance" / "corpus_sources.json"
    if provenance_path.exists():
        with open(provenance_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    return {
        "note": "Provenance file not found. Run: create data/provenance/corpus_sources.json",
        "project_context": "Benchmark corpus for OASE-like academic IR prototype",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
