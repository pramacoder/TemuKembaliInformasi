#!/usr/bin/env python3
"""
Academic IR System — Ablation Study Runner
==========================================
Runs ablation ladder experiments E0–E5 to identify which components
of the retrieval pipeline contribute to performance improvements.

Ablation Ladder:
  E0: TF-IDF (baseline, no chunking, no aggregation)
  E1: TF-IDF + Chunk (chunking enabled)
  E2: TF-IDF + Chunk + Aggregation (max-doc aggregation)
  E3: BM25 + Chunk + Aggregation (current best)
  E4: BM25 + Title Boost (field weighting)
  E5: BM25 + Query Expansion (vocabulary bridge)

Audit basis:
  - Section 12: Penyebab peningkatan BM25 tidak bisa langsung disimpulkan
  - Section 21: Belum terbukti bahwa metadata-aware ranking meningkatkan performa
  - Section 26: Arsitektur eksperimen yang direkomendasikan (ablation ladder)

Produces:
  - evaluation/results/ablation_results.json

Usage:
    python scripts/run_ablation.py
    python scripts/run_ablation.py --experiments E0,E3,E4
    python scripts/run_ablation.py --skip-missing
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.metrics import (
    load_queries, load_qrels, evaluate
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ablation")


# ─── Engine Wrappers ─────────────────────────────────────────────────────────

class E0_TFIDFEngine:
    """E0: Baseline TF-IDF (standard vector space model, no chunking tweak)."""

    def __init__(self, models_dir: str, db):
        from src.indexing.tfidf import TFIDFIndex
        from src.preprocessing.pipeline import PreprocessingPipeline
        from src.retrieval.search import SearchEngine
        self.index = TFIDFIndex()
        self.index.load(models_dir)
        pipeline = PreprocessingPipeline(default_language="id")
        self.engine = SearchEngine(self.index, db, pipeline)

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        return self.engine.search(query, top_k=top_k)


class E3_BM25Engine:
    """E3: BM25 + Chunk + Aggregation (current best system)."""

    def __init__(self, bm25_dir: str):
        from src.retrieval.bm25 import BM25Retriever
        self.engine = BM25Retriever()
        self.engine.load(bm25_dir)

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        return self.engine.search(query, top_k=top_k)


class E4_BM25TitleBoostEngine:
    """
    E4: BM25 + Title Boost.
    Applies a score multiplier to documents whose title overlaps with the query.
    Requires that search results include 'title' field.
    """

    def __init__(self, bm25_dir: str, title_boost: float = 1.5):
        from src.retrieval.bm25 import BM25Retriever
        self.engine = BM25Retriever()
        self.engine.load(bm25_dir)
        self.title_boost = title_boost

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        results = self.engine.search(query, top_k=top_k * 2)
        query_terms = set(query.lower().split())
        boosted = []
        for r in results:
            title = (r.get("title") or "").lower()
            title_terms = set(title.split())
            overlap = query_terms & title_terms
            boost = self.title_boost if len(overlap) >= 2 else 1.0
            boosted.append({**r, "score": r.get("score", 0.0) * boost})
        boosted.sort(key=lambda x: x["score"], reverse=True)
        return boosted[:top_k]


class E5_BM25QueryExpansionEngine:
    """
    E5: BM25 + Query Expansion via bilingual synonym dictionary.
    Falls back to E3 if synonym dict not found.
    """

    def __init__(self, bm25_dir: str, synonym_dict_path: Optional[str] = None):
        from src.retrieval.bm25 import BM25Retriever
        self.engine = BM25Retriever()
        self.engine.load(bm25_dir)
        self.synonyms: Dict[str, List[str]] = {}

        if synonym_dict_path:
            try:
                with open(synonym_dict_path, encoding="utf-8") as f:
                    self.synonyms = json.load(f)
                logger.info(f"Loaded {len(self.synonyms)} synonym entries.")
            except FileNotFoundError:
                logger.warning(f"Synonym dict not found at {synonym_dict_path}. "
                                "E5 will run without expansion (same as E3).")
        else:
            # Try default path
            default_path = PROJECT_ROOT / "data" / "synonym_dict_bilingual.json"
            if default_path.exists():
                with open(default_path, encoding="utf-8") as f:
                    self.synonyms = json.load(f)
                logger.info(f"Loaded {len(self.synonyms)} synonym entries from default path.")

    def _expand_query(self, query: str) -> str:
        expanded_terms = [query]
        q_lower = query.lower()
        for term, expansions in self.synonyms.items():
            if term in q_lower:
                expanded_terms.extend(expansions)
        expanded = " ".join(expanded_terms)
        if expanded != query:
            logger.debug(f"Expanded: '{query}' → '{expanded}'")
        return expanded

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        expanded_query = self._expand_query(query)
        return self.engine.search(expanded_query, top_k=top_k)


# ─── Experiment Runner ────────────────────────────────────────────────────────

def run_experiment(label: str, engine, queries: Dict[str, str],
                   qrels: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    """Run a single ablation experiment and return metrics + latency."""
    import time
    logger.info(f"\n>>> Running experiment: {label}")
    start = time.time()
    results = evaluate(engine, queries, qrels, k_values=[5, 10, 20])
    elapsed = round(time.time() - start, 2)
    agg = results.get("aggregate", {})
    return {
        "label": label,
        "MAP":      agg.get("MAP", 0.0),
        "MRR":      agg.get("MRR", 0.0),
        "P@5":      agg.get("Avg_P@5", 0.0),
        "P@10":     agg.get("Avg_P@10", 0.0),
        "NDCG@10":  agg.get("Avg_NDCG@10", 0.0),
        "R@10":     agg.get("Avg_R@10", 0.0),
        "eval_time_sec": elapsed,
        "per_query": results.get("per_query", {}),
    }


def delta(current: float, reference: float) -> str:
    d = current - reference
    return f"{d:+.4f}"


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="IR Ablation Ladder Study")
    parser.add_argument("--models-dir",      default="models")
    parser.add_argument("--bm25-dir",        default="models/bm25_v1")
    parser.add_argument("--synonym-dict",    default=None)
    parser.add_argument("--queries",         default="evaluation/queries.csv")
    parser.add_argument("--qrels",           default="evaluation/qrels.csv")
    parser.add_argument("--output-dir",      default="evaluation/results")
    parser.add_argument("--experiments",     default="E0,E3,E4,E5",
                        help="Comma-separated list of experiments to run (E0,E3,E4,E5)")
    parser.add_argument("--skip-missing",    action="store_true",
                        help="Skip experiments whose models are not available")
    args = parser.parse_args()

    selected = [e.strip() for e in args.experiments.split(",")]
    out_dir = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    queries = load_queries(str(PROJECT_ROOT / args.queries))
    qrels   = load_qrels(str(PROJECT_ROOT / args.qrels))
    logger.info(f"Loaded {len(queries)} queries, {sum(len(v) for v in qrels.values())} judgements.")

    # Check model availability
    tfidf_available = (PROJECT_ROOT / args.models_dir / "tfidf_vectorizer.pkl").exists()
    bm25_available  = (PROJECT_ROOT / args.bm25_dir / "bm25_index.pkl").exists()

    if not tfidf_available and not args.skip_missing:
        logger.error("TF-IDF model not found. Run indexing pipeline first.")
        sys.exit(1)
    if not bm25_available and not args.skip_missing:
        logger.error("BM25 model not found. Run scripts/build_bm25_index.py first.")
        sys.exit(1)

    # Load DB for TF-IDF
    db = None
    if tfidf_available:
        try:
            from src.database.models import Database
            db_file = PROJECT_ROOT / "database" / "academic_ir.db"
            if db_file.exists():
                db = Database(str(db_file))
        except Exception as e:
            logger.warning(f"Could not load database: {e}. TF-IDF experiments may fail.")

    # ── Run selected experiments ──────────────────────────────────────────
    ablation_results = []

    experiment_registry = {
        "E0": {
            "name": "E0: TF-IDF Baseline",
            "description": "Standard TF-IDF VSM — current baseline A",
            "available": tfidf_available and db is not None,
            "factory": lambda: E0_TFIDFEngine(str(PROJECT_ROOT / args.models_dir), db),
        },
        "E3": {
            "name": "E3: BM25 + Chunk + Aggregation",
            "description": "Okapi BM25 with document-level aggregation — current best (Baseline B)",
            "available": bm25_available,
            "factory": lambda: E3_BM25Engine(str(PROJECT_ROOT / args.bm25_dir)),
        },
        "E4": {
            "name": "E4: BM25 + Title Boost",
            "description": "BM25 with score boost applied when title overlaps with query terms",
            "available": bm25_available,
            "factory": lambda: E4_BM25TitleBoostEngine(str(PROJECT_ROOT / args.bm25_dir)),
        },
        "E5": {
            "name": "E5: BM25 + Query Expansion",
            "description": "BM25 with bilingual synonym expansion to bridge vocabulary mismatch",
            "available": bm25_available,
            "factory": lambda: E5_BM25QueryExpansionEngine(
                str(PROJECT_ROOT / args.bm25_dir),
                str(PROJECT_ROOT / args.synonym_dict) if args.synonym_dict else None
            ),
        },
    }

    for exp_key in selected:
        if exp_key not in experiment_registry:
            logger.warning(f"Unknown experiment: {exp_key}. Skipping.")
            continue

        exp = experiment_registry[exp_key]
        if not exp["available"]:
            if args.skip_missing:
                logger.warning(f"Skipping {exp_key}: required model not available.")
                continue
            else:
                logger.error(f"Required model for {exp_key} not available.")
                sys.exit(1)

        try:
            engine = exp["factory"]()
            result = run_experiment(exp["name"], engine, queries, qrels)
            result["experiment_id"] = exp_key
            result["description"] = exp["description"]
            ablation_results.append(result)
        except Exception as e:
            logger.error(f"Experiment {exp_key} failed: {e}")
            if not args.skip_missing:
                raise

    if not ablation_results:
        logger.error("No experiments completed successfully.")
        sys.exit(1)

    # ── Generate report ───────────────────────────────────────────────────
    e0_result = next((r for r in ablation_results if r["experiment_id"] == "E0"), None)
    e3_result = next((r for r in ablation_results if r["experiment_id"] == "E3"), None)
    ref_result = e3_result or ablation_results[0]

    report = {
        "ablation_ladder": [
            {k: v for k, v in r.items() if k != "per_query"}
            for r in ablation_results
        ],
        "component_contribution_vs_e3": {
            r["experiment_id"]: {
                "delta_MAP":    delta(r["MAP"],    ref_result["MAP"]),
                "delta_NDCG@10": delta(r["NDCG@10"], ref_result["NDCG@10"]),
                "delta_P@10":   delta(r["P@10"],   ref_result["P@10"]),
            }
            for r in ablation_results if r["experiment_id"] != "E3"
        } if e3_result else {},
        "conclusion": (
            "The ablation ladder allows attribution of each performance gain to a specific "
            "component. Improvements should be analyzed incrementally to avoid overclaiming. "
            "Audit §12: causation between BM25 improvement and document-length normalization "
            "requires controlled comparison, not just E0 vs E3."
        ),
        "per_query_detail": {
            r["experiment_id"]: r.get("per_query", {})
            for r in ablation_results
        }
    }

    out_path = out_dir / "ablation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ── Console table ─────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  ABLATION STUDY RESULTS")
    print("=" * 80)
    print(f"  {'Experiment':<35} {'MAP':>7} {'NDCG@10':>9} {'P@10':>7} {'MRR':>7}")
    print(f"  {'-'*35} {'-'*7} {'-'*9} {'-'*7} {'-'*7}")
    for r in ablation_results:
        print(f"  {r['label']:<35} {r['MAP']:>7.4f} {r['NDCG@10']:>9.4f} {r['P@10']:>7.4f} {r['MRR']:>7.4f}")
    print("=" * 80)
    print(f"\n  Full results: {out_path}\n")


if __name__ == "__main__":
    main()
