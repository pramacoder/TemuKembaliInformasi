#!/usr/bin/env python3
"""
Academic IR System — BM25 Index Builder
=========================================
Builds and saves the BM25 index from all chunks in the SQLite database.

Usage:
    python scripts/build_bm25_index.py [--output-dir models/bm25_v1]

Output (saved to models/bm25_v1/):
    bm25_index.pkl  — serialized BM25Okapi object, chunk_ids, chunk_meta

Expert plan references: §6.2, §28 Phase 4
"""

import sys
import logging
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.retrieval.bm25 import BM25Retriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("build_bm25_index")


def main():
    parser = argparse.ArgumentParser(description="Build BM25 index from SQLite corpus.")
    parser.add_argument("--output-dir", default="models/bm25_v1",
                        help="Directory to save BM25 index (default: models/bm25_v1)")
    parser.add_argument("--k1", type=float, default=1.5,
                        help="BM25 k1 parameter (default: 1.5)")
    parser.add_argument("--b", type=float, default=0.75,
                        help="BM25 b parameter (default: 0.75)")
    parser.add_argument("--db", default="database/academic_ir.db",
                        help="Path to SQLite database")
    args = parser.parse_args()

    db_path = PROJECT_ROOT / args.db
    output_dir = PROJECT_ROOT / args.output_dir

    # Load all chunks from DB
    logger.info(f"Loading chunks from {db_path}...")
    db = Database(str(db_path))
    conn = db.get_connection()
    try:
        rows = conn.execute("""
            SELECT c.chunk_id, c.document_id, c.page_start, c.page_end,
                   c.chunk_index, c.raw_text, c.clean_text,
                   d.document_type, d.title, d.abstract, d.authors,
                   d.course, d.year, d.language, d.source,
                   d.source_url, d.local_path, d.institution,
                   d.keywords, d.doi
            FROM chunks c
            JOIN documents d ON c.document_id = d.document_id
            WHERE c.clean_text IS NOT NULL AND c.clean_text != ''
            ORDER BY c.chunk_id
        """).fetchall()
        chunks = [dict(row) for row in rows]
    finally:
        conn.close()

    logger.info(f"Loaded {len(chunks)} chunks.")

    # Build BM25 index
    retriever = BM25Retriever(k1=args.k1, b=args.b)
    stats = retriever.build_index(chunks)

    # Save index
    retriever.save(str(output_dir))

    print("\n" + "=" * 60)
    print("  BM25 INDEX BUILD COMPLETE")
    print("=" * 60)
    print(f"Total Chunks Indexed:  {stats['chunk_count']:,}")
    print(f"k1 Parameter:          {stats['k1']}")
    print(f"b Parameter:           {stats['b']}")
    print(f"Index Saved To:        {output_dir}")
    print("=" * 60)
    print("\nTo use BM25 retrieval:")
    print("  API: GET /api/search?q=<query>&retrieval_mode=bm25")
    print("=" * 60)


if __name__ == "__main__":
    main()
