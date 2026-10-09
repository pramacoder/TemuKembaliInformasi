"""
Academic IR System — TextRank Sentence Centrality Solver
========================================================
Implements graph-based ranking for extractive summarization.
Represents sentences as TF-IDF vectors, constructs a cosine similarity
graph, and solves sentence centrality using PageRank / power iteration.
"""

import logging
from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import RawSentence, get_language_stopwords

logger = logging.getLogger(__name__)


class ScoredSentence:
    """A sentence paired with its TextRank centrality score and original position."""
    def __init__(self, raw: RawSentence, score: float, vector_idx: int):
        self.raw = raw
        self.score = float(score)
        self.vector_idx = vector_idx

    @property
    def text(self) -> str:
        return self.raw.text

    @property
    def page_number(self):
        return self.raw.page_number

    @property
    def order_idx(self) -> int:
        return self.raw.order_idx

    def __repr__(self):
        return f"<ScoredSentence score={self.score:.4f} p={self.page_number}: {self.text[:35]}...>"


def compute_textrank_scores(
    candidates: List[RawSentence],
    language: str = "en",
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-5,
    sim_threshold: float = 0.05,
) -> Tuple[List[ScoredSentence], np.ndarray]:
    """
    Compute TextRank centrality scores for a list of candidate sentences.

    Args:
        candidates: List of RawSentence instances.
        language: 'id', 'en', or 'mixed' for language-tailored stopword removal.
        damping: PageRank damping factor (typically 0.85).
        max_iter: Max power iteration steps.
        tol: Convergence tolerance threshold.
        sim_threshold: Minimum cosine similarity to form an edge in the graph.

    Returns:
        Tuple of (scored_sentences, tfidf_sentence_matrix)
    """
    n = len(candidates)
    if n == 0:
        return [], np.zeros((0, 0))

    if n == 1:
        return [ScoredSentence(candidates[0], score=1.0, vector_idx=0)], np.ones((1, 1))

    # 1. Vectorize sentences using TF-IDF
    stopwords = list(get_language_stopwords(language))
    vectorizer = TfidfVectorizer(
        stop_words=stopwords if stopwords else None,
        min_df=1,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-zA-Z0-9_\-\.]{2,}\b",
    )

    sentence_texts = [c.text for c in candidates]
    try:
        tfidf_matrix = vectorizer.fit_transform(sentence_texts).toarray()
    except Exception as exc:
        logger.warning(f"TF-IDF vectorizer fallback for TextRank: {exc}")
        # Fallback with simpler character/word settings
        vectorizer = TfidfVectorizer(stop_words=None, min_df=1)
        tfidf_matrix = vectorizer.fit_transform(sentence_texts).toarray()

    # 2. Compute pairwise Cosine Similarity matrix (Adjacency Matrix)
    sim_matrix = cosine_similarity(tfidf_matrix)

    # Eliminate self-loops
    np.fill_diagonal(sim_matrix, 0.0)

    # Zero out weak noise edges
    sim_matrix[sim_matrix < sim_threshold] = 0.0

    # 3. Solve PageRank Centrality using Power Iteration
    # Row normalize to obtain transition probability matrix
    row_sums = sim_matrix.sum(axis=1)
    
    # Handle isolated nodes (row_sum == 0)
    trans_matrix = np.zeros_like(sim_matrix)
    for i in range(n):
        if row_sums[i] > 0:
            trans_matrix[i, :] = sim_matrix[i, :] / row_sums[i]
        else:
            trans_matrix[i, :] = 1.0 / n

    # Power iteration: v = (1 - d)/n + d * trans_matrix.T @ v
    scores = np.ones(n) / n
    for _ in range(max_iter):
        next_scores = (1.0 - damping) / n + damping * (trans_matrix.T @ scores)
        if np.linalg.norm(next_scores - scores, 1) < tol:
            scores = next_scores
            break
        scores = next_scores

    # Normalize scores to [0, 1] for intuitive display
    max_s = np.max(scores)
    if max_s > 0:
        norm_scores = scores / max_s
    else:
        norm_scores = scores

    scored_list = [
        ScoredSentence(candidates[i], norm_scores[i], vector_idx=i)
        for i in range(n)
    ]

    # Sort descending by centrality score
    scored_list.sort(key=lambda s: s.score, reverse=True)

    return scored_list, tfidf_matrix
