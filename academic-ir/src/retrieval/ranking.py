"""
Academic IR System — Field-Aware Ranking
==========================================
Enhances cosine similarity scores with metadata signals.
"""

import re
import logging

logger = logging.getLogger(__name__)


def compute_title_score(title: str, query: str) -> float:
    """
    Compute how well the query matches the document title.

    Returns a score between 0 and 1.
    """
    if not title or not query:
        return 0.0

    title_lower = title.lower()
    query_terms = query.lower().split()

    if not query_terms:
        return 0.0

    # Count how many query terms appear in the title
    matches = sum(1 for term in query_terms if term in title_lower)

    # Exact match bonus
    if query.lower().strip() in title_lower:
        return 1.0

    return matches / len(query_terms)


def compute_metadata_score(result: dict, query: str) -> float:
    """
    Compute a metadata relevance signal from keywords, abstract, course.

    Returns a score between 0 and 1.
    """
    if not query:
        return 0.0

    query_terms = query.lower().split()
    score = 0.0
    checks = 0

    # Check abstract
    abstract = (result.get('abstract') or '').lower()
    if abstract:
        checks += 1
        abstract_matches = sum(1 for t in query_terms if t in abstract)
        score += abstract_matches / len(query_terms)

    # Check course
    course = (result.get('course') or '').lower()
    if course:
        checks += 1
        course_matches = sum(1 for t in query_terms if t in course)
        score += course_matches / len(query_terms)

    if checks == 0:
        return 0.0

    return score / checks


def rerank(results: list, query: str,
           content_weight: float = 0.60,
           title_weight: float = 0.20,
           metadata_weight: float = 0.20) -> list:
    """
    Re-rank search results using field-aware scoring.

    Final Score = content_weight × cosine_score
               + title_weight × title_match_score
               + metadata_weight × metadata_score

    Args:
        results: List of search result dicts (must have 'score', 'title')
        query: Original search query
        content_weight: Weight for content cosine similarity
        title_weight: Weight for title match
        metadata_weight: Weight for metadata signals

    Returns:
        Re-ranked list of results with 'final_score' added
    """
    if not results:
        return results

    for result in results:
        content_score = result.get('score', 0.0)
        title_score = compute_title_score(result.get('title', ''), query)
        meta_score = compute_metadata_score(result, query)

        final_score = (
            content_weight * content_score +
            title_weight * title_score +
            metadata_weight * meta_score
        )

        result['content_score'] = content_score
        result['title_score'] = title_score
        result['metadata_score'] = meta_score
        result['final_score'] = final_score

    # Re-sort by final score
    results.sort(key=lambda x: x['final_score'], reverse=True)

    # Re-assign ranks
    return results


# Alias for backwards/forward compatibility
rank_results = rerank

