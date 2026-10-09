"""
Academic IR System — Document-Level Aggregation
=================================================
Aggregates chunk-level retrieval results into document-level results.

Problem solved:
  Without aggregation, a single long document can dominate the SERP with
  dozens of fragments (e.g., Thesis A chunks 12-18 occupying ranks 1-7).
  This module groups chunks by document_id and computes a single document score
  using one of three strategies:
    - "max"     : document_score = max(chunk_scores)
    - "max+2nd" : document_score = max + lambda * second_best (default)
    - "topN_avg": document_score = weighted avg of top-N chunk scores

Reference: expert plan §8 — Document Aggregation
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Lambda weight for second-best chunk in "max+2nd" strategy
SECOND_BEST_LAMBDA = 0.3

# Number of top chunks to average in "topN_avg" strategy
TOP_N_AVG = 3


def aggregate_by_document(
    chunk_results: list,
    strategy: str = "max+2nd",
) -> list:
    """
    Group chunk-level results by document_id and compute a document-level score.

    Args:
        chunk_results: List of chunk-level result dicts, each must have:
            - chunk_id, document_id, score
            - page_start, page_end
            - title, document_type, authors, year, source, institution,
              course, language, source_url, local_path, raw_text, snippet
        strategy: Aggregation strategy — one of:
            "max"     : document score = max chunk score
            "max+2nd" : document score = max + LAMBDA * second_best chunk score
            "topN_avg": document score = weighted average of top-N chunk scores

    Returns:
        List of document-level result dicts sorted by document_score descending.
        Each dict contains:
            - document_id, document_score, aggregation_strategy
            - best_chunk_id, best_page_start, best_page_end
            - matched_chunks: list of (chunk_id, score, page_start, page_end)
            - title, document_type, authors, year, source, institution, etc.
            - snippet: from the best-scoring chunk
    """
    if not chunk_results:
        return []

    # Group chunks by document_id
    doc_chunks: dict[str, list] = defaultdict(list)
    for chunk in chunk_results:
        doc_id = chunk.get("document_id")
        if doc_id:
            doc_chunks[doc_id].append(chunk)

    aggregated = []
    for doc_id, chunks in doc_chunks.items():
        # Sort chunks within document by score descending
        chunks_sorted = sorted(chunks, key=lambda c: c.get("score", 0.0), reverse=True)

        scores = [c.get("score", 0.0) for c in chunks_sorted]
        best_chunk = chunks_sorted[0]

        # Compute document score based on strategy
        if strategy == "max":
            doc_score = scores[0]

        elif strategy == "max+2nd":
            doc_score = scores[0]
            if len(scores) >= 2:
                doc_score += SECOND_BEST_LAMBDA * scores[1]

        elif strategy == "topN_avg":
            top_n_scores = scores[:TOP_N_AVG]
            # Weighted average: weight[i] = 1 / (i+1)
            weights = [1.0 / (i + 1) for i in range(len(top_n_scores))]
            total_weight = sum(weights)
            doc_score = sum(s * w for s, w in zip(top_n_scores, weights)) / total_weight if total_weight > 0 else 0.0

        else:
            logger.warning(f"Unknown aggregation strategy '{strategy}', falling back to 'max'.")
            doc_score = scores[0]

        # Build matched_chunks summary (up to 5)
        matched_chunks = [
            {
                "chunk_id": c.get("chunk_id"),
                "score": round(c.get("score", 0.0), 6),
                "page_start": c.get("page_start"),
                "page_end": c.get("page_end"),
            }
            for c in chunks_sorted[:5]
        ]

        aggregated.append({
            # Scores & strategy
            "document_id": doc_id,
            "document_score": round(doc_score, 6),
            "aggregation_strategy": strategy,
            "chunk_count": len(chunks),

            # Best evidence
            "best_chunk_id": best_chunk.get("chunk_id"),
            "best_page_start": best_chunk.get("page_start"),
            "best_page_end": best_chunk.get("page_end"),
            "matched_chunks": matched_chunks,
            "matched_pages": sorted(list(set(c.get("page_start") for c in chunks if c.get("page_start") is not None))),

            # Document metadata (from best chunk)
            "title": best_chunk.get("title", ""),
            "document_type": best_chunk.get("document_type", ""),
            "authors": best_chunk.get("authors", ""),
            "year": best_chunk.get("year"),
            "source": best_chunk.get("source", ""),
            "institution": best_chunk.get("institution", ""),
            "course": best_chunk.get("course", ""),
            "language": best_chunk.get("language", ""),
            "source_url": best_chunk.get("source_url", ""),
            "local_path": best_chunk.get("local_path", ""),
            "abstract": best_chunk.get("abstract", ""),
            "keywords": best_chunk.get("keywords", ""),
            "page_count": best_chunk.get("page_count"),

            # Evidence snippet from best-scoring chunk
            "snippet": best_chunk.get("snippet", best_chunk.get("raw_text", "")[:200]),

            # UI-backward-compat aliases
            "score": round(doc_score, 6),
            "page": best_chunk.get("page_start"),
            "page_start": best_chunk.get("page_start"),
            "page_end": best_chunk.get("page_end"),
            "chunk_id": best_chunk.get("chunk_id"),
        })

    # Sort by document_score descending
    aggregated.sort(key=lambda d: d["document_score"], reverse=True)

    # Add final rank
    for rank, doc in enumerate(aggregated, 1):
        doc["rank"] = rank

    logger.debug(
        f"Aggregated {len(chunk_results)} chunks -> {len(aggregated)} documents "
        f"using strategy='{strategy}'"
    )
    return aggregated


def compare_strategies(chunk_results: list) -> dict:
    """
    Run all three aggregation strategies on the same chunk_results
    and return all results for benchmarking / ablation study.

    Returns:
        {
            "max": [...document results...],
            "max+2nd": [...document results...],
            "topN_avg": [...document results...],
        }
    """
    return {
        "max": aggregate_by_document(chunk_results, strategy="max"),
        "max+2nd": aggregate_by_document(chunk_results, strategy="max+2nd"),
        "topN_avg": aggregate_by_document(chunk_results, strategy="topN_avg"),
    }
