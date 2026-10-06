#!/usr/bin/env python3
"""
Academic IR System — Large-Scale Multi-Corpus Harvester
=======================================================
Orchestrates high-volume harvesting of Research Papers (arXiv / DOAJ)
and Theses / Dissertations (Indonesian OAI-PMH Repositories), saves
everything into SQLite (database/academic_ir.db), and rebuilds
the TF-IDF Vector Space Model search index.

Usage:
    python scripts/harvest_large_corpus.py [--research N] [--thesis N]
"""

import sys
import os
import time
import argparse
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from scripts.collect_arxiv import ArxivCollector, generate_manifest as gen_res_manifest
from src.collectors.repository import RepositoryCollector
from scripts.collect_repo import generate_manifest as gen_ths_manifest
from scripts.build_index import build_unified_manifest, main as build_index_main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("harvest_large_corpus")


def get_db_stats(db: Database) -> dict:
    conn = db.get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT document_type, count(*) FROM documents GROUP BY document_type")
        docs = dict(c.fetchall())
        c.execute("SELECT count(*) FROM chunks")
        total_chunks = c.fetchone()[0]
        return {"documents": docs, "total_chunks": total_chunks}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Harvest high-volume academic corpus.")
    parser.add_argument("--research", type=int, default=50, help="Number of research papers to collect")
    parser.add_argument("--thesis", type=int, default=50, help="Number of thesis documents to collect")
    parser.add_argument("--rebuild-index", action="store_true", default=True, help="Rebuild TF-IDF index after collection")

    args = parser.parse_args()

    full_db_path = PROJECT_ROOT / "database" / "academic_ir.db"
    db = Database(str(full_db_path))
    db.initialize()

    initial_stats = get_db_stats(db)
    logger.info(f"Initial Corpus Status in SQLite: {initial_stats}")

    start_time = time.time()

    # 1. Harvest Research Papers from arXiv
    if args.research > 0:
        logger.info(f"=== Starting Research Paper Collection (target: {args.research}) ===")
        res_collector = ArxivCollector(
            config={"rate_limit_seconds": 1.5, "timeout": 45},
            output_dir=str(PROJECT_ROOT / "data"),
            db=db,
        )
        # Use multiple query themes for topic diversity
        queries = [
            "cat:cs.IR",
            "cat:cs.CL AND (ti:retrieval OR ti:search OR ti:ranking)",
            "all:\"vector space model\" OR all:\"tf-idf\" OR all:\"dense retrieval\"",
        ]
        collected_research = 0
        per_query = max(10, args.research // len(queries) + 1)
        for q in queries:
            if collected_research >= args.research:
                break
            needed = args.research - collected_research
            docs = res_collector.collect(limit=min(needed, per_query), query=q)
            collected_research += len(docs)
            logger.info(f"Harvested {len(docs)} papers for query: '{q}' (total research so far: {collected_research}/{args.research})")

        gen_res_manifest(db, PROJECT_ROOT / "data" / "manifests" / "research.jsonl")

    # 2. Harvest Theses from Indonesian OAI-PMH Repositories
    if args.thesis > 0:
        logger.info(f"=== Starting Indonesian Thesis Collection (target: {args.thesis}) ===")
        repo_collector = RepositoryCollector(
            config={
                "endpoints": [
                    "http://eprints.undip.ac.id/cgi/oai2",
                    "http://repository.uin-malang.ac.id/cgi/oai2",
                ],
                "set_spec": "74797065733D746865736973",
                "rate_limit_seconds": 1.5,
                "timeout": 45,
            },
            output_dir=str(PROJECT_ROOT / "data"),
            db=db,
        )
        theses = repo_collector.collect(limit=args.thesis)
        logger.info(f"Harvested {len(theses)} theses across institutional repositories.")
        gen_ths_manifest(db, PROJECT_ROOT / "data" / "manifests" / "thesis.jsonl")

    # 3. Export Unified CSV Manifest
    manifest_csv = PROJECT_ROOT / "data" / "manifests" / "unified_manifest.csv"
    build_unified_manifest(db, manifest_csv)

    # 4. Rebuild TF-IDF Index
    if args.rebuild_index:
        logger.info("=== Rebuilding TF-IDF Vector Space Model Index ===")
        # Call build_index script logic
        from src.indexing.tfidf import TFIDFIndex
        import yaml
        config_file = PROJECT_ROOT / "config" / "sources.yaml"
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        tfidf_cfg = cfg.get("tfidf", {})

        chunks = db.get_all_indexed_chunks()
        logger.info(f"Loaded {len(chunks)} chunks for TF-IDF training.")
        tfidf = TFIDFIndex(
            ngram_range=tuple(tfidf_cfg.get("ngram_range", [1, 2])),
            sublinear_tf=tfidf_cfg.get("sublinear_tf", True),
            min_df=tfidf_cfg.get("min_df", 2),
            max_df=tfidf_cfg.get("max_df", 0.95),
        )
        tfidf.fit(chunks)
        models_dir = PROJECT_ROOT / "models"
        tfidf.save(str(models_dir))
        logger.info(f"TF-IDF model artifacts successfully updated in {models_dir}")

    final_stats = get_db_stats(db)
    elapsed = round(time.time() - start_time, 1)

    print("\n" + "=" * 65)
    print("  BATCH HARVESTING & INDEXING COMPLETE")
    print("=" * 65)
    print(f"Elapsed Time:               {elapsed} seconds")
    print(f"Database:                   SQLite (database/academic_ir.db)")
    print(f"Documents Before:           {initial_stats['documents']}")
    print(f"Documents After:            {final_stats['documents']}")
    print(f"Total Chunks:               {initial_stats['total_chunks']} -> {final_stats['total_chunks']}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
