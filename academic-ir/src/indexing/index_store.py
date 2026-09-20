"""
Academic IR System — Index Store
==================================
Save/load index artifacts with versioning metadata.
"""

import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def save_index_metadata(output_dir: str, chunk_count: int,
                        vocab_size: int, corpus_stats: dict = None):
    """
    Save index metadata for reproducibility.

    Args:
        output_dir: Directory where index files are stored
        chunk_count: Number of chunks indexed
        vocab_size: TF-IDF vocabulary size
        corpus_stats: Optional corpus statistics dict
    """
    metadata = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'chunk_count': chunk_count,
        'vocab_size': vocab_size,
        'corpus_stats': corpus_stats,
    }

    path = os.path.join(output_dir, "index_metadata.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"Index metadata saved to {path}")


def load_index_metadata(output_dir: str) -> dict:
    """Load index metadata."""
    path = os.path.join(output_dir, "index_metadata.json")
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
