#!/usr/bin/env python3
"""
Academic IR System — Statistical Significance Testing
======================================================
Performs Wilcoxon signed-rank test between TF-IDF and BM25 on per-query scores.

Addresses audit findings:
  - Section 3.1: Klaim "signifikan" tanpa statistical significance test
  - Section 4:   Interpretasi MRR yang tidak tepat
  - Section 32:  Checklist — statistical significance test dan MRR distribution

Produces:
  - evaluation/results/significance_test.json
    Contains: p-value, effect size, confidence interval, per-query scores,
              MRR rank distribution, dan interpretation.

Usage:
    python scripts/statistical_significance.py
    python scripts/statistical_significance.py --metric NDCG@10
    python scripts/statistical_significance.py --report evaluation/results/
"""

import sys
import json
import logging
import argparse
import math
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("significance_test")


# ─── Statistical Functions (No extra deps beyond scipy) ─────────────────────

def wilcoxon_signed_rank(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Wilcoxon signed-rank test: non-parametric paired test.
    Tests H0: median(x - y) == 0.

    Returns (statistic, p_value).
    Falls back to scipy if available, else manual implementation.
    """
    try:
        from scipy.stats import wilcoxon
        stat, p = wilcoxon(x, y, alternative="two-sided", zero_method="wilcox")
        return float(stat), float(p)
    except ImportError:
        logger.warning("scipy not available, using manual Wilcoxon approximation.")
        return _wilcoxon_manual(x, y)


def _wilcoxon_manual(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Manual Wilcoxon signed-rank test with normal approximation (for large N).
    Reference: Conover (1999) Practical Nonparametric Statistics.
    """
    differences = [xi - yi for xi, yi in zip(x, y)]
    nonzero_diffs = [(abs(d), d) for d in differences if d != 0]
    n = len(nonzero_diffs)

    if n == 0:
        return 0.0, 1.0

    # Rank absolute differences
    sorted_diffs = sorted(nonzero_diffs, key=lambda t: t[0])
    ranks = {}
    i = 0
    while i < len(sorted_diffs):
        j = i
        while j < len(sorted_diffs) - 1 and sorted_diffs[j][0] == sorted_diffs[j+1][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1

    W_plus = sum(ranks[k] for k, (_, d) in enumerate(sorted_diffs) if d > 0)

    # Normal approximation
    mean_W = n * (n + 1) / 4
    var_W = n * (n + 1) * (2 * n + 1) / 24
    std_W = math.sqrt(var_W)

    if std_W == 0:
        return W_plus, 1.0

    z = (W_plus - mean_W) / std_W
    # Two-tailed p-value from normal approximation
    p = 2 * (1 - _normal_cdf(abs(z)))
    return W_plus, p


def _normal_cdf(x: float) -> float:
    """Standard normal CDF using math.erf."""
    return (1 + math.erf(x / math.sqrt(2))) / 2


def rank_biserial_r(x: List[float], y: List[float]) -> float:
    """
    Effect size: rank-biserial correlation r for Wilcoxon test.
    r = 1 - (2 * W_minus) / (n * (n+1) / 2)
    Range: -1 to +1. |r| > 0.5 = large effect.
    """
    differences = [xi - yi for xi, yi in zip(x, y)]
    nonzero_diffs = [(abs(d), d) for d in differences if d != 0]
    n = len(nonzero_diffs)
    if n == 0:
        return 0.0

    sorted_diffs = sorted(nonzero_diffs, key=lambda t: t[0])
    ranks = {}
    i = 0
    while i < len(sorted_diffs):
        j = i
        while j < len(sorted_diffs) - 1 and sorted_diffs[j][0] == sorted_diffs[j+1][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1

    W_plus  = sum(ranks[k] for k, (_, d) in enumerate(sorted_diffs) if d > 0)
    W_minus = sum(ranks[k] for k, (_, d) in enumerate(sorted_diffs) if d < 0)
    max_W = n * (n + 1) / 2

    r = (W_plus - W_minus) / max_W
    return round(float(r), 4)


def bootstrap_ci(x: List[float], y: List[float],
                 n_boot: int = 5000, confidence: float = 0.95) -> Tuple[float, float]:
    """
    95% bootstrap confidence interval for the mean difference (x - y).
    """
    import random
    random.seed(42)
    diffs = [xi - yi for xi, yi in zip(x, y)]
    n = len(diffs)
    boot_means = []
    for _ in range(n_boot):
        sample = [random.choice(diffs) for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo_idx = int((1 - confidence) / 2 * n_boot)
    hi_idx = int((1 - (1 - confidence) / 2) * n_boot)
    return round(boot_means[lo_idx], 4), round(boot_means[hi_idx], 4)


def mrr_rank_distribution(rr_values: List[float]) -> Dict[str, str]:
    """
    From a list of reciprocal rank values, compute the distribution of
    the position of the first relevant document.

    RR = 1/rank => rank = round(1/RR) when RR > 0.
    """
    n = len(rr_values)
    dist = {"rank_1": 0, "rank_2": 0, "rank_3": 0, "rank_gt3": 0, "not_found": 0}
    for rr in rr_values:
        if rr == 0.0:
            dist["not_found"] += 1
        elif rr >= 1.0:
            dist["rank_1"] += 1
        elif rr >= 0.5:
            dist["rank_2"] += 1
        elif rr >= 1/3:
            dist["rank_3"] += 1
        else:
            dist["rank_gt3"] += 1
    return {k: f"{v}/{n} ({100*v/n:.1f}%)" for k, v in dist.items()}


def interpret_p_value(p: float) -> str:
    if p < 0.001:
        return "p < 0.001 — Perbedaan sangat kuat secara statistik."
    elif p < 0.01:
        return "p < 0.01 — Perbedaan kuat secara statistik."
    elif p < 0.05:
        return "p < 0.05 — Perbedaan signifikan secara statistik (α=0.05)."
    elif p < 0.10:
        return "p < 0.10 -- Terdapat indikasi perbedaan, namun tidak signifikan pada alpha=0.05."
    else:
        return "p >= 0.10 -- Tidak terdapat bukti statistik yang cukup untuk menyatakan perbedaan."


def interpret_effect_size(r: float) -> str:
    ar = abs(r)
    if ar < 0.1:
        return "Effect size: negligible (|r| < 0.1)"
    elif ar < 0.3:
        return "Effect size: small (0.1 <= |r| < 0.3)"
    elif ar < 0.5:
        return "Effect size: medium (0.3 <= |r| < 0.5)"
    else:
        return "Effect size: large (|r| >= 0.5)"


def generate_claim_guidance(p: float, bm25_mean: float, tfidf_mean: float, metric: str) -> str:
    """Generate the correct claim wording for the report based on test results."""
    direction = "lebih tinggi" if bm25_mean > tfidf_mean else "lebih rendah"
    if p < 0.05:
        return (
            f"BM25 memperoleh {metric} yang secara statistik lebih tinggi daripada TF-IDF "
            f"(BM25={bm25_mean:.4f}, TF-IDF={tfidf_mean:.4f}; Wilcoxon p={p:.4f})."
        )
    else:
        return (
            f"BM25 memperoleh nilai {metric} yang {direction} daripada TF-IDF "
            f"(BM25={bm25_mean:.4f}, TF-IDF={tfidf_mean:.4f}), namun perbedaan ini "
            f"tidak mencapai signifikansi statistik pada alpha=0.05 (Wilcoxon p={p:.4f}). "
            f"Klaim 'signifikan' tidak boleh digunakan."
        )


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Statistical Significance Test: TF-IDF vs BM25")
    parser.add_argument("--tfidf-report", default="evaluation/results/baseline_tfidf_report.json")
    parser.add_argument("--bm25-report",  default="evaluation/results/bm25_report.json")
    parser.add_argument("--output-dir",   default="evaluation/results")
    parser.add_argument("--metric",       default="NDCG@10",
                        help="Primary metric for significance test (default: NDCG@10)")
    args = parser.parse_args()

    tfidf_path = PROJECT_ROOT / args.tfidf_report
    bm25_path  = PROJECT_ROOT / args.bm25_report
    out_dir    = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not tfidf_path.exists() or not bm25_path.exists():
        logger.error(
            "Benchmark reports not found. Run scripts/run_full_benchmark.py first.\n"
            f"  Expected: {tfidf_path}\n  Expected: {bm25_path}"
        )
        sys.exit(1)

    with open(tfidf_path, encoding="utf-8") as f:
        tfidf_report = json.load(f)
    with open(bm25_path, encoding="utf-8") as f:
        bm25_report = json.load(f)

    tfidf_per_q = tfidf_report.get("per_query", {})
    bm25_per_q  = bm25_report.get("per_query", {})

    common_queries = sorted(set(tfidf_per_q.keys()) & set(bm25_per_q.keys()))
    if not common_queries:
        logger.error("No common queries found between the two reports.")
        sys.exit(1)

    logger.info(f"Running significance test on {len(common_queries)} queries using metric: {args.metric}")

    # ── Collect per-query scores ────────────────────────────────────────────
    primary_metric = args.metric  # e.g., "NDCG@10"

    tfidf_scores_ndcg = [tfidf_per_q[q].get(primary_metric, 0.0) for q in common_queries]
    bm25_scores_ndcg  = [bm25_per_q[q].get(primary_metric, 0.0) for q in common_queries]
    tfidf_scores_ap   = [tfidf_per_q[q].get("AP", 0.0) for q in common_queries]
    bm25_scores_ap    = [bm25_per_q[q].get("AP", 0.0) for q in common_queries]
    tfidf_scores_rr   = [tfidf_per_q[q].get("RR", 0.0) for q in common_queries]
    bm25_scores_rr    = [bm25_per_q[q].get("RR", 0.0) for q in common_queries]
    tfidf_scores_p10  = [tfidf_per_q[q].get("P@10", 0.0) for q in common_queries]
    bm25_scores_p10   = [bm25_per_q[q].get("P@10", 0.0) for q in common_queries]

    # ── Wilcoxon tests for multiple metrics ────────────────────────────────
    tests = {}
    for metric_key, tfidf_s, bm25_s in [
        (primary_metric, tfidf_scores_ndcg, bm25_scores_ndcg),
        ("AP (MAP component)", tfidf_scores_ap, bm25_scores_ap),
        ("P@10", tfidf_scores_p10, bm25_scores_p10),
        ("RR (MRR component)", tfidf_scores_rr, bm25_scores_rr),
    ]:
        stat, p = wilcoxon_signed_rank(tfidf_s, bm25_s)
        r = rank_biserial_r(tfidf_s, bm25_s)
        ci_lo, ci_hi = bootstrap_ci(bm25_s, tfidf_s)  # BM25 - TF-IDF
        tfidf_mean = sum(tfidf_s) / len(tfidf_s)
        bm25_mean  = sum(bm25_s) / len(bm25_s)

        tests[metric_key] = {
            "tfidf_mean":         round(tfidf_mean, 4),
            "bm25_mean":          round(bm25_mean, 4),
            "mean_difference":    round(bm25_mean - tfidf_mean, 4),
            "relative_improvement_pct": round(
                100 * (bm25_mean - tfidf_mean) / tfidf_mean, 2
            ) if tfidf_mean > 0 else None,
            "wilcoxon_statistic": round(stat, 4),
            "p_value":            round(p, 6),
            "p_interpretation":   interpret_p_value(p),
            "effect_size_r":      r,
            "effect_interpretation": interpret_effect_size(r),
            "ci_95_difference":   [ci_lo, ci_hi],
            "claim_guidance":     generate_claim_guidance(p, bm25_mean, tfidf_mean, metric_key),
        }

    # ── MRR Rank Distribution ───────────────────────────────────────────────
    mrr_dist = {
        "tfidf": mrr_rank_distribution(tfidf_scores_rr),
        "bm25":  mrr_rank_distribution(bm25_scores_rr),
        "interpretation": (
            "Distribusi ini menunjukkan posisi dokumen relevan pertama yang ditemukan. "
            "MRR tidak dapat diinterpretasikan langsung sebagai rata-rata rank "
            "karena E[1/R] ≠ 1/E[R]. Gunakan distribusi ini untuk menyatakan "
            "posisi dokumen relevan pertama secara deskriptif."
        )
    }

    # ── Per-query comparison table ──────────────────────────────────────────
    per_query_comparison = []
    for q in common_queries:
        t = tfidf_per_q[q]
        b = bm25_per_q[q]
        ndcg_diff = b.get(primary_metric, 0) - t.get(primary_metric, 0)
        per_query_comparison.append({
            "query_id": q,
            f"tfidf_{primary_metric}": t.get(primary_metric, 0.0),
            f"bm25_{primary_metric}":  b.get(primary_metric, 0.0),
            "difference":             round(ndcg_diff, 4),
            "winner":                 "BM25" if ndcg_diff > 0.001 else ("TF-IDF" if ndcg_diff < -0.001 else "TIE"),
        })

    n_bm25_wins = sum(1 for r in per_query_comparison if r["winner"] == "BM25")
    n_tfidf_wins = sum(1 for r in per_query_comparison if r["winner"] == "TF-IDF")
    n_ties = sum(1 for r in per_query_comparison if r["winner"] == "TIE")

    # ── Full Report ─────────────────────────────────────────────────────────
    primary_result = tests[primary_metric]
    report = {
        "test_configuration": {
            "method": "Wilcoxon signed-rank test (two-tailed)",
            "primary_metric": primary_metric,
            "n_queries": len(common_queries),
            "alpha": 0.05,
            "effect_size_measure": "Rank-biserial correlation r",
            "ci_method": "Bootstrap (5000 samples, 95% CI)",
        },
        "primary_test_result": {
            "metric": primary_metric,
            **primary_result,
        },
        "all_metric_tests": tests,
        "per_query_summary": {
            "bm25_wins": n_bm25_wins,
            "tfidf_wins": n_tfidf_wins,
            "ties": n_ties,
            "per_query_detail": per_query_comparison,
        },
        "mrr_rank_distribution": mrr_dist,
        "report_writing_guidance": {
            "RULE_1": "Jika p >= 0.05: JANGAN gunakan kata 'signifikan'. Gunakan: 'BM25 memperoleh nilai evaluasi yang lebih tinggi daripada TF-IDF.'",
            "RULE_2": "Jika p < 0.05: Boleh menyatakan 'perbedaan ini signifikan secara statistik (Wilcoxon p=...)'.",
            "RULE_3": "MRR TIDAK boleh diinterpretasikan sebagai rata-rata rank. Gunakan mrr_rank_distribution untuk menjelaskan posisi dokumen relevan.",
            "RULE_4": "Selalu laporkan: mean kedua model, p-value, effect size r, dan 95% CI.",
        }
    }

    out_path = out_dir / "significance_test.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ── Console Summary ─────────────────────────────────────────────────────
    p = tests[primary_metric]["p_value"]
    r = tests[primary_metric]["effect_size_r"]
    ci = tests[primary_metric]["ci_95_difference"]

    print("\n" + "=" * 72)
    print("  STATISTICAL SIGNIFICANCE TEST: TF-IDF vs BM25")
    print("=" * 72)
    print(f"  Primary metric   : {primary_metric}")
    print(f"  N queries        : {len(common_queries)}")
    print(f"  TF-IDF mean      : {tests[primary_metric]['tfidf_mean']:.4f}")
    print(f"  BM25 mean        : {tests[primary_metric]['bm25_mean']:.4f}")
    print(f"  Mean difference  : {tests[primary_metric]['mean_difference']:+.4f}")
    print(f"  Relative improve : {tests[primary_metric]['relative_improvement_pct']:+.2f}%")
    print(f"  Wilcoxon p-value : {p:.6f}")
    print(f"  Effect size r    : {r:.4f}")
    print(f"  95% CI (BM25-TF) : [{ci[0]:.4f}, {ci[1]:.4f}]")
    print("-" * 72)
    print(f"  Interpretation   : {interpret_p_value(p)}")
    print(f"  Effect size      : {interpret_effect_size(r)}")
    print("-" * 72)
    print("  Query wins:")
    print(f"    BM25 wins  : {n_bm25_wins}/{len(common_queries)}")
    print(f"    TF-IDF wins: {n_tfidf_wins}/{len(common_queries)}")
    print(f"    Ties       : {n_ties}/{len(common_queries)}")
    print("-" * 72)
    print("  MRR Rank Distribution (BM25):")
    for k, v in mrr_dist["bm25"].items():
        print(f"    {k:12s}: {v}")
    print("=" * 72)
    print(f"\n  CLAIM GUIDANCE:\n  {tests[primary_metric]['claim_guidance']}")
    print(f"\n  Full report saved to: {out_path}\n")


if __name__ == "__main__":
    main()
