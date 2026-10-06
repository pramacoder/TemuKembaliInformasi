"""
Academic IR System — Evaluation Metrics
=========================================
Precision@K, Recall@K, F1, MAP, NDCG, MRR for retrieval evaluation.

Added in revision:
  - compute_mrr(): Mean Reciprocal Rank (expert plan §21.1)
  - evaluate() now includes MRR in aggregate metrics
"""

import math
import csv
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def precision_at_k(retrieved: list, relevant: set, k: int) -> float:
    """
    Precision@K: fraction of top-K retrieved documents that are relevant.

    Args:
        retrieved: Ordered list of document IDs (ranked by score)
        relevant: Set of relevant document IDs
        k: Cutoff position

    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant)
    return relevant_in_top_k / k


def recall_at_k(retrieved: list, relevant: set, k: int) -> float:
    """
    Recall@K: fraction of relevant documents found in top-K.

    Args:
        retrieved: Ordered list of document IDs
        relevant: Set of relevant document IDs
        k: Cutoff position

    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant)
    return relevant_in_top_k / len(relevant)


def f1_score(precision: float, recall: float) -> float:
    """Compute F1 score from precision and recall."""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def average_precision(retrieved: list, relevant: set) -> float:
    """
    Average Precision for a single query.
    Used as a component of MAP.

    Args:
        retrieved: Ordered list of document IDs
        relevant: Set of relevant document IDs

    Returns:
        Average Precision score
    """
    if not relevant:
        return 0.0

    hits = 0
    sum_precision = 0.0

    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant:
            hits += 1
            sum_precision += hits / (i + 1)

    return sum_precision / len(relevant)


def mean_average_precision(queries_results: list) -> float:
    """
    Mean Average Precision across multiple queries.

    Args:
        queries_results: List of tuples (retrieved_list, relevant_set)

    Returns:
        MAP score
    """
    if not queries_results:
        return 0.0

    aps = [average_precision(ret, rel) for ret, rel in queries_results]
    return sum(aps) / len(aps)


def dcg_at_k(scores: list, k: int) -> float:
    """
    Discounted Cumulative Gain at K.

    Args:
        scores: List of relevance scores in rank order
        k: Cutoff position

    Returns:
        DCG@K score
    """
    dcg = 0.0
    for i, score in enumerate(scores[:k]):
        dcg += score / math.log2(i + 2)  # +2 because i starts at 0
    return dcg


