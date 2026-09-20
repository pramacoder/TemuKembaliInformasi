#!/usr/bin/env python3
"""
Academic IR System — OCW UI Collector & Ingestion Script
=========================================================
Imports OCW UI course materials into the Academic IR database,
extracts text, chunks content, runs language detection, and creates
the material manifest.

Usage:
    python scripts/collect_ocw.py [--limit N] [--scrape] [--dataset-dir PATH]
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

from src.database.models import Database
from src.collectors.ocw_ui import OCWUICollector
from src.validation.corpus import validate_corpus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("collect_ocw")


def load_config(config_path: Path) -> dict:
    """Load sources configuration YAML."""
    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def generate_manifest(db: Database, manifest_path: Path) -> int:
    """Export all MATERIAL documents to a JSONL manifest file."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    docs = db.get_documents_by_type("MATERIAL")
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            
    logger.info(f"Generated manifest with {len(docs)} records at {manifest_path}")
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Collect or migrate OCW UI materials.")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to existing dataset_ocw_ui folder (default: looks in parent or local dir)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process (for testing)"
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Perform live scraping from ocw.ui.ac.id instead of local dataset"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/manifests/material.jsonl",
        help="Manifest output path"
    )

    args = parser.parse_args()

    # Load configuration
    config_file = PROJECT_ROOT / "config" / "sources.yaml"
    config_data = load_config(config_file)
    ocw_config = config_data.get("sources", {}).get("ocw_ui", {})
    db_path = config_data.get("collection", {}).get("db_path", "database/academic_ir.db")

    # Resolve database path relative to project root
    full_db_path = PROJECT_ROOT / db_path
    db = Database(str(full_db_path))
    db.initialize()

    # Locate dataset directory if migrating
    if not args.scrape:
        candidate_dirs = [
            args.dataset_dir,
            PROJECT_ROOT.parent / "dataset_ocw_ui",
            PROJECT_ROOT / "dataset_ocw_ui",
        ]
        chosen_dir = None
        for cd in candidate_dirs:
            if cd and Path(cd).exists() and (Path(cd) / "all_metadata.json").exists():
                chosen_dir = Path(cd)
                break

        if not chosen_dir:
            logger.error(
                "Could not find dataset_ocw_ui directory with all_metadata.json. "
                "Specify with --dataset-dir or use --scrape for live scraping."
            )
            sys.exit(1)

        logger.info(f"Using local dataset directory: {chosen_dir}")

    # Initialize collector
    collector = OCWUICollector(
        config=ocw_config,
        output_dir=str(PROJECT_ROOT / "data"),
        db=db,
    )

    if args.scrape:
        logger.info("Starting live discovery and scraping from OCW UI...")
        collector.collect(limit=args.limit)
    else:
        logger.info(f"Starting ingestion from {chosen_dir}...")
        collector.migrate_from_existing(
            dataset_dir=str(chosen_dir),
            limit=args.limit,
            copy_files=True,
            batch_commit_size=20,
        )

    # Export manifest
    manifest_file = PROJECT_ROOT / args.manifest
    manifest_count = generate_manifest(db, manifest_file)

    # Validation
    logger.info("Running corpus validation...")
    val_summary = validate_corpus(db)

    print("\n" + "=" * 60)
    print("  SPRINT 2: OCW UI MATERIAL CORPUS INGESTION SUMMARY")
    print("=" * 60)
    print(f"Total Documents in DB:      {val_summary['total']}")
    print(f"Ready for Indexing:         {val_summary['ready']}")
    print(f"Not Ready / Issues:         {val_summary['not_ready']}")
    print(f"Manifest Generated:         {manifest_file} ({manifest_count} entries)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
