"""
Academic IR System — Deduplication
====================================
SHA-256 exact duplicate detection + near-duplicate heuristics.
"""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            sha256.update(block)
    return sha256.hexdigest()


def check_exact_duplicate(sha256: str, db) -> dict:
    """
    Check if a file with the same SHA-256 exists in the database.

    Returns:
        dict with 'is_duplicate' (bool) and 'existing_id' (str or None)
    """
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT document_id FROM documents WHERE sha256 = ?",
            (sha256,)
        ).fetchone()
        if row:
            return {'is_duplicate': True, 'existing_id': row['document_id']}
        return {'is_duplicate': False, 'existing_id': None}
    finally:
        conn.close()


def check_near_duplicate(title: str, authors: str, year: int,
                         doi: str, db) -> dict:
    """
    Heuristic near-duplicate check based on metadata.

    Checks for:
    1. Same DOI (strongest signal)
    2. Same normalized title + authors + year

    Returns:
        dict with 'is_duplicate' (bool), 'existing_id' (str or None),
        'match_type' (str or None)
    """
    conn = db.get_connection()
    try:
        # Check DOI match first (strongest signal)
        if doi:
            row = conn.execute(
                "SELECT document_id FROM documents WHERE doi = ? AND doi IS NOT NULL",
                (doi,)
            ).fetchone()
            if row:
                return {
                    'is_duplicate': True,
                    'existing_id': row['document_id'],
                    'match_type': 'DOI'
                }

        # Check normalized title + year
        if title:
            normalized_title = title.strip().lower()
            row = conn.execute(
                "SELECT document_id FROM documents "
                "WHERE LOWER(TRIM(title)) = ? AND year = ?",
                (normalized_title, year)
            ).fetchone()
            if row:
                return {
                    'is_duplicate': True,
                    'existing_id': row['document_id'],
                    'match_type': 'TITLE_YEAR'
                }

        return {'is_duplicate': False, 'existing_id': None, 'match_type': None}
    finally:
        conn.close()
