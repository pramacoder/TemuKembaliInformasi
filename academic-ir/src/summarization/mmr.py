"""
Academic IR System — Maximal Marginal Relevance (MMR)
======================================================
Eliminates redundant sentences in extractive summaries by balancing
sentence relevance/centrality score with novelty relative to already selected sentences.
Reorders selected sentences chronologically for coherent narrative flow.
"""

import logging
from typing import List, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .textrank import ScoredSentence
from .schemas import SentenceItem

logger = logging.getLogger(__name__)


def apply_mmr_selection(
    scored_sentences: List[ScoredSentence],
    sentence_vectors: np.ndarray,
    top_k: int = 4,
    lambda_param: float = 0.70,
    chronological_order: bool = True,
) -> List[SentenceItem]:
    """
    Select top-k diverse and relevant sentences using Maximal Marginal Relevance.

    Args:
        scored_sentences: Sentences sorted by initial importance score.
        sentence_vectors: 2D array of sentence representations (e.g. TF-IDF or Embeddings).
        top_k: Target number of sentences in the final summary.
        lambda_param: Weight trade-off between importance (lambda) and novelty (1 - lambda).
        chronological_order: If True, re-sorts selected sentences by their original document order.

    Returns:
        List of SentenceItem models ready for the API response.
    """
    if not scored_sentences:
        return []

    num_candidates = len(scored_sentences)
    k = min(top_k, num_candidates)

    # Pre-calculate pairwise similarity matrix between candidate vectors
    if sentence_vectors.shape[0] == num_candidates:
        pairwise_sim = cosine_similarity(sentence_vectors)
    else:
        # Fallback if dimensions don't match
        pairwise_sim = np.zeros((num_candidates, num_candidates))

    # Map candidate objects to their indices in the candidate pool
    unselected_indices = list(range(num_candidates))
    selected_indices: List[int] = []

    # First sentence is the one with the highest initial score
    first_choice = unselected_indices.pop(0)
    selected_indices.append(first_choice)

    # Greedily pick remaining sentences with MMR
    while len(selected_indices) < k and unselected_indices:
        best_score = -float("inf")
        best_cand_idx = -1
        best_pos_in_unselected = -1

        for i_pos, cand_idx in enumerate(unselected_indices):
            cand_obj = scored_sentences[cand_idx]
            cand_vec_idx = cand_obj.vector_idx

            # Calculate maximum similarity with any already-selected sentence
            max_sim_to_selected = 0.0
            for sel_idx in selected_indices:
                sel_obj = scored_sentences[sel_idx]
                sel_vec_idx = sel_obj.vector_idx
                sim = pairwise_sim[cand_vec_idx, sel_vec_idx]
                if sim > max_sim_to_selected:
                    max_sim_to_selected = sim

            # MMR formula
            mmr_score = (lambda_param * cand_obj.score) - ((1.0 - lambda_param) * max_sim_to_selected)

            if mmr_score > best_score:
                best_score = mmr_score
                best_cand_idx = cand_idx
                best_pos_in_unselected = i_pos

        if best_cand_idx != -1:
            selected_indices.append(best_cand_idx)
            unselected_indices.pop(best_pos_in_unselected)
        else:
            break

    # Gather selected sentence items
    selected_items: List[SentenceItem] = []
    for idx in selected_indices:
        obj = scored_sentences[idx]
        selected_items.append(
            SentenceItem(
                text=obj.text,
                page=obj.page_number,
                score=round(obj.score, 4),
                order_idx=obj.order_idx,
            )
        )

    # Chronological sort so summary reads as coherent prose from beginning to end
    if chronological_order:
        selected_items.sort(key=lambda item: (item.page or 0, item.order_idx))

    return selected_items
