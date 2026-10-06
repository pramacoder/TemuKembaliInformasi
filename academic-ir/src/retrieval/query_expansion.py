#!/usr/bin/env python3
"""
Academic IR System — Query Expansion Module
============================================
Synonym-based bilingual query expansion to bridge vocabulary mismatch
between Indonesian queries and English (or mixed-language) documents.

Problem addressed (audit §24):
  Vocabulary mismatch is a root cause of retrieval failures:
  - Query "analisis sentimen" misses documents about "sentiment analysis"
  - Query "jaringan saraf" misses documents about "neural network"

This module provides:
  1. QueryExpander class (used by search API and ablation scripts)
  2. CLI for evaluating BM25 vs BM25+QE on all 33 queries

Usage as library:
    from src.retrieval.query_expansion import QueryExpander
    expander = QueryExpander()
    expanded = expander.expand("analisis sentimen")
    # → "analisis sentimen sentiment analysis opinion mining"

Usage as CLI:
    python src/retrieval/query_expansion.py --query "analisis sentimen"
    python src/retrieval/query_expansion.py --eval --output-dir evaluation/results
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


# ─── Built-in Bilingual Synonym Dictionary ───────────────────────────────────
# Domain: Informatika / Computer Science (Indonesian ↔ English)
# Entries cover the most common vocabulary gaps identified in error analysis.

BUILTIN_SYNONYMS: Dict[str, List[str]] = {
    # NLP / Text Mining
    "analisis sentimen":         ["sentiment analysis", "opinion mining", "sentiment classification"],
    "penambangan teks":          ["text mining", "information extraction"],
    "pemrosesan bahasa alami":   ["natural language processing", "NLP", "computational linguistics"],
    "klasifikasi teks":          ["text classification", "document classification"],
    "pengenalan entitas":        ["named entity recognition", "NER"],

    # Machine Learning
    "pembelajaran mesin":        ["machine learning", "statistical learning", "predictive modeling"],
    "jaringan saraf":            ["neural network", "artificial neural network", "ANN"],
    "pembelajaran mendalam":     ["deep learning", "deep neural network", "DNN"],
    "pohon keputusan":           ["decision tree", "classification tree"],
    "hutan acak":                ["random forest", "ensemble learning"],
    "mesin vektor pendukung":    ["support vector machine", "SVM"],
    "regresi linier":            ["linear regression", "regression analysis"],
    "klasterisasi":              ["clustering", "cluster analysis", "unsupervised learning"],
    "pengelompokan data":        ["data clustering", "k-means", "hierarchical clustering"],
    "naive bayes":               ["naive bayes classifier", "probabilistic classifier", "Bayes classifier"],

    # Computer Vision / Image
    "pengolahan citra":          ["image processing", "computer vision", "digital image processing"],
    "deteksi objek":             ["object detection", "object recognition"],
    "segmentasi gambar":         ["image segmentation", "semantic segmentation"],
    "pengenalan wajah":          ["face recognition", "facial recognition"],

    # Information Retrieval
    "temu kembali informasi":    ["information retrieval", "IR system", "search engine"],
    "pencarian informasi":       ["information retrieval", "document retrieval", "search"],
    "peringkat dokumen":         ["document ranking", "relevance ranking", "ranked retrieval"],
    "model ruang vektor":        ["vector space model", "VSM", "TF-IDF"],

    # Data & Databases
    "basis data":                ["database", "relational database", "SQL"],
    "penambangan data":          ["data mining", "knowledge discovery"],
    "gudang data":               ["data warehouse", "OLAP", "business intelligence"],
    "kualitas data":             ["data quality", "data cleaning", "data preprocessing"],

    # Software Engineering
    "rekayasa perangkat lunak":  ["software engineering", "software development"],
    "pengembangan perangkat lunak": ["software development", "SDLC", "agile"],
    "pengujian perangkat lunak": ["software testing", "unit testing", "quality assurance"],
    "desain sistem":             ["system design", "system architecture", "software design"],
    "analisis sistem":           ["systems analysis", "requirements analysis"],
    "diagram kelas":             ["class diagram", "UML", "object-oriented design"],

    # Networking / Security
    "jaringan komputer":         ["computer network", "networking", "TCP/IP"],
    "keamanan jaringan":         ["network security", "cybersecurity", "information security"],
    "keamanan informasi":        ["information security", "cybersecurity", "data security"],
    "kriptografi":               ["cryptography", "encryption", "cryptographic protocol"],

    # Embedded / IoT
    "sistem tertanam":           ["embedded system", "embedded computing", "microcontroller"],
    "internet of things":        ["IoT", "connected devices", "smart devices"],

    # Mathematics / Statistics
    "aljabar linier":            ["linear algebra", "matrix operations", "vector operations"],
    "statistika":                ["statistics", "statistical analysis", "probability"],
    "probabilitas":              ["probability", "probability theory", "stochastic"],

    # Generic academic terms
    "penelitian":                ["research", "study", "investigation"],
    "skripsi":                   ["undergraduate thesis", "final project", "bachelor thesis"],
    "tesis":                     ["thesis", "graduate thesis", "dissertation"],
    "jurnal":                    ["journal", "research paper", "academic paper"],
    "metode":                    ["method", "methodology", "approach", "technique"],
    "algoritma":                 ["algorithm", "computational method"],
    "evaluasi":                  ["evaluation", "assessment", "benchmarking"],
    "optimasi":                  ["optimization", "parameter tuning", "hyperparameter optimization"],
    "implementasi":              ["implementation", "development", "system development"],
    "perancangan":               ["design", "system design", "architecture"],
    "antarmuka":                 ["interface", "user interface", "UI", "GUI"],
    "aplikasi":                  ["application", "software application", "system"],
    "kinerja":                   ["performance", "efficiency", "accuracy"],
    "akurasi":                   ["accuracy", "precision", "performance metric"],
    "prediksi":                  ["prediction", "forecasting", "classification"],
    "klasifikasi":               ["classification", "categorization", "labeling"],

    # Reverse (English → Indonesian synonyms to help when query is in English)
    "sentiment analysis":        ["analisis sentimen", "opini publik"],
    "data clustering":           ["pengelompokan data", "klasterisasi"],
    "machine learning":          ["pembelajaran mesin", "kecerdasan buatan"],
    "information retrieval":     ["temu kembali informasi", "pencarian informasi"],
    "deep learning":             ["pembelajaran mendalam", "jaringan saraf dalam"],
    "natural language processing": ["pemrosesan bahasa alami", "analisis teks"],
}


class QueryExpander:
    """
    Bilingual synonym-based query expansion for Indonesian-English academic IR.

    Expands a query by appending known synonyms of matched phrases,
    broadening lexical coverage without semantic embedding.

    This is a deterministic, dictionary-based approach — no model weights needed.
    It directly addresses vocabulary mismatch identified in error analysis (audit §24).
    """

    def __init__(self, synonym_dict: Optional[Dict[str, List[str]]] = None,
                 external_dict_path: Optional[str] = None,
                 max_expansions: int = 3):
        """
        Args:
            synonym_dict:      Custom synonym dictionary (overrides built-in).
            external_dict_path: Path to JSON synonym dict to merge with built-in.
            max_expansions:    Maximum number of synonyms to add per matched term.
        """
        self.synonyms = dict(BUILTIN_SYNONYMS)
        self.max_expansions = max_expansions

        if synonym_dict:
            self.synonyms.update(synonym_dict)
            logger.debug(f"Loaded {len(synonym_dict)} custom synonym entries.")

        if external_dict_path:
            try:
                with open(external_dict_path, encoding="utf-8") as f:
                    ext = json.load(f)
                self.synonyms.update(ext)
                logger.debug(f"Merged {len(ext)} entries from external dict.")
            except FileNotFoundError:
                logger.warning(f"External synonym dict not found: {external_dict_path}")

        # Sort by length descending for greedy longest-match
        self._sorted_terms = sorted(self.synonyms.keys(), key=len, reverse=True)

    def expand(self, query: str, verbose: bool = False) -> str:
        """
        Expand query by appending synonyms of matched phrases.

        Strategy: greedy longest-phrase match (no overlap allowed).

        Args:
            query:   Original query string.
            verbose: If True, log matched terms and expansions.

        Returns:
            Expanded query string.
        """
        q_lower = query.lower()
        matched_terms = []
        expansions = []
        covered = set()  # Track character positions already expanded

        for term in self._sorted_terms:
            pos = q_lower.find(term)
            if pos == -1:
                continue
            end = pos + len(term)
            if any(pos < c_end and end > c_start for c_start, c_end in covered):
                continue
            covered.add((pos, end))
            syns = self.synonyms[term][:self.max_expansions]
            matched_terms.append(term)
            expansions.extend(syns)

        if not expansions:
            return query

        # Deduplicate expansions, keeping original query terms intact
        expansion_str = " ".join(e for e in expansions if e.lower() not in q_lower)
        expanded = query + " " + expansion_str if expansion_str else query

        if verbose:
            logger.info(f"Query: '{query}'")
            logger.info(f"Matched terms: {matched_terms}")
            logger.info(f"Expanded: '{expanded}'")

        return expanded.strip()

    def expand_batch(self, queries: Dict[str, str]) -> Dict[str, str]:
        """Expand a dictionary of {query_id: query_text}."""
        return {qid: self.expand(q) for qid, q in queries.items()}

    def get_expansions(self, query: str) -> Dict[str, List[str]]:
        """Return a dict of {matched_term: [synonyms]} for a query."""
        q_lower = query.lower()
        result = {}
        for term in self._sorted_terms:
            if term in q_lower:
                result[term] = self.synonyms[term][:self.max_expansions]
        return result


# ─── CLI / Evaluation Mode ────────────────────────────────────────────────────

def _evaluate_with_expansion(args):
    """Compare BM25 vs BM25+QE on all queries and save results."""
    from src.evaluation.metrics import load_queries, load_qrels, evaluate
    from src.retrieval.bm25 import BM25Retriever

    out_dir = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    queries = load_queries(str(PROJECT_ROOT / args.queries))
    qrels   = load_qrels(str(PROJECT_ROOT / args.qrels))

    bm25_dir = PROJECT_ROOT / args.bm25_dir
    if not (bm25_dir / "bm25_index.pkl").exists():
        logger.error(f"BM25 index not found at {bm25_dir}. Run build_bm25_index.py first.")
        sys.exit(1)

    # BM25 baseline (no expansion)
    bm25 = BM25Retriever()
    bm25.load(str(bm25_dir))
    logger.info("Running BM25 baseline evaluation...")
    bm25_eval = evaluate(bm25, queries, qrels)

    # BM25 + Query Expansion
    expander = QueryExpander()

    class BM25QEEngine:
        def __init__(self, engine, qexpander):
            self.engine = engine
            self.qexpander = qexpander
        def search(self, query: str, top_k: int = 20):
            expanded = self.qexpander.expand(query)
            return self.engine.search(expanded, top_k=top_k)

    bm25_qe = BM25QEEngine(bm25, expander)
    logger.info("Running BM25+QE evaluation...")
    bm25_qe_eval = evaluate(bm25_qe, queries, qrels)

    # Build comparison
    bm25_agg   = bm25_eval.get("aggregate", {})
    bm25qe_agg = bm25_qe_eval.get("aggregate", {})

    metrics = ["MAP", "MRR", "Avg_P@5", "Avg_P@10", "Avg_NDCG@10", "Avg_R@10"]
    comparison = {}
    for m in metrics:
        b = bm25_agg.get(m, 0.0)
        q = bm25qe_agg.get(m, 0.0)
        comparison[m] = {
            "bm25":     b,
            "bm25_qe":  q,
            "delta":    round(q - b, 4),
            "improved": q > b,
        }

    per_query_comparison = {}
    for qid in queries:
        b = bm25_eval["per_query"].get(qid, {})
        q = bm25_qe_eval["per_query"].get(qid, {})
        expanded_q = expander.expand(queries[qid])
        per_query_comparison[qid] = {
            "original_query":  queries[qid],
            "expanded_query":  expanded_q,
            "expanded":        expanded_q != queries[qid],
            "bm25_NDCG@10":   b.get("NDCG@10", 0.0),
            "bm25qe_NDCG@10": q.get("NDCG@10", 0.0),
            "delta_NDCG@10":  round(q.get("NDCG@10", 0) - b.get("NDCG@10", 0), 4),
        }

    report = {
        "method": "BM25 vs BM25 + Synonym Query Expansion (bilingual dictionary)",
        "n_queries":       len(queries),
        "n_synonyms_dict": len(BUILTIN_SYNONYMS),
        "metric_comparison": comparison,
        "per_query": per_query_comparison,
        "queries_expanded": sum(1 for v in per_query_comparison.values() if v["expanded"]),
        "conclusion": (
            "Positive delta indicates that query expansion improved retrieval. "
            "Focus on queries where 'expanded=True' and check if delta is positive. "
            "Negative deltas may indicate over-expansion (noisy synonyms)."
        )
    }

    out_path = out_dir / "query_expansion_eval.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    n_exp = report["queries_expanded"]
    print("\n" + "=" * 65)
    print("  BM25 vs BM25 + QUERY EXPANSION EVALUATION")
    print("=" * 65)
    print(f"  Queries expanded  : {n_exp}/{len(queries)}")
    print(f"  {'Metric':<20} {'BM25':>8} {'BM25+QE':>9} {'Delta':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*9} {'-'*8}")
    for m, vals in comparison.items():
        tag = "[+]" if vals["improved"] else "[-]"
        print(f"  {m:<20} {vals['bm25']:>8.4f} {vals['bm25_qe']:>9.4f} {vals['delta']:>+8.4f} {tag}")
    print("=" * 65)
    print(f"\n  Results saved to: {out_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Query Expansion — Bilingual Synonym Expansion")
    subparsers = parser.add_subparsers(dest="mode")

    # Expand mode
    expand_parser = subparsers.add_parser("expand", help="Expand a single query")
    expand_parser.add_argument("--query", required=True, help="Query to expand")
    expand_parser.add_argument("--verbose", action="store_true")

    # Eval mode
    eval_parser = subparsers.add_parser("eval", help="Evaluate BM25 vs BM25+QE on benchmark")
    eval_parser.add_argument("--bm25-dir",    default="models/bm25_v1")
    eval_parser.add_argument("--queries",     default="evaluation/queries.csv")
    eval_parser.add_argument("--qrels",       default="evaluation/qrels.csv")
    eval_parser.add_argument("--output-dir",  default="evaluation/results")

    # Legacy: direct args
    parser.add_argument("--query",   help="Expand a single query (shorthand)")
    parser.add_argument("--eval",    action="store_true", help="Run evaluation")
    parser.add_argument("--bm25-dir",   default="models/bm25_v1")
    parser.add_argument("--queries",    default="evaluation/queries.csv")
    parser.add_argument("--qrels",      default="evaluation/qrels.csv")
    parser.add_argument("--output-dir", default="evaluation/results")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if args.mode == "expand" or args.query:
        query = getattr(args, "query", None)
        expander = QueryExpander()
        expanded = expander.expand(query, verbose=True)
        expansions = expander.get_expansions(query)
        print(f"\nOriginal : {query}")
        print(f"Expanded : {expanded}")
        if expansions:
            print("\nMatched terms:")
            for term, syns in expansions.items():
                print(f"  '{term}' → {syns}")

    elif args.mode == "eval" or args.eval:
        _evaluate_with_expansion(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