def ndcg_at_k(retrieved: list, relevance_map: dict, k: int) -> float:
    """
    Normalized Discounted Cumulative Gain at K.

    Args:
        retrieved: Ordered list of document IDs
        relevance_map: {document_id: relevance_score} (0, 1, 2, 3)
        k: Cutoff position

    Returns:
        NDCG@K score (0.0 to 1.0)
    """
    # Actual DCG
    actual_scores = [relevance_map.get(doc_id, 0) for doc_id in retrieved[:k]]
    actual_dcg = dcg_at_k(actual_scores, k)

    # Ideal DCG (best possible ranking)
    ideal_scores = sorted(relevance_map.values(), reverse=True)[:k]
    ideal_dcg = dcg_at_k(ideal_scores, k)

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def reciprocal_rank(retrieved: list, relevant: set) -> float:
    """
    Reciprocal Rank for a single query.
    Returns 1/rank of first relevant document found, or 0 if none found.

    Args:
        retrieved: Ordered list of document IDs (ranked by score)
        relevant: Set of relevant document IDs

    Returns:
        Reciprocal Rank score (0.0 to 1.0)
    """
    for rank, doc_id in enumerate(retrieved, 1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(queries_results: list) -> float:
    """
    Mean Reciprocal Rank (MRR) across multiple queries.

    MRR = (1/|Q|) * sum(1/rank_i)

    Measures at what average rank the first relevant document appears.
    Higher is better (1.0 = always returned as rank 1).

    Args:
        queries_results: List of tuples (retrieved_list, relevant_set)

    Returns:
        MRR score (0.0 to 1.0)
    """
    if not queries_results:
        return 0.0
    rrs = [reciprocal_rank(ret, rel) for ret, rel in queries_results]
    return sum(rrs) / len(rrs)


# ─── Evaluation Runner ──────────────────────────────────────────────────

def load_qrels(qrels_path: str) -> dict:
    """
    Load relevance judgments from CSV.

    Format: query_id,document_id,relevance

    Returns:
        {query_id: {document_id: relevance_score}}
    """
    qrels = {}
    with open(qrels_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row['query_id']
            did = row['document_id']
            rel = int(row['relevance'])
            if qid not in qrels:
                qrels[qid] = {}
            qrels[qid][did] = rel
    return qrels


def load_queries(queries_path: str) -> dict:
    """
    Load queries from CSV.

    Format: query_id,query

    Returns:
        {query_id: query_string}
    """
    queries = {}
    with open(queries_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries[row['query_id']] = row['query']
    return queries


def evaluate(search_engine, queries: dict, qrels: dict,
             k_values: list = None) -> dict:
    """
    Run full evaluation suite.

    Args:
        search_engine: SearchEngine instance
        queries: {query_id: query_string}
        qrels: {query_id: {document_id: relevance_score}}
        k_values: List of K values to evaluate (default: [5, 10, 20])

    Returns:
        dict with per-query and aggregate metrics
    """
    if k_values is None:
        k_values = [5, 10, 20]

    results = {
        'per_query': {},
        'aggregate': {},
    }

    all_ap = []
    all_rr = []  # Reciprocal Ranks for MRR

    for qid, query_text in queries.items():
        if qid not in qrels:
            continue

        # Run search
        search_results = search_engine.search(query_text, top_k=max(k_values))
        retrieved = [r['document_id'] for r in search_results]
        relevant = set(doc_id for doc_id, rel in qrels[qid].items() if rel > 0)

        query_metrics = {}

        for k in k_values:
            p = precision_at_k(retrieved, relevant, k)
            r = recall_at_k(retrieved, relevant, k)
            f1 = f1_score(p, r)
            ndcg = ndcg_at_k(retrieved, qrels[qid], k)

            query_metrics[f'P@{k}'] = round(p, 4)
            query_metrics[f'R@{k}'] = round(r, 4)
            query_metrics[f'F1@{k}'] = round(f1, 4)
            query_metrics[f'NDCG@{k}'] = round(ndcg, 4)

        ap = average_precision(retrieved, relevant)
        query_metrics['AP'] = round(ap, 4)
        all_ap.append(ap)

        rr = reciprocal_rank(retrieved, relevant)
        query_metrics['RR'] = round(rr, 4)
        all_rr.append(rr)

        results['per_query'][qid] = query_metrics

    # Aggregate metrics
    if all_ap:
        results['aggregate']['MAP'] = round(sum(all_ap) / len(all_ap), 4)
        results['aggregate']['MRR'] = round(sum(all_rr) / len(all_rr), 4) if all_rr else 0.0
        for k in k_values:
            key_p = f'P@{k}'
            key_r = f'R@{k}'
            key_ndcg = f'NDCG@{k}'
            values_p = [results['per_query'][q].get(key_p, 0) for q in results['per_query']]
            values_r = [results['per_query'][q].get(key_r, 0) for q in results['per_query']]
            values_ndcg = [results['per_query'][q].get(key_ndcg, 0) for q in results['per_query']]

            results['aggregate'][f'Avg_{key_p}'] = round(sum(values_p) / len(values_p), 4) if values_p else 0
            results['aggregate'][f'Avg_{key_r}'] = round(sum(values_r) / len(values_r), 4) if values_r else 0
            results['aggregate'][f'Avg_{key_ndcg}'] = round(sum(values_ndcg) / len(values_ndcg), 4) if values_ndcg else 0

    return results
