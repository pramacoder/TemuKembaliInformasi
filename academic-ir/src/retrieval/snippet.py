"""
Academic IR System — Snippet Generation
==========================================
Extracts relevant text snippets around matching query terms.
"""

import re


def generate_snippet(text: str, query: str, max_length: int = 200,
                     context_words: int = 15, max_chars: int = None) -> str:
    """
    Generate a snippet from text highlighting where query terms appear.

    Args:
        text: Source text to extract snippet from
        query: Original search query
        max_length: Maximum snippet length in characters
        context_words: Number of words to include around match
        max_chars: Alias for max_length

    Returns:
        Snippet string with '...' markers
    """
    if max_chars is not None:
        max_length = max_chars

    if not text or not query:
        return text[:max_length] + "..." if text and len(text) > max_length else (text or "")

    text_lower = text.lower()
    query_terms = query.lower().split()
    words = text.split()

    if not words:
        return ""

    # Find the best position: where the most query terms appear nearby
    best_pos = 0
    best_score = 0

    for i, word in enumerate(words):
        word_lower = word.lower()
        score = 0
        for term in query_terms:
            if term in word_lower:
                score += 2  # exact/partial match at this position
            # Also check nearby words
            for j in range(max(0, i - context_words), min(len(words), i + context_words)):
                if term in words[j].lower():
                    score += 1

        if score > best_score:
            best_score = score
            best_pos = i

    # Extract snippet around best position
    start = max(0, best_pos - context_words)
    end = min(len(words), best_pos + context_words + 1)

    snippet_words = words[start:end]
    snippet = " ".join(snippet_words)

    # Add ellipsis
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(words) else ""

    snippet = f"{prefix}{snippet}{suffix}"

    # Truncate if still too long
    if len(snippet) > max_length:
        snippet = snippet[:max_length - 3] + "..."

    return snippet
