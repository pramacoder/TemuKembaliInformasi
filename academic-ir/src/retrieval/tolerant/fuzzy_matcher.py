"""
Tolerant Retrieval — Fuzzy Term Matcher & Typo Corrector
========================================================
Implements fast Damerau-Levenshtein distance, n-gram filtered vocabulary index,
and frequency-weighted candidate generation with confidence scoring.

Guards (Section 6 & 16 of spec):
- Similarity threshold (default >= 0.82)
- Max candidate count (default <= 3)
- Vocabulary validation against academic corpus
- Technical term protection
- Confidence scoring
"""

from collections import defaultdict
import math
from typing import Dict, List, Optional, Set, Tuple


def damerau_levenshtein(s1: str, s2: str) -> int:
    """
    Computes Damerau-Levenshtein distance between two strings,
    supporting insertions, deletions, substitutions, and transpositions.
    """
    len1, len2 = len(s1), len(s2)
    if not s1:
        return len2
    if not s2:
        return len1

    d = {}
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,        # deletion
                d[(i, j - 1)] + 1,        # insertion
                d[(i - 1, j - 1)] + cost, # substitution
            )
            # Transposition of adjacent characters
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + cost)

    return d[(len1 - 1, len2 - 1)]


def string_similarity(s1: str, s2: str, dist: Optional[int] = None) -> float:
    """Calculates normalized string similarity between 0.0 and 1.0."""
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    if dist is None:
        dist = damerau_levenshtein(s1, s2)
    return max(0.0, 1.0 - (dist / max_len))


def get_bigrams(text: str) -> Set[str]:
    """Extracts character bigrams for fast candidate pre-filtering."""
    if len(text) < 2:
        return {text}
    return {text[i:i + 2] for i in range(len(text) - 1)}


class FuzzyMatcher:
    """
    Indexed vocabulary fuzzy matcher for sub-millisecond typo tolerance.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.82,
        max_candidates: int = 3,
        max_edit_distance: int = 2,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_candidates = max_candidates
        self.max_edit_distance = max_edit_distance

        # Vocabulary storage
        self.vocabulary: Set[str] = set()
        self.term_frequencies: Dict[str, int] = defaultdict(int)

        # Inverted index: length bucket -> list of terms
        self._len_index: Dict[int, List[str]] = defaultdict(list)
        # Inverted index: bigram -> set of terms for rapid candidate pruning
        self._bigram_index: Dict[str, Set[str]] = defaultdict(set)

    def load_vocabulary(self, terms: Dict[str, int] or Set[str] or List[str]):
        """
        Indexes vocabulary terms with optional frequencies.
        """
        if isinstance(terms, dict):
            for t, freq in terms.items():
                self.add_term(t, freq)
        else:
            for t in terms:
                self.add_term(t, 1)

    def add_term(self, term: str, frequency: int = 1):
        """Adds a single term to the vocabulary index."""
        t_clean = term.strip().lower()
        if len(t_clean) < 2:
            return

        is_new = t_clean not in self.vocabulary
        self.vocabulary.add(t_clean)
        self.term_frequencies[t_clean] = max(self.term_frequencies[t_clean], frequency)

        if is_new:
            self._len_index[len(t_clean)].append(t_clean)
            for bg in get_bigrams(t_clean):
                self._bigram_index[bg].add(t_clean)

    def contains(self, term: str) -> bool:
        """Checks if term is in the known vocabulary."""
        return term.strip().lower() in self.vocabulary

    def get_frequency(self, term: str) -> int:
        return self.term_frequencies.get(term.strip().lower(), 0)

    def find_candidates(
        self,
        token: str,
        threshold: Optional[float] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, any]]:
        """
        Finds fuzzy matches for a token, sorted by confidence and frequency.

        Returns list of dicts:
        [
            {
                "candidate": "analisis",
                "distance": 1,
                "similarity": 0.875,
                "confidence": 0.96,
                "frequency": 142
            }
        ]
        """
        token = token.strip().lower()
        if not token:
            return []

        # If exact match exists, return immediately with confidence 1.0
        if token in self.vocabulary:
            return [{
                "candidate": token,
                "distance": 0,
                "similarity": 1.0,
                "confidence": 1.0,
                "frequency": self.term_frequencies.get(token, 1),
            }]

        sim_thresh = threshold if threshold is not None else self.similarity_threshold
        max_k = max_results if max_results is not None else self.max_candidates
        t_len = len(token)

        # 1. Retrieve candidates within length bounds (len +/- max_edit_distance)
        potential_candidates: Set[str] = set()
        for l in range(max(2, t_len - self.max_edit_distance), t_len + self.max_edit_distance + 1):
            potential_candidates.update(self._len_index.get(l, []))

        if not potential_candidates:
            return []

        # 2. Bigram overlap filtering (must share at least 1 bigram for words >= 4 chars)
        token_bigrams = get_bigrams(token)
        if t_len >= 4 and token_bigrams:
            bigram_matches: Set[str] = set()
            for bg in token_bigrams:
                bigram_matches.update(self._bigram_index.get(bg, set()))
            # Intersect with length-filtered candidates
            filtered_candidates = potential_candidates.intersection(bigram_matches)
            # If intersection is non-empty, use it for speed; otherwise fall back to length filter
            if filtered_candidates:
                candidates_to_score = filtered_candidates
            else:
                candidates_to_score = potential_candidates
        else:
            candidates_to_score = potential_candidates

        # 3. Score candidates with Damerau-Levenshtein
        scored = []
        for cand in candidates_to_score:
            dist = damerau_levenshtein(token, cand)
            if dist > self.max_edit_distance:
                continue

            sim = string_similarity(token, cand, dist)
            if sim < sim_thresh:
                continue

            # Calculate confidence score
            # Base confidence from similarity
            conf = sim

            # Bonus 1: first character matches (psycholinguistic commonality of typing errors)
            if token[0] == cand[0]:
                conf += 0.04
            else:
                conf -= 0.05

            # Bonus 2: frequency factor (higher frequency -> more likely intended)
            freq = self.term_frequencies.get(cand, 1)
            freq_bonus = min(0.04, math.log10(max(1, freq)) * 0.015)
            conf += freq_bonus

            # Bonus 3: word length penalty for very short words (less tolerance for short words)
            if t_len <= 3 and dist > 1:
                conf -= 0.15

            conf = max(0.0, min(0.99, conf))

            if conf >= sim_thresh:
                scored.append({
                    "candidate": cand,
                    "distance": dist,
                    "similarity": round(sim, 4),
                    "confidence": round(conf, 4),
                    "frequency": freq,
                })

        # Sort primarily by confidence, secondarily by frequency
        scored.sort(key=lambda x: (x["confidence"], x["frequency"]), reverse=True)
        return scored[:max_k]
