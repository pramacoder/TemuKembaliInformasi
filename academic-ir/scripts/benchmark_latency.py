#!/usr/bin/env python3
"""
Academic IR System — Latency Benchmark
=======================================
Measures latency (cold-start, P50, P95, P99) for TF-IDF and BM25 retrievers
across different values of top_k and candidate_k.

Outputs:
  evaluation/results/latency_benchmark.json
"""

import sys
import time
import json
import logging
import statistics
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.indexing.tfidf import TFIDFIndex
from src.preprocessing.pipeline import PreprocessingPipeline
from src.retrieval.search import SearchEngine
from src.retrieval.bm25 import BM25Retriever
from src.evaluation.metrics import load_queries

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("latency_benchmark")


def benchmark_engine(engine_name: str, search_fn, sample_queries: list, top_k_list=[5, 10, 20, 50], candidate_k_list=[100, 200, 500]):
    logger.info(f"\n--- Benchmarking {engine_name} ---")

    # 1. Warm-up
    for q in sample_queries[:3]:
        search_fn(q, top_k=10)

    results = {
        "engine": engine_name,
        "configurations": []
    }

    # Test baseline top_k=10, candidate_k=500 for latency percentiles
    latencies = []
    for _ in range(3):  # 3 passes over all queries
        for q in sample_queries:
            t0 = time.perf_counter()
            search_fn(q, top_k=10, candidate_k=500)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)  # ms

    latencies_sorted = sorted(latencies)
    p50 = float(np.percentile(latencies_sorted, 50))
    p95 = float(np.percentile(latencies_sorted, 95))
    p99 = float(np.percentile(latencies_sorted, 99))
    mean_lat = float(statistics.mean(latencies_sorted))

    results["summary_p50_ms"] = round(p50, 2)
    results["summary_p95_ms"] = round(p95, 2)
    results["summary_p99_ms"] = round(p99, 2)
    results["summary_mean_ms"] = round(mean_lat, 2)

    logger.info(f"{engine_name} Latency: P50={p50:.2f}ms | P95={p95:.2f}ms | P99={p99:.2f}ms | Mean={mean_lat:.2f}ms")

    # Matrix benchmark across candidate_k and top_k
    for cand_k in candidate_k_list:
        for top_k in top_k_list:
            sub_lat = []
            for q in sample_queries[:10]:
                t0 = time.perf_counter()
                search_fn(q, top_k=top_k, candidate_k=cand_k)
                t1 = time.perf_counter()
                sub_lat.append((t1 - t0) * 1000.0)

            results["configurations"].append({
                "candidate_k": cand_k,
                "top_k": top_k,
                "mean_ms": round(statistics.mean(sub_lat), 2),
                "p95_ms": round(float(np.percentile(sub_lat, 95)), 2)
            })

    return results


def main():
    db_file = PROJECT_ROOT / "database" / "academic_ir.db"
    db = Database(str(db_file))
    queries_dict = load_queries(str(PROJECT_ROOT / "evaluation" / "queries.csv"))
    query_texts = list(queries_dict.values())

    out_file = PROJECT_ROOT / "evaluation" / "results" / "latency_benchmark.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    benchmark_data = {}

    # 1. Cold start TF-IDF
    t_load_start = time.perf_counter()
    tfidf_index = TFIDFIndex()
    tfidf_index.load(str(PROJECT_ROOT / "models"))
    pipeline = PreprocessingPipeline(default_language="id")
    tfidf_engine = SearchEngine(tfidf_index, db, pipeline)
    tfidf_first_q = time.perf_counter()
    tfidf_engine.search(query_texts[0], top_k=10)
    t_load_end = time.perf_counter()
    tfidf_cold_ms = (t_load_end - t_load_start) * 1000.0

    # 2. Cold start BM25
    b_load_start = time.perf_counter()
    bm25_engine = BM25Retriever()
    bm25_engine.load(str(PROJECT_ROOT / "models" / "bm25_v1"))
    bm25_first_q = time.perf_counter()
    bm25_engine.search(query_texts[0], top_k=10)
    b_load_end = time.perf_counter()
    bm25_cold_ms = (b_load_end - b_load_start) * 1000.0

    # 3. Benchmark TF-IDF
    benchmark_data["tfidf"] = benchmark_engine(
        "TF-IDF (VSM)",
        lambda q, top_k=10, candidate_k=500: tfidf_engine.search(q, top_k=top_k, candidate_k=candidate_k),
        query_texts
    )
    benchmark_data["tfidf"]["cold_start_ms"] = round(tfidf_cold_ms, 2)

    # 4. Benchmark BM25
    benchmark_data["bm25"] = benchmark_engine(
        "BM25 (Okapi BM25)",
        lambda q, top_k=10, candidate_k=500: bm25_engine.search(q, top_k=top_k, candidate_k=candidate_k),
        query_texts
    )
    benchmark_data["bm25"]["cold_start_ms"] = round(bm25_cold_ms, 2)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)

    print("\n" + "=" * 70)
    print("             LATENCY BENCHMARK SUMMARY (ms)")
    print("=" * 70)
    print(f"{'Engine':<20} {'Cold Start':<14} {'P50 (ms)':<12} {'P95 (ms)':<12} {'P99 (ms)':<12}")
    print("-" * 70)
    print(f"{'TF-IDF':<20} {tfidf_cold_ms:<14.2f} {benchmark_data['tfidf']['summary_p50_ms']:<12.2f} {benchmark_data['tfidf']['summary_p95_ms']:<12.2f} {benchmark_data['tfidf']['summary_p99_ms']:<12.2f}")
    print(f"{'BM25':<20} {bm25_cold_ms:<14.2f} {benchmark_data['bm25']['summary_p50_ms']:<12.2f} {benchmark_data['bm25']['summary_p95_ms']:<12.2f} {benchmark_data['bm25']['summary_p99_ms']:<12.2f}")
    print("=" * 70)
    print(f"Detailed latency benchmark saved to: {out_file}\n")


if __name__ == "__main__":
    main()
