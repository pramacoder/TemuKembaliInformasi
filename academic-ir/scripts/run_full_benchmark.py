#!/usr/bin/env python3
"""
Academic IR System — Full Benchmark Suite & Error Analysis
===========================================================
Runs side-by-side evaluation between Baseline TF-IDF and BM25 Retriever
across all 33 evaluation queries with Document-Level Aggregation.

Produces:
  - evaluation/results/baseline_tfidf_report.json
  - evaluation/results/bm25_report.json
  - evaluation/results/comparison_table.csv
  - evaluation/results/error_analysis.jsonl

Reference:
  - Expert plan §21 (Evaluation Protocol)
  - Expert plan §27 (Error Analysis Taxonomy)
  - Expert plan §33 (Research Questions RQ1 & RQ2)
"""

import sys
import os
import csv
import json
import logging
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.indexing.tfidf import TFIDFIndex
from src.preprocessing.pipeline import PreprocessingPipeline
from src.retrieval.search import SearchEngine
from src.retrieval.bm25 import BM25Retriever
from src.evaluation.metrics import evaluate, load_queries, load_qrels

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("full_benchmark")


ERROR_TAXONOMY = {
    "VOCABULARY_MISMATCH": "Query terms not matched in index despite relevant concept existing",
    "SEMANTIC_MISMATCH": "Keyword match occurred but semantic intent differs",
    "LANGUAGE_MISMATCH": "Query in Indonesian but target documents in English (or vice versa)",
    "WRONG_DOCUMENT_TYPE": "Retrieved documents of wrong type due to loose ranking",
    "BAD_METADATA": "Document has missing or incomplete title/author/course metadata",
    "LONG_DOCUMENT_BIAS": "Overly long document has disproportionately many chunks matched",
    "LOW_RECALL": "Fewer relevant documents retrieved than available in qrels",
    "PERFECT_MATCH": "Query retrieved relevant documents at top ranks",
}


def analyze_query_errors(qid: str, qtext: str, retrieved_docs: list, relevant_docs: set, qrels_map: dict) -> dict:
    """
    Classify failure mode for a given query based on retrieved vs relevant docs.
    """
    top5 = retrieved_docs[:5]
    top10 = retrieved_docs[:10]
    hits5 = [d for d in top5 if d in relevant_docs]
    hits10 = [d for d in top10 if d in relevant_docs]

    categories = []
    notes = []

    if len(hits5) >= 3:
        categories.append("PERFECT_MATCH")
        notes.append(f"Strong retrieval: {len(hits5)}/5 relevant in top-5")
    else:
        if len(hits10) == 0:
            # Complete miss
            if any(ord(c) > 127 for c in qtext) or any(w in qtext.lower() for w in ["clustering", "sentiment", "retrieval", "machine learning"]):
                categories.append("LANGUAGE_MISMATCH")
                notes.append("Possible cross-lingual vocabulary gap between Indonesian query and English corpus")
            else:
                categories.append("VOCABULARY_MISMATCH")
                notes.append("No relevant document found in top-10 lexical search")
        else:
            categories.append("LOW_RECALL")
            notes.append(f"Partial retrieval: {len(hits10)} in top-10, missed {len(relevant_docs) - len(hits10)} relevant")

    return {
        "query_id": qid,
        "query_text": qtext,
        "total_relevant_in_qrels": len(relevant_docs),
        "retrieved_top5_hits": len(hits5),
        "retrieved_top10_hits": len(hits10),
        "failure_modes": categories,
        "notes": "; ".join(notes),
    }


