#!/usr/bin/env python3
"""
Academic IR System — CORE Research Paper Harvester Script
===========================================================
Collects open access research papers via CORE API v3.

Usage:
    python scripts/collect_core.py [--limit N] [--query "topic"] [--api-key KEY]
"""

import sys
import os
import json
import yaml
import argparse
import logging
from pathlib import Path

# Ensure academic-ir root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from src.database.models import Database
from src.collectors.core_api import CORECollector
from src.validation.corpus import validate_corpus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("collect_core")


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
    parser = argparse.ArgumentParser(description="Collect research papers from CORE API.")
    parser.add_argument("--limit", type=int, default=50, help="Number of papers to collect")
    parser.add_argument("--query", type=str, default=None, help="Search query (e.g. 'information retrieval')")
    parser.add_argument("--api-key", type=str, default=None, help="CORE API v3 Key")
    parser.add_argument("--manifest", type=str, default="data/manifests/research.jsonl")

    args = parser.parse_args()

    config_file = PROJECT_ROOT / "config" / "sources.yaml"
    config_data = load_config(config_file)
    core_config = config_data.get("sources", {}).get("core", {})
    db_path = config_data.get("collection", {}).get("db_path", "database/academic_ir.db")

    full_db_path = PROJECT_ROOT / db_path
    db = Database(str(full_db_path))
    db.initialize()

    collector = CORECollector(
        config=core_config,
        output_dir=str(PROJECT_ROOT / "data"),
        db=db,
        api_key=args.api_key,
    )

    if not collector.is_configured():
        print("\n" + "!" * 60)
        print("  WARNING: CORE_API_KEY IS NOT SET")
        print("!" * 60)
        print("To collect live research papers from CORE:")
        print("1. Get a free API key at: https://core.ac.uk/services/api")
        print("2. Add to academic-ir/.env: CORE_API_KEY=your_key_here")
        print("3. Or pass via command line: --api-key your_key_here")
        print("!" * 60 + "\n")
        sys.exit(1)

    logger.info(f"Starting CORE collection (limit={args.limit})...")
    collector.collect(limit=args.limit)

    manifest_file = PROJECT_ROOT / args.manifest
    count = generate_manifest(db, manifest_file)

    val_summary = validate_corpus(db)
    print("\n" + "=" * 60)
    print("  SPRINT 3: CORE RESEARCH CORPUS COLLECTION SUMMARY")
    print("=" * 60)
    print(f"Total Research in DB:       {len(db.get_documents_by_type('RESEARCH'))}")
    print(f"Total Documents in DB:      {val_summary['total']}")
    print(f"Manifest Generated:         {manifest_file} ({count} entries)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
