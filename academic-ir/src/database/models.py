"""
Academic IR System — SQLite Database Models
=============================================
Unified schema supporting Material, Research, and Thesis corpora
with page-level and chunk-level retrieval units.
"""

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Schema Definition ──────────────────────────────────────────────────────

SCHEMA_SQL = """
-- =================================================================
-- Core documents table (unified schema for all corpus types)
-- =================================================================
CREATE TABLE IF NOT EXISTS documents (
    document_id         TEXT PRIMARY KEY,
    document_type       TEXT NOT NULL CHECK(document_type IN ('MATERIAL', 'RESEARCH', 'THESIS')),
    title               TEXT,
    abstract            TEXT,
    authors             TEXT,          -- JSON array: ["Author A", "Author B"]
    institution         TEXT,
    department          TEXT,
    course              TEXT,
    year                INTEGER,
    language            TEXT,
    language_confidence REAL,
    keywords            TEXT,          -- JSON array: ["keyword1", "keyword2"]
    source              TEXT,          -- OCW_UI, CORE, DOAJ, REPOSITORY
    source_url          TEXT,
    fulltext_url        TEXT,
    local_path          TEXT,
    file_type           TEXT DEFAULT 'pdf',
    file_size           INTEGER,
    page_count          INTEGER,
    license             TEXT,
    sha256              TEXT UNIQUE,
    doi                 TEXT,
    extraction_method   TEXT,          -- pymupdf, ocr, pymupdf+ocr
    extraction_status   TEXT CHECK(extraction_status IN ('SUCCESS', 'PARTIAL', 'FAILED', 'OCR_REQUIRED', NULL)),
    collection_status   TEXT CHECK(collection_status IN ('DOWNLOADED', 'VALIDATED', 'EXTRACTED', 'NORMALIZED', 'DEDUPLICATED', 'READY_FOR_INDEXING', NULL)),
    collected_at        TEXT
);

-- =================================================================
-- Page-level text storage
-- Each page of a PDF is stored separately for page-level retrieval
-- =================================================================
CREATE TABLE IF NOT EXISTS pages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     TEXT NOT NULL,
    page_number     INTEGER NOT NULL,
    raw_text        TEXT,
    clean_text      TEXT,
    word_count      INTEGER DEFAULT 0,
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE(document_id, page_number)
);

-- =================================================================
-- Chunk-level retrieval units
-- Chunks are the actual units indexed by TF-IDF
-- =================================================================
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        TEXT PRIMARY KEY,
    document_id     TEXT NOT NULL,
    page_start      INTEGER,
    page_end        INTEGER,
    chunk_index     INTEGER NOT NULL,
    raw_text        TEXT,
    clean_text      TEXT,
    word_count      INTEGER DEFAULT 0,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

-- =================================================================
-- Ingestion / processing logs for traceability
-- =================================================================
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     TEXT,
    stage           TEXT NOT NULL,    -- DISCOVER, DOWNLOAD, VALIDATE, EXTRACT, PREPROCESS, CHUNK, INDEX
    status          TEXT NOT NULL,    -- SUCCESS, FAILED, SKIPPED, WARNING
    message         TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

-- =================================================================
-- Text summarization cache (extractive & query-focused)
-- =================================================================
CREATE TABLE IF NOT EXISTS document_summaries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id         TEXT NOT NULL,
    summary_type        TEXT NOT NULL,        -- 'document' or 'query_focused'
    query_text          TEXT,                 -- NULL if summary_type = 'document'
    summary_text        TEXT NOT NULL,
    language            TEXT NOT NULL,        -- 'id', 'en', 'mixed'
    algorithm           TEXT NOT NULL,        -- 'textrank_mmr' or 'multilingual_embedding_mmr'
    key_sentences_json  TEXT NOT NULL,        -- JSON array: [{text, page, score}]
    source_pages_json   TEXT NOT NULL,        -- JSON array: [1, 3, 5]
    sentence_count      INTEGER NOT NULL,
    processing_time_ms  REAL NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE(document_id, summary_type, query_text)
);

-- =================================================================
-- Indexes for common queries
-- =================================================================
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_language ON documents(language);
CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256);
CREATE INDEX IF NOT EXISTS idx_documents_collection_status ON documents(collection_status);
CREATE INDEX IF NOT EXISTS idx_pages_document_id ON pages(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_document_id ON ingestion_logs(document_id);
CREATE INDEX IF NOT EXISTS idx_summaries_doc ON document_summaries(document_id, summary_type);
"""


