"""
Academic IR System — Tokenizer
===============================
Simple whitespace tokenizer with token validation.
"""

import re


def tokenize(text: str, min_length: int = 2) -> list:
    """
    Tokenize cleaned text into a list of tokens.

    Args:
        text: Cleaned text string (already lowercased and cleaned)
        min_length: Minimum token length to keep

    Returns:
        List of token strings
    """
    if not text:
        return []

    # Split on whitespace
    tokens = text.split()

    # Filter by minimum length
    if min_length > 1:
        tokens = [t for t in tokens if len(t) >= min_length]

    return tokens


def detokenize(tokens: list) -> str:
    """Join tokens back into a string."""
    return " ".join(tokens)
