#!/usr/bin/env python3
"""
Academic IR System — Index Builder Script
==========================================
Extracts all clean chunks from the database across Material, Research,
and Thesis corpora, builds the TF-IDF Vector Space Model index, and
saves the serialized model artifacts.

Usage:
    python scripts/build_index.py [--output-dir models]
"""

import sys
import os
import json
import csv
import time
import yaml
import argparse
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.indexing.tfidf import TFIDFIndex

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("build_index")


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_unified_manifest(db: Database, output_csv: Path) -> int:
    """Export unified CSV manifest for all documents in DB."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    docs = db.get_all_documents()
    
    if not docs:
        return 0

    fieldnames = [
        "document_id", "document_type", "title", "authors", "course",
        "institution", "year", "language", "source", "page_count",
        "file_size", "collection_status", "local_path", "sha256"
    ]

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for d in docs:
            writer.writerow(d)

    logger.info(f"Unified manifest saved to {output_csv} ({len(docs)} documents)")
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Build TF-IDF search index.")
    parser.add_argument("--output-dir", type=str, default="models", help="Directory to save index artifacts")
    parser.add_argument("--min-df", type=int, default=None, help="Override min_df")
    parser.add_argument("--max-df", type=float, default=None, help="Override max_df")

    args = parser.parse_args()

    config_file = PROJECT_ROOT / "config" / "sources.yaml"
    config_data = load_config(config_file)
    tfidf_config = config_data.get("tfidf", {})
    db_path = config_data.get("collection", {}).get("db_path", "database/academic_ir.db")

    ngram_range = tuple(tfidf_config.get("ngram_range", [1, 2]))
    sublinear_tf = tfidf_config.get("sublinear_tf", True)
    min_df = args.min_df if args.min_df is not None else tfidf_config.get("min_df", 2)
    max_df = args.max_df if args.max_df is not None else tfidf_config.get("max_df", 0.95)

    full_db_path = PROJECT_ROOT / db_path
    db = Database(str(full_db_path))

    # 1. Export unified manifest
    manifest_csv = PROJECT_ROOT / "data" / "manifests" / "unified_manifest.csv"
    doc_count = build_unified_manifest(db, manifest_csv)

    # 2. Fetch all indexed chunks
    logger.info("Fetching all chunks with clean text from database...")
    chunks = db.get_all_indexed_chunks()
    logger.info(f"Loaded {len(chunks)} chunks ready for TF-IDF indexing.")

    if not chunks:
        logger.error("No chunks found with clean_text in database! Run collection/ingestion first.")
        sys.exit(1)

    # 3. Build TF-IDF index
    start_time = time.time()
    logger.info(f"Fitting TF-IDF index (ngram={ngram_range}, min_df={min_df}, max_df={max_df})...")

    index = TFIDFIndex(
        ngram_range=ngram_range,
        sublinear_tf=sublinear_tf,
        min_df=min_df,
        max_df=max_df,
    )
    fit_stats = index.fit(chunks)
    elapsed = time.time() - start_time

    # 4. Save index to disk
    models_dir = PROJECT_ROOT / args.output_dir
    models_dir.mkdir(parents=True, exist_ok=True)
    index.save(str(models_dir))

    print("\n" + "=" * 60)
    print("  SPRINT 6: TF-IDF VECTOR SPACE MODEL INDEX BUILT")
    print("=" * 60)
    print(f"Total Documents:            {doc_count}")
    print(f"Total Indexed Chunks:       {fit_stats['chunk_count']}")
    print(f"Vocabulary Size:            {fit_stats['vocab_size']:,} terms")
    print(f"Matrix Shape:               {fit_stats['matrix_shape']}")
    print(f"Density:                    {fit_stats['density']:.4%}")
    print(f"Time Elapsed:               {elapsed:.2f} seconds")
    print(f"Index Saved To:             {models_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
