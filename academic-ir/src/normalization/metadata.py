"""
Academic IR System — Metadata Normalization
=============================================
Normalizes metadata from different sources into the unified schema.
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def normalize_authors(authors) -> str:
    """
    Normalize authors field to a JSON array string.

    Handles:
    - String: "Author A, Author B" → '["Author A", "Author B"]'
    - List: ["Author A", "Author B"] → '["Author A", "Author B"]'
    - None → None
    """
    if authors is None:
        return None
    if isinstance(authors, list):
        return json.dumps(authors)
    if isinstance(authors, str):
        if authors.startswith('['):
            return authors  # already JSON
        # Split by comma or semicolon
        parts = [a.strip() for a in authors.replace(';', ',').split(',')]
        parts = [a for a in parts if a]
        return json.dumps(parts)
    return None


def normalize_keywords(keywords) -> str:
    """Normalize keywords to JSON array string."""
    if keywords is None:
        return None
    if isinstance(keywords, list):
        return json.dumps(keywords)
    if isinstance(keywords, str):
        if keywords.startswith('['):
            return keywords
        parts = [k.strip() for k in keywords.replace(';', ',').split(',')]
        parts = [k for k in parts if k]
        return json.dumps(parts)
    return None


def normalize_year(year) -> int:
    """Extract year from various formats."""
    if year is None:
        return None
    if isinstance(year, int):
        return year if 1900 <= year <= 2100 else None
    if isinstance(year, str):
        # Try to extract 4-digit year
        import re
        match = re.search(r'(19|20)\d{2}', str(year))
        if match:
            return int(match.group())
    return None


def normalize_metadata(raw_metadata: dict, source: str) -> dict:
    """
    Normalize raw metadata from any source into the unified schema.

    Args:
        raw_metadata: Source-specific metadata dict
        source: Source identifier (OCW_UI, CORE, DOAJ, REPOSITORY)

    Returns:
        Normalized metadata dict matching the documents table schema
    """
    normalized = {
        'document_id': raw_metadata.get('document_id'),
        'document_type': raw_metadata.get('document_type'),
        'title': raw_metadata.get('title'),
        'abstract': raw_metadata.get('abstract'),
        'authors': normalize_authors(raw_metadata.get('authors')),
        'institution': raw_metadata.get('institution'),
        'department': raw_metadata.get('department'),
        'course': raw_metadata.get('course'),
        'year': normalize_year(raw_metadata.get('year')),
        'language': raw_metadata.get('language'),
        'language_confidence': raw_metadata.get('language_confidence'),
        'keywords': normalize_keywords(raw_metadata.get('keywords')),
        'source': source,
        'source_url': raw_metadata.get('source_url'),
        'fulltext_url': raw_metadata.get('fulltext_url'),
        'local_path': raw_metadata.get('local_path'),
        'file_type': raw_metadata.get('file_type', 'pdf'),
        'file_size': raw_metadata.get('file_size'),
        'page_count': raw_metadata.get('page_count'),
        'license': raw_metadata.get('license'),
        'sha256': raw_metadata.get('sha256'),
        'doi': raw_metadata.get('doi'),
        'extraction_method': raw_metadata.get('extraction_method'),
        'extraction_status': raw_metadata.get('extraction_status'),
        'collection_status': raw_metadata.get('collection_status', 'DOWNLOADED'),
        'collected_at': raw_metadata.get('collected_at',
                                          datetime.now(timezone.utc).isoformat()),
    }

    return normalized
