#!/usr/bin/env python3
"""
Academic IR System — DOAJ Research Harvester Script
====================================================
Collects open access research articles from DOAJ via its public search API.

Usage:
    python scripts/collect_doaj.py [--limit N] [--query "topic"]
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
from src.collectors.doaj import DOAJCollector
from src.validation.corpus import validate_corpus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("collect_doaj")


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def generate_manifest(db: Database, manifest_path: Path) -> int:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    docs = db.get_documents_by_type("RESEARCH")
    with open(manifest_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Collect research articles from DOAJ.")
    parser.add_argument("--limit", type=int, default=30, help="Maximum articles to collect")
    parser.add_argument("--query", type=str, default=None, help="Custom query topic")
    parser.add_argument("--manifest", type=str, default="data/manifests/research.jsonl")

    args = parser.parse_args()

    config_file = PROJECT_ROOT / "config" / "sources.yaml"
    config_data = load_config(config_file)
    doaj_config = config_data.get("sources", {}).get("doaj", {})
    db_path = config_data.get("collection", {}).get("db_path", "database/academic_ir.db")

    full_db_path = PROJECT_ROOT / db_path
    db = Database(str(full_db_path))
    db.initialize()

    collector = DOAJCollector(
        config=doaj_config,
        output_dir=str(PROJECT_ROOT / "data"),
        db=db,
    )

    logger.info(f"Starting DOAJ article collection (target limit={args.limit})...")
    collector.collect(limit=args.limit)

    manifest_file = PROJECT_ROOT / args.manifest
    count = generate_manifest(db, manifest_file)

    val_summary = validate_corpus(db)
    print("\n" + "=" * 60)
    print("  SPRINT 4: DOAJ RESEARCH ARTICLE HARVEST SUMMARY")
    print("=" * 60)
    print(f"Total Research in DB:       {len(db.get_documents_by_type('RESEARCH'))}")
    print(f"Total Documents in DB:      {val_summary['total']}")
    print(f"Manifest Generated:         {manifest_file} ({count} entries)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
