"""
Academic IR System — Enhanced TF-IDF Index Builder
===================================================
Builds TF-IDF index from preprocessed chunks with bigram support.
"""

import os
import logging
import joblib
import scipy.sparse
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


class TFIDFIndex:
    """
    TF-IDF index builder with enhanced parameters.

    Key improvements over the original:
    - ngram_range=(1, 2) for bigram support
    - sublinear_tf=True for log-normalized term frequency
    - min_df/max_df to filter very rare / very common terms
    """

    def __init__(self, ngram_range=(1, 2), sublinear_tf=True,
                 min_df=2, max_df=0.95):
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            sublinear_tf=sublinear_tf,
            min_df=min_df,
            max_df=max_df,
        )
        self.tfidf_matrix = None
        self.chunk_ids = []
        self.is_fitted = False

    def build(self, chunks: list) -> dict:
        """
        Build the TF-IDF index from preprocessed chunks.

        Args:
            chunks: List of dicts with at minimum 'chunk_id' and 'clean_text'.
        """
        if not chunks:
            logger.error("No chunks provided for indexing.")
            return {}

        self.chunk_ids = [c['chunk_id'] for c in chunks]
        corpus = [c['clean_text'] for c in chunks]

        logger.info(f"Building TF-IDF index from {len(corpus)} chunks...")
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True

        vocab_size = len(self.vectorizer.vocabulary_)
        density = self.tfidf_matrix.nnz / (self.tfidf_matrix.shape[0] * self.tfidf_matrix.shape[1]) if self.tfidf_matrix.shape[0] * self.tfidf_matrix.shape[1] > 0 else 0
        logger.info(
            f"TF-IDF index built: matrix shape={self.tfidf_matrix.shape}, "
            f"vocabulary size={vocab_size}"
        )
        return {
            'chunk_count': len(self.chunk_ids),
            'vocab_size': vocab_size,
            'matrix_shape': self.tfidf_matrix.shape,
            'density': density,
        }

    def fit(self, chunks: list) -> dict:
        """Alias for build() returning index statistics."""
        return self.build(chunks)

    @property
    def vocabulary(self) -> dict:
        """Return vocabulary mapping."""
        return getattr(self.vectorizer, 'vocabulary_', {})

    def transform(self, texts: list):
        """
        Transform new texts using the fitted vectorizer.
        Used for queries and proposal similarity.

        Args:
            texts: List of preprocessed text strings

        Returns:
            Sparse TF-IDF matrix
        """
        if not self.is_fitted:
            raise RuntimeError("Index has not been built yet. Call build() first.")
        return self.vectorizer.transform(texts)

    def save(self, output_dir: str) -> None:
        """Save index artifacts to disk."""
        os.makedirs(output_dir, exist_ok=True)

        joblib.dump(self.vectorizer, os.path.join(output_dir, "tfidf_vectorizer.pkl"))
        scipy.sparse.save_npz(os.path.join(output_dir, "tfidf_matrix.npz"), self.tfidf_matrix)
        joblib.dump(self.chunk_ids, os.path.join(output_dir, "chunk_ids.pkl"))

        # Save metadata about the index
        import json
        meta = {
            'chunk_count': len(self.chunk_ids),
            'vocab_size': len(self.vectorizer.vocabulary_),
            'matrix_shape': list(self.tfidf_matrix.shape),
            'ngram_range': list(self.vectorizer.ngram_range),
            'sublinear_tf': self.vectorizer.sublinear_tf,
        }
        with open(os.path.join(output_dir, "index_metadata.json"), 'w') as f:
            json.dump(meta, f, indent=2)

        logger.info(f"Index saved to {output_dir}")

    def load(self, output_dir: str) -> None:
        """Load index artifacts from disk."""
        self.vectorizer = joblib.load(os.path.join(output_dir, "tfidf_vectorizer.pkl"))
        self.tfidf_matrix = scipy.sparse.load_npz(os.path.join(output_dir, "tfidf_matrix.npz"))
        self.chunk_ids = joblib.load(os.path.join(output_dir, "chunk_ids.pkl"))
        self.is_fitted = True

        logger.info(
            f"Index loaded from {output_dir}: "
            f"{self.tfidf_matrix.shape[0]} chunks, "
            f"{self.tfidf_matrix.shape[1]} features"
        )