class Database:
    """SQLite database manager for the Academic IR System."""

    def __init__(self, db_path: str = "database/academic_ir.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self):
        """Create all tables and indexes."""
        conn = self.get_connection()
        try:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        finally:
            conn.close()

    # ─── Document CRUD ───────────────────────────────────────────────────

    def insert_document(self, doc: dict, conn: sqlite3.Connection = None):
        """Insert a document record. Pass an existing connection for batch operations."""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection()

        try:
            conn.execute("""
                INSERT OR IGNORE INTO documents (
                    document_id, document_type, title, abstract, authors,
                    institution, department, course, year, language,
                    language_confidence, keywords, source, source_url, fulltext_url,
                    local_path, file_type, file_size, page_count, license,
                    sha256, doi, extraction_method, extraction_status,
                    collection_status, collected_at
                ) VALUES (
                    :document_id, :document_type, :title, :abstract, :authors,
                    :institution, :department, :course, :year, :language,
                    :language_confidence, :keywords, :source, :source_url, :fulltext_url,
                    :local_path, :file_type, :file_size, :page_count, :license,
                    :sha256, :doi, :extraction_method, :extraction_status,
                    :collection_status, :collected_at
                )
            """, doc)
            if should_close:
                conn.commit()
        finally:
            if should_close:
                conn.close()

    def update_document_status(self, document_id: str, status: str, conn: sqlite3.Connection = None):
        """Update collection_status of a document."""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection()
        try:
            conn.execute(
                "UPDATE documents SET collection_status = ? WHERE document_id = ?",
                (status, document_id)
            )
            if should_close:
                conn.commit()
        finally:
            if should_close:
                conn.close()

    def get_document(self, document_id: str) -> dict:
        """Get a single document by ID."""
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_documents_by_type(self, document_type: str) -> list:
        """Get all documents of a given type."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM documents WHERE document_type = ?", (document_type,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_documents(self) -> list:
        """Get all documents."""
        conn = self.get_connection()
        try:
            rows = conn.execute("SELECT * FROM documents").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def check_duplicate(self, sha256: str, conn: sqlite3.Connection = None) -> bool:
        """Check if a file with the same hash already exists."""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT document_id FROM documents WHERE sha256 = ?", (sha256,)
            ).fetchone()
            return row is not None
        finally:
            if should_close:
                conn.close()

    def get_next_id(self, prefix: str, conn: sqlite3.Connection = None) -> str:
        """Generate the next sequential document ID (e.g., MAT-000001)."""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT document_id FROM documents WHERE document_id LIKE ? ORDER BY document_id DESC LIMIT 1",
                (f"{prefix}-%",)
            ).fetchone()
            if row and row['document_id']:
                try:
                    last_num = int(row['document_id'].split('-')[1])
                    next_num = last_num + 1
                except (IndexError, ValueError):
                    next_num = 1
            else:
                next_num = 1
            return f"{prefix}-{next_num:06d}"
        finally:
            if should_close:
                conn.close()

    # ─── Page CRUD ───────────────────────────────────────────────────────

    def insert_page(self, document_id: str, page_number: int,
                    raw_text: str, clean_text: str = None,
                    word_count: int = 0, conn: sqlite3.Connection = None):
        """Insert a page text record."""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO pages (document_id, page_number, raw_text, clean_text, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, page_number, raw_text, clean_text, word_count))
            if should_close:
                conn.commit()
        finally:
            if should_close:
                conn.close()

    def get_pages(self, document_id: str) -> list:
        """Get all pages for a document, ordered by page number."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM pages WHERE document_id = ? ORDER BY page_number",
                (document_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ─── Chunk CRUD ──────────────────────────────────────────────────────

    def insert_chunk(self, chunk: dict, conn: sqlite3.Connection = None):
        """Insert a chunk record."""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO chunks (
                    chunk_id, document_id, page_start, page_end,
                    chunk_index, raw_text, clean_text, word_count
                ) VALUES (
                    :chunk_id, :document_id, :page_start, :page_end,
                    :chunk_index, :raw_text, :clean_text, :word_count
                )
            """, chunk)
            if should_close:
                conn.commit()
        finally:
            if should_close:
                conn.close()

    def get_chunks(self, document_id: str) -> list:
        """Get all chunks for a document, ordered by chunk index."""
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
                (document_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_indexed_chunks(self) -> list:
        """Get all chunks that have clean_text (ready for TF-IDF)."""
        conn = self.get_connection()
        try:
            rows = conn.execute("""
                SELECT c.chunk_id, c.document_id, c.page_start, c.page_end,
                       c.chunk_index, c.clean_text, c.word_count,
                       d.document_type, d.title, d.language
                FROM chunks c
                JOIN documents d ON c.document_id = d.document_id
                WHERE c.clean_text IS NOT NULL AND c.clean_text != ''
                  AND d.collection_status = 'READY_FOR_INDEXING'
                ORDER BY c.chunk_id
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ─── Logging ─────────────────────────────────────────────────────────

    def log(self, document_id: str, stage: str, status: str,
            message: str = "", conn: sqlite3.Connection = None):
        """Insert an ingestion log entry."""
        should_close = conn is None
        if conn is None:
            conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO ingestion_logs (document_id, stage, status, message)
                VALUES (?, ?, ?, ?)
            """, (document_id, stage, status, message))
            if should_close:
                conn.commit()
        finally:
            if should_close:
                conn.close()

    # ─── Statistics ──────────────────────────────────────────────────────

    def get_corpus_stats(self) -> dict:
        """Get corpus statistics for reporting."""
        conn = self.get_connection()
        try:
            stats = {}

            # Total documents
            row = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
            stats['total_documents'] = row['cnt']

            # By type
            rows = conn.execute(
                "SELECT document_type, COUNT(*) as cnt FROM documents GROUP BY document_type"
            ).fetchall()
            stats['by_type'] = {r['document_type']: r['cnt'] for r in rows}

            # By language
            rows = conn.execute(
                "SELECT language, COUNT(*) as cnt FROM documents GROUP BY language"
            ).fetchall()
            stats['by_language'] = {r['language']: r['cnt'] for r in rows}

            # By source
            rows = conn.execute(
                "SELECT source, COUNT(*) as cnt FROM documents GROUP BY source"
            ).fetchall()
            stats['by_source'] = {r['source']: r['cnt'] for r in rows}

            # By extraction status
            rows = conn.execute(
                "SELECT extraction_status, COUNT(*) as cnt FROM documents GROUP BY extraction_status"
            ).fetchall()
            stats['by_extraction'] = {r['extraction_status']: r['cnt'] for r in rows}

            # By collection status
            rows = conn.execute(
                "SELECT collection_status, COUNT(*) as cnt FROM documents GROUP BY collection_status"
            ).fetchall()
            stats['by_collection'] = {r['collection_status']: r['cnt'] for r in rows}

            # Total chunks
            row = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()
            stats['total_chunks'] = row['cnt']

            # Total pages
            row = conn.execute("SELECT COUNT(*) as cnt FROM pages").fetchone()
            stats['total_pages'] = row['cnt']

            # Duplicates
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE sha256 IN "
                "(SELECT sha256 FROM documents GROUP BY sha256 HAVING COUNT(*) > 1)"
            ).fetchone()
            stats['duplicates'] = row['cnt']

            return stats
        finally:
            conn.close()


# ─── Standalone initialization ───────────────────────────────────────────

def init_database(db_path: str = "database/academic_ir.db"):
    """Initialize the database (callable from scripts)."""
    db = Database(db_path)
    db.initialize()
    print(f"[OK] Database initialized at {db_path}")
    return db


if __name__ == "__main__":
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/academic_ir.db"
    init_database(db_path)
