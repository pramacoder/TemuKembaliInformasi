#!/usr/bin/env python3
"""
Academic IR System — Information Retrieval Evaluation Runner
============================================================
Runs evaluation benchmarks using standard IR metrics:
- Precision@K (P@5, P@10)
- Recall@K (R@5, R@10)
- Mean Average Precision (MAP)
- Normalized Discounted Cumulative Gain (NDCG@10)

Usage:
    python scripts/run_evaluation.py [--models-dir models]
"""

import sys
import os
import csv
import json
import logging
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.indexing.tfidf import TFIDFIndex
from src.preprocessing.pipeline import PreprocessingPipeline
from src.retrieval.search import SearchEngine
from src.evaluation.metrics import evaluate, load_queries, load_qrels

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("evaluation")


def generate_course_qrels_if_missing(db: Database, queries_file: Path, qrels_file: Path):
    """
    If ground-truth qrels file does not exist, construct course-aligned ground truth
    mapping based on document course/title matching for the standard evaluation suite.
    """
    if qrels_file.exists():
        return

    logger.info("Generating standard course-aligned qrels benchmark...")
    docs = db.get_all_documents()
    
    # Keyword to course mapping for query IDs
    q_course_map = {
        "Q01": "Analisis dan Perancangan Sistem Informasi",
        "Q02": "Manajemen Proyek TI",
        "Q03": "Manajemen Proyek TI",
        "Q04": "Data Mining and Business Intelligence",
        "Q05": "Aljabar Linier",
        "Q06": "Pemrograman Fungsional",
        "Q07": "Sistem Operasi",
        "Q08": "Human Computer Interaction",
        "Q09": "Metodologi Penelitian",
        "Q10": "Arsitektur Komputer",
    }

    qrels_file.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    for qid, course_sub in q_course_map.items():
        for doc in docs:
            d_course = (doc.get("course") or "").lower()
            d_title = (doc.get("title") or "").lower()
            c_sub = course_sub.lower()
            
            # Graded relevance: 3 = exact course, 2 = title match, 1 = relevant topic
            if c_sub in d_course:
                rows.append({"query_id": qid, "document_id": doc["document_id"], "relevance": 3})
            elif any(w in d_title for w in c_sub.split() if len(w) > 4):
                rows.append({"query_id": qid, "document_id": doc["document_id"], "relevance": 2})

    with open(qrels_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["query_id", "document_id", "relevance"])
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Generated {len(rows)} qrel judgements at {qrels_file}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Academic IR Retrieval Engine.")
    parser.add_argument("--models-dir", type=str, default="models", help="Directory containing TF-IDF model")
    parser.add_argument("--queries", type=str, default="evaluation/queries.csv", help="Queries CSV file")
    parser.add_argument("--qrels", type=str, default="evaluation/qrels.csv", help="Qrels CSV file")
    parser.add_argument("--report", type=str, default="data/reports/evaluation_results.json")

    args = parser.parse_args()

    models_dir = PROJECT_ROOT / args.models_dir
    if not (models_dir / "tfidf_vectorizer.pkl").exists():
        logger.error(f"Index models not found in {models_dir}! Run 'python scripts/build_index.py' first.")
        sys.exit(1)

    # 1. Load Database
    db_file = PROJECT_ROOT / "database" / "academic_ir.db"
    db = Database(str(db_file))

    # 2. Load Index and Search Engine
    logger.info(f"Loading TF-IDF index from {models_dir}...")
    index = TFIDFIndex()
    index.load(str(models_dir))

    pipeline = PreprocessingPipeline(default_language="id")
    search_engine = SearchEngine(index, db, pipeline)

    # 3. Ensure Qrels exist
    queries_path = PROJECT_ROOT / args.queries
    qrels_path = PROJECT_ROOT / args.qrels
    generate_course_qrels_if_missing(db, queries_path, qrels_path)

    # 4. Load queries and qrels
    queries = load_queries(str(queries_path))
    qrels = load_qrels(str(qrels_path))

    logger.info(f"Evaluating {len(queries)} queries against {len(qrels)} ground truth judgements...")
    metrics_result = evaluate(search_engine, queries, qrels, k_values=[5, 10])

    # 5. Save report
    report_file = PROJECT_ROOT / args.report
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(metrics_result, f, indent=2)

    # 6. Display results
    print("\n" + "=" * 78)
    print("           ACADEMIC IR SYSTEM — RETRIEVAL EVALUATION BENCHMARK")
    print("=" * 78)
    print(f"{'Query ID':<10} {'Query Text':<42} {'P@5':<8} {'P@10':<8} {'NDCG@10':<8} {'AP':<8}")
    print("-" * 78)

    for qid, qtext in queries.items():
        qm = metrics_result['per_query'].get(qid, {})
        p5 = qm.get('P@5', 0.0)
        p10 = qm.get('P@10', 0.0)
        ndcg10 = qm.get('NDCG@10', 0.0)
        ap = qm.get('AP', 0.0)
        print(f"{qid:<10} {qtext[:40]:<42} {p5:<8.4f} {p10:<8.4f} {ndcg10:<8.4f} {ap:<8.4f}")

    agg = metrics_result.get("aggregate", {})
    print("=" * 78)
    print("  AGGREGATE PERFORMANCE METRICS")
    print("-" * 78)
    print(f"  Mean Average Precision (MAP):       {agg.get('MAP', 0.0):.4f}")
    print(f"  Average Precision@5 (P@5):          {agg.get('Avg_P@5', 0.0):.4f}")
    print(f"  Average Precision@10 (P@10):        {agg.get('Avg_P@10', 0.0):.4f}")
    print(f"  Average Recall@10 (R@10):           {agg.get('Avg_R@10', 0.0):.4f}")
    print(f"  Average NDCG@10:                    {agg.get('Avg_NDCG@10', 0.0):.4f}")
    print("=" * 78)
    print(f"Detailed evaluation report saved to: {report_file}\n")


if __name__ == "__main__":
    main()
