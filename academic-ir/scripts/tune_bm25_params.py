#!/usr/bin/env python3
"""
Academic IR System — BM25 Parameter Tuning Script
==================================================
Grid search over BM25 hyperparameters (k1, b) using a development set.

IMPORTANT: Only the development set (Q01–Q22) is used for tuning.
           The test set (Q23–Q33) MUST NOT be seen during tuning to
           prevent test-set leakage / overfitting.

Audit basis: Section 13 — Parameter BM25 Belum Dibuktikan Optimal.

Produces:
  - evaluation/results/bm25_tuning.json
    Contains: all 20 grid combinations scored on dev set,
              best parameter set, and test-set evaluation of best params.

Usage:
    python scripts/tune_bm25_params.py
    python scripts/tune_bm25_params.py --dev-cutoff Q22 --test-start Q23
"""

import sys
import json
import logging
import argparse
import pickle
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.metrics import (
    load_queries, load_qrels, precision_at_k,
    recall_at_k, average_precision, ndcg_at_k, reciprocal_rank
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("bm25_tuning")


# ─── BM25 Scoring (in-memory, no index reload each time) ─────────────────────

class BM25GridSearch:
    """
    Loads BM25 index once and allows re-scoring with different k1/b parameters
    without rebuilding the inverted index.
    """

    def __init__(self, bm25_index_path: str):
        logger.info(f"Loading BM25 index from {bm25_index_path} ...")
        with open(bm25_index_path, "rb") as f:
            data = pickle.load(f)

        # rank_bm25 serialization format: keys are bm25, chunk_ids, chunk_meta, k1, b
        self.chunk_ids: List[str] = data["chunk_ids"]
        self.chunk_meta: dict = data.get("chunk_meta", {})
        self.N: int = len(self.chunk_ids)
        self.bm25_obj = data["bm25"]

        # Build doc_id mapping from chunk_ids
        self._chunk_to_doc: Dict[str, str] = {}
        for cid in self.chunk_ids:
            # Format: MAT-000001-C0001 → MAT-000001
            if "-C" in cid:
                did = cid.rsplit("-C", 1)[0]
            else:
                did = cid
            self._chunk_to_doc[cid] = did

        # Build preprocessor
        self.preprocessor = self._get_preprocessor()
        logger.info(f"BM25 index loaded: {self.N} chunks.")

    def _get_preprocessor(self):
        try:
            from src.preprocessing.pipeline import PreprocessingPipeline
            return PreprocessingPipeline(default_language="id")
        except Exception:
            return None

    def _tokenize(self, text: str) -> List[str]:
        if self.preprocessor:
            try:
                return self.preprocessor.tokenize(text)
            except Exception:
                pass
        return text.lower().split()

    def search(self, query: str, top_k: int = 20,
               k1: float = 1.5, b: float = 0.75) -> List[Dict[str, Any]]:
        """Search using BM25Okapi with custom k1/b, aggregate max score per doc."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        self.bm25_obj.k1 = k1
        self.bm25_obj.b = b
        chunk_scores_arr = self.bm25_obj.get_scores(query_terms)

        # Aggregate to document level (max score per doc)
        doc_best = {}
        for i, s in enumerate(chunk_scores_arr):
            if s <= 0:
                continue
            cid = self.chunk_ids[i]
            did = self._chunk_to_doc.get(cid, cid)
            if did not in doc_best or s > doc_best[did]:
                doc_best[did] = s

        ranked = sorted(doc_best.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"document_id": did, "score": s} for did, s in ranked]


# ─── Evaluation helper ────────────────────────────────────────────────────────

def evaluate_params(engine: BM25GridSearch, queries: Dict[str, str],
                    qrels: Dict[str, Dict[str, int]],
                    k1: float, b: float,
                    k_val: int = 10) -> Dict[str, float]:
    """Evaluate a (k1, b) configuration on given query set."""
    ndcg_scores, ap_scores, rr_scores, p10_scores = [], [], [], []

    for qid, qtext in queries.items():
        if qid not in qrels:
            continue
        results = engine.search(qtext, top_k=max(20, k_val), k1=k1, b=b)
        retrieved = [r["document_id"] for r in results]
        relevant = set(did for did, rel in qrels[qid].items() if rel > 0)

        ndcg_scores.append(ndcg_at_k(retrieved, qrels[qid], k_val))
        ap_scores.append(average_precision(retrieved, relevant))
        rr_scores.append(reciprocal_rank(retrieved, relevant))
        p10_scores.append(precision_at_k(retrieved, relevant, k_val))

    def avg(lst): return round(sum(lst) / len(lst), 4) if lst else 0.0

    return {
        f"NDCG@{k_val}": avg(ndcg_scores),
        "MAP":            avg(ap_scores),
        "MRR":            avg(rr_scores),
        f"P@{k_val}":     avg(p10_scores),
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BM25 Parameter Tuning (Grid Search)")
    parser.add_argument("--bm25-index",   default="models/bm25_v1/bm25_index.pkl")
    parser.add_argument("--queries",      default="evaluation/queries.csv")
    parser.add_argument("--qrels",        default="evaluation/qrels.csv")
    parser.add_argument("--output-dir",   default="evaluation/results")
    parser.add_argument("--dev-cutoff",   default="Q22",
                        help="Last query ID in development set (default: Q22)")
    parser.add_argument("--test-start",   default="Q23",
                        help="First query ID in test set (default: Q23)")
    parser.add_argument("--primary-metric", default="NDCG@10",
                        help="Metric used to select best parameters")
    args = parser.parse_args()

    bm25_path = PROJECT_ROOT / args.bm25_index
    if not bm25_path.exists():
        logger.error(f"BM25 index not found at {bm25_path}. Run scripts/build_bm25_index.py first.")
        sys.exit(1)

    out_dir = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    queries = load_queries(str(PROJECT_ROOT / args.queries))
    qrels   = load_qrels(str(PROJECT_ROOT / args.qrels))
    logger.info(f"Loaded {len(queries)} queries, {sum(len(v) for v in qrels.values())} judgements.")

    # Dev/Test split
    all_qids = sorted(queries.keys())
    dev_qids  = [q for q in all_qids if q <= args.dev_cutoff]
    test_qids = [q for q in all_qids if q >= args.test_start]
    dev_queries  = {q: queries[q] for q in dev_qids if q in queries}
    test_queries = {q: queries[q] for q in test_qids if q in queries}

    logger.info(f"Dev set: {len(dev_queries)} queries ({dev_qids[0]}–{dev_qids[-1]})")
    logger.info(f"Test set: {len(test_queries)} queries ({test_qids[0]}–{test_qids[-1]})")
    logger.warning("⚠ Test set is ONLY evaluated at the very end using the best parameters found on dev set.")

    # Load BM25 engine (once)
    engine = BM25GridSearch(str(bm25_path))

    # Grid search parameters
    k1_values = [0.5, 1.0, 1.5, 2.0]
    b_values  = [0.0, 0.25, 0.50, 0.75, 1.00]

    logger.info(f"\nStarting grid search: {len(k1_values)} × {len(b_values)} = {len(k1_values)*len(b_values)} combinations")
    logger.info(f"Optimizing for: {args.primary_metric} on dev set\n")

    grid_results = []
    best_score = -1.0
    best_params = {"k1": 1.5, "b": 0.75}

    for k1 in k1_values:
        for b in b_values:
            metrics = evaluate_params(engine, dev_queries, qrels, k1=k1, b=b)
            score = metrics.get(args.primary_metric, 0.0)

            result_entry = {
                "k1": k1, "b": b,
                **metrics,
                "is_default": (k1 == 1.5 and b == 0.75),
            }
            grid_results.append(result_entry)

            logger.info(
                f"  k1={k1:.2f}  b={b:.2f}  "
                f"{args.primary_metric}={score:.4f}  MAP={metrics['MAP']:.4f}  "
                f"{'★ DEFAULT' if result_entry['is_default'] else ''}"
            )

            if score > best_score:
                best_score = score
                best_params = {"k1": k1, "b": b}

    logger.info(f"\n✓ Best params (dev): k1={best_params['k1']}, b={best_params['b']} → {args.primary_metric}={best_score:.4f}")

    # Evaluate best params on test set (only once!)
    logger.info(f"\nEvaluating best params on TEST SET (this runs only once)...")
    test_metrics_best = evaluate_params(engine, test_queries, qrels,
                                        k1=best_params["k1"], b=best_params["b"])

    # Also evaluate default params on test set for comparison
    logger.info("Evaluating default params (k1=1.5, b=0.75) on TEST SET for comparison...")
    test_metrics_default = evaluate_params(engine, test_queries, qrels, k1=1.5, b=0.75)

    # Sort grid results by primary metric descending
    grid_results.sort(key=lambda x: x.get(args.primary_metric, 0), reverse=True)

    report = {
        "configuration": {
            "primary_metric": args.primary_metric,
            "dev_set": {"query_ids": dev_qids, "n": len(dev_qids)},
            "test_set": {"query_ids": test_qids, "n": len(test_qids)},
            "k1_search_space": k1_values,
            "b_search_space":  b_values,
            "total_combinations": len(k1_values) * len(b_values),
        },
        "best_params": {
            **best_params,
            f"dev_{args.primary_metric}": best_score,
            "test_metrics": test_metrics_best,
        },
        "default_params_comparison": {
            "k1": 1.5, "b": 0.75,
            "test_metrics": test_metrics_default,
            "note": "These are the commonly used default values (k1=1.5, b=0.75)."
        },
        "improvement_over_default": {
            k: round(test_metrics_best.get(k, 0) - test_metrics_default.get(k, 0), 4)
            for k in test_metrics_best
        },
        "grid_search_results_dev_set": grid_results,
        "audit_note": (
            "Parameter tuning was performed exclusively on the development set. "
            "Test set was only evaluated ONCE with the best parameters to prevent "
            "test-set leakage. This addresses audit finding §13."
        )
    }

    out_path = out_dir / "bm25_tuning.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary
    print("\n" + "=" * 70)
    print("  BM25 PARAMETER TUNING RESULTS")
    print("=" * 70)
    print(f"  Primary metric     : {args.primary_metric}")
    print(f"  Dev set            : {dev_qids[0]}–{dev_qids[-1]} ({len(dev_qids)} queries)")
    print(f"  Test set           : {test_qids[0]}–{test_qids[-1]} ({len(test_qids)} queries)")
    print("-" * 70)
    print(f"  Best params (dev)  : k1={best_params['k1']}, b={best_params['b']}")
    print(f"  Default params     : k1=1.5, b=0.75")
    print("-" * 70)
    print(f"  {'Metric':<15} {'Best Params':>14} {'Default':>14} {'Delta':>10}")
    print(f"  {'-'*15} {'-'*14} {'-'*14} {'-'*10}")
    for k in test_metrics_best:
        best_v   = test_metrics_best[k]
        default_v = test_metrics_default.get(k, 0)
        delta = best_v - default_v
        print(f"  {k:<15} {best_v:>14.4f} {default_v:>14.4f} {delta:>+10.4f}")
    print("=" * 70)
    print(f"\n  Full results: {out_path}\n")


if __name__ == "__main__":
    main()
