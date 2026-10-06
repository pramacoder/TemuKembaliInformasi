"""
Academic IR System — BM25 Loader (lazy singleton)
====================================================
Provides a get_bm25_retriever() function that the FastAPI app can call
without crashing if the BM25 index is not yet built.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_bm25_instance = None
_bm25_tried = False

BM25_INDEX_DIR = Path(__file__).resolve().parent.parent / "models" / "bm25_v1"


def get_bm25_retriever():
    """
    Return the BM25Retriever singleton if its index exists, else None.
    Falls back gracefully so TF-IDF can take over.
    """
    global _bm25_instance, _bm25_tried
    if _bm25_tried:
        return _bm25_instance

    _bm25_tried = True
    index_file = BM25_INDEX_DIR / "bm25_index.pkl"
    if not index_file.exists():
        logger.info(
            f"BM25 index not found at {BM25_INDEX_DIR}. "
            "Run 'python scripts/build_bm25_index.py' to build it."
        )
        return None

    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from src.retrieval.bm25 import BM25Retriever
        _bm25_instance = BM25Retriever()
        _bm25_instance.load(str(BM25_INDEX_DIR))
        logger.info(f"BM25 retriever loaded from {BM25_INDEX_DIR}")
    except Exception as e:
        logger.error(f"Failed to load BM25 retriever: {e}")
        _bm25_instance = None

    return _bm25_instance