def main():
    parser = argparse.ArgumentParser(description="Run Full Academic IR Benchmark")
    parser.add_argument("--models-dir", type=str, default="models", help="TF-IDF models dir")
    parser.add_argument("--bm25-dir", type=str, default="models/bm25_v1", help="BM25 model dir")
    parser.add_argument("--queries", type=str, default="evaluation/queries.csv", help="Queries CSV")
    parser.add_argument("--qrels", type=str, default="evaluation/qrels.csv", help="Qrels CSV")
    parser.add_argument("--output-dir", type=str, default="evaluation/results", help="Output directory")
    args = parser.parse_args()

    out_dir = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load DB, queries, qrels
    db_file = PROJECT_ROOT / "database" / "academic_ir.db"
    db = Database(str(db_file))
    queries_path = PROJECT_ROOT / args.queries
    qrels_path = PROJECT_ROOT / args.qrels

    queries = load_queries(str(queries_path))
    qrels = load_qrels(str(qrels_path))
    logger.info(f"Loaded {len(queries)} queries and {sum(len(v) for v in qrels.values())} qrel judgements.")

    # 2. Setup TF-IDF Search Engine
    logger.info("Initializing TF-IDF Baseline Search Engine...")
    tfidf_index = TFIDFIndex()
    tfidf_index.load(str(PROJECT_ROOT / args.models_dir))
    pipeline = PreprocessingPipeline(default_language="id")
    tfidf_engine = SearchEngine(tfidf_index, db, pipeline)

    # 3. Setup BM25 Retriever
    bm25_model_file = PROJECT_ROOT / args.bm25_dir / "bm25_index.pkl"
    if not bm25_model_file.exists():
        logger.error(f"BM25 model not found at {bm25_model_file}. Run scripts/build_bm25_index.py first.")
        sys.exit(1)

    logger.info("Initializing BM25 Retriever...")
    bm25_engine = BM25Retriever()
    bm25_engine.load(str(PROJECT_ROOT / args.bm25_dir))

    # 4. Run Evaluation on TF-IDF
    logger.info("\n>>> Running Evaluation: Baseline TF-IDF (VSM)...")
    tfidf_eval = evaluate(tfidf_engine, queries, qrels, k_values=[5, 10, 20])
    with open(out_dir / "baseline_tfidf_report.json", "w", encoding="utf-8") as f:
        json.dump(tfidf_eval, f, indent=2)

    # 5. Run Evaluation on BM25
    logger.info("\n>>> Running Evaluation: Baseline BM25 (Okapi BM25)...")
    bm25_eval = evaluate(bm25_engine, queries, qrels, k_values=[5, 10, 20])
    with open(out_dir / "bm25_report.json", "w", encoding="utf-8") as f:
        json.dump(bm25_eval, f, indent=2)

    # 6. Generate Side-by-Side Comparison Table
    logger.info("\n>>> Generating Comparison Table...")
    comparison_csv = out_dir / "comparison_table.csv"
    with open(comparison_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Query ID", "Query Text",
            "TF-IDF P@5", "BM25 P@5",
            "TF-IDF P@10", "BM25 P@10",
            "TF-IDF NDCG@10", "BM25 NDCG@10",
            "TF-IDF AP", "BM25 AP",
            "TF-IDF RR", "BM25 RR",
            "Winner"
        ])

        for qid, qtext in queries.items():
            t_m = tfidf_eval["per_query"].get(qid, {})
            b_m = bm25_eval["per_query"].get(qid, {})

            t_ndcg = t_m.get("NDCG@10", 0.0)
            b_ndcg = b_m.get("NDCG@10", 0.0)
            t_ap = t_m.get("AP", 0.0)
            b_ap = b_m.get("AP", 0.0)

            winner = "BM25" if b_ndcg > t_ndcg else ("TF-IDF" if t_ndcg > b_ndcg else "TIE")

            writer.writerow([
                qid, qtext,
                t_m.get("P@5", 0.0), b_m.get("P@5", 0.0),
                t_m.get("P@10", 0.0), b_m.get("P@10", 0.0),
                t_ndcg, b_ndcg,
                t_ap, b_ap,
                t_m.get("RR", 0.0), b_m.get("RR", 0.0),
                winner
            ])

    # 7. Generate Error Analysis
    logger.info("\n>>> Conducting Error Analysis...")
    error_analysis_file = out_dir / "error_analysis.jsonl"
    with open(error_analysis_file, "w", encoding="utf-8") as f:
        for qid, qtext in queries.items():
            if qid not in qrels:
                continue
            rel_docs = set(did for did, score in qrels[qid].items() if score > 0)

            # Analyze TF-IDF
            t_res = [r["document_id"] for r in tfidf_engine.search(qtext, top_k=20)]
            t_analysis = analyze_query_errors(qid, qtext, t_res, rel_docs, qrels[qid])
            t_analysis["model"] = "TF-IDF"
            f.write(json.dumps(t_analysis) + "\n")

            # Analyze BM25
            b_res = [r["document_id"] for r in bm25_engine.search(qtext, top_k=20)]
            b_analysis = analyze_query_errors(qid, qtext, b_res, rel_docs, qrels[qid])
            b_analysis["model"] = "BM25"
            f.write(json.dumps(b_analysis) + "\n")

    # 8. Print Executive Summary
    t_agg = tfidf_eval.get("aggregate", {})
    b_agg = bm25_eval.get("aggregate", {})

    print("\n" + "=" * 84)
    print("      ACADEMIC IR SYSTEM — BENCHMARK RESULTS (TF-IDF vs BM25)")
    print("=" * 84)
    print(f"{'Metric':<24} {'TF-IDF (Baseline A)':<22} {'BM25 (Baseline B)':<22} {'Delta':<12}")
    print("-" * 84)

    metrics_to_show = [
        ("MAP", "MAP"),
        ("MRR", "MRR"),
        ("Avg_P@5", "P@5"),
        ("Avg_P@10", "P@10"),
        ("Avg_R@10", "Recall@10"),
        ("Avg_NDCG@10", "NDCG@10"),
    ]

    for key, label in metrics_to_show:
        t_val = t_agg.get(key, 0.0)
        b_val = b_agg.get(key, 0.0)
        delta = b_val - t_val
        delta_str = f"+{delta:.4f}" if delta > 0 else f"{delta:.4f}"
        print(f"{label:<24} {t_val:<22.4f} {b_val:<22.4f} {delta_str:<12}")

    print("=" * 84)
    print(f"Results saved to:")
    print(f"  - TF-IDF Report:       {out_dir / 'baseline_tfidf_report.json'}")
    print(f"  - BM25 Report:         {out_dir / 'bm25_report.json'}")
    print(f"  - Comparison Table:    {comparison_csv}")
    print(f"  - Error Analysis:      {error_analysis_file}\n")


if __name__ == "__main__":
    main()
