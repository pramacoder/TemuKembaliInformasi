#!/usr/bin/env python3
"""
Academic IR System — Institutional Repository Thesis Harvester
==============================================================
Collects thesis and dissertation documents from institutional repositories
or local deposits.

Usage:
    python scripts/collect_repo.py [--local-dir PATH] [--limit N]
"""

import sys
import os
import json
import yaml
import argparse
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.collectors.repository import RepositoryCollector
from src.validation.corpus import validate_corpus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("collect_repo")


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def generate_manifest(db: Database, manifest_path: Path) -> int:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    docs = db.get_documents_by_type("THESIS")
    with open(manifest_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Collect thesis documents.")
    parser.add_argument("--local-dir", type=str, default=None, help="Local directory containing thesis PDFs")
    parser.add_argument("--endpoint", type=str, default=None, help="OAI-PMH repository endpoint")
    parser.add_argument("--limit", type=int, default=50, help="Maximum documents to collect")
    parser.add_argument("--manifest", type=str, default="data/manifests/thesis.jsonl")

    args = parser.parse_args()

    config_file = PROJECT_ROOT / "config" / "sources.yaml"
    config_data = load_config(config_file)
    repo_config = config_data.get("sources", {}).get("repositories", {})
    db_path = config_data.get("collection", {}).get("db_path", "database/academic_ir.db")

    full_db_path = PROJECT_ROOT / db_path
    db = Database(str(full_db_path))
    db.initialize()

    collector = RepositoryCollector(
        config=repo_config,
        output_dir=str(PROJECT_ROOT / "data"),
        db=db,
    )

    if args.local_dir:
        logger.info(f"Ingesting theses from local directory: {args.local_dir}")
        collector.ingest_local_theses(args.local_dir, limit=args.limit)
    else:
        logger.info(f"Harvesting theses from OAI endpoint...")
        collector.collect(limit=args.limit)

    manifest_file = PROJECT_ROOT / args.manifest
    count = generate_manifest(db, manifest_file)

    val_summary = validate_corpus(db)
    print("\n" + "=" * 60)
    print("  SPRINT 5: THESIS CORPUS COLLECTION SUMMARY")
    print("=" * 60)
    print(f"Total Theses in DB:         {len(db.get_documents_by_type('THESIS'))}")
    print(f"Total Documents in DB:      {val_summary['total']}")
    print(f"Manifest Generated:         {manifest_file} ({count} entries)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
