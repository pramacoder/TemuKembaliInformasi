"""
Academic IR System — Multilingual Semantic Embeddings for Query-Focused Summarization
====================================================================================
Computes cross-lingual semantic similarity between user queries (e.g. Bahasa Indonesia)
and academic document sentences (e.g. English research papers).

Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) when available,
with a fast bilingual lexical-subword cosine similarity fallback.
"""

import logging
from typing import List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Common cross-lingual academic vocabulary dictionary for fast semantic bridging
BILINGUAL_ACADEMIC_DICT = {
    # Indonesian -> English synonyms
    "klasifikasi": ["classification", "classifier", "classify"],
    "pembelajaran": ["learning", "training", "machine learning"],
    "mesin": ["machine", "engine"],
    "jaringan": ["network", "neural"],
    "saraf": ["neural", "neuron"],
    "tiruan": ["artificial", "synthetic"],
    "data": ["data", "dataset"],
    "evaluasi": ["evaluation", "metric", "accuracy", "performance", "f1"],
    "akurasi": ["accuracy", "precision", "performance"],
    "metode": ["method", "methodology", "approach", "technique"],
    "algoritma": ["algorithm", "pipeline"],
    "ringkasan": ["summary", "summarization", "abstract"],
    "pencarian": ["search", "retrieval", "query"],
    "gambar": ["image", "picture", "visual"],
    "citra": ["image", "vision"],
    "teks": ["text", "document"],
    "bahasa": ["language", "linguistic", "nlp"],
    "alami": ["natural"],
    "penelitian": ["research", "study", "investigation", "paper"],
    "hasil": ["result", "finding", "outcome"],
    "analisis": ["analysis", "analyze"],
    "kesimpulan": ["conclusion", "conclude"],
    "latar": ["background"],
    "belakang": ["background"],
    "tujuan": ["objective", "goal", "aim", "purpose"],
    "sistem": ["system", "framework", "architecture"],
    "arsitektur": ["architecture", "model"],
    "pengenalan": ["recognition", "identification"],
    "suara": ["speech", "audio", "voice"],
    "wajah": ["face", "facial"],
    "deteksi": ["detection", "detect"],
    "optimasi": ["optimization", "tuning"],
    "parameter": ["parameter", "hyperparameter"],
    "fitur": ["feature", "attribute"],
    "bobot": ["weight", "importance"],
    "vektor": ["vector", "embedding"],
    "ruang": ["space"],
    "kemiripan": ["similarity", "distance"],
    "jarak": ["distance", "metric"],
    "dokumen": ["document", "corpus"],
    "korpus": ["corpus", "dataset"],
    "halaman": ["page"],
    "indeks": ["index", "indexing"],
    "koleksi": ["collection"],
}


class MultilingualEmbedder:
    """Provides cross-lingual embeddings or hybrid semantic similarity."""

    _instance = None
    _model = None
    _is_transformer = False

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._init_model()

    def _init_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading multilingual transformer: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            self._is_transformer = True
            logger.info("Multilingual transformer loaded successfully.")
        except Exception as e:
            logger.info(f"SentenceTransformers unavailable ({e}). Using bilingual lexical-semantic engine.")
            self._model = None
            self._is_transformer = False

    def is_transformer(self) -> bool:
        return self._is_transformer

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts into dense vectors."""
        if not texts:
            return np.zeros((0, 64))

        if self._is_transformer and self._model is not None:
            embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            # Normalize to unit length for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return embeddings / norms

        # Fallback: Character n-gram + Expanded vocabulary TF-IDF representation
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize

        expanded_texts = [self._expand_text(t) for t in texts]

        vec = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
            max_features=2048,
        )
        mat = vec.fit_transform(expanded_texts).toarray()
        return normalize(mat)

    def _expand_text(self, text: str) -> str:
        words = text.lower().split()
        expansions = []
        for w in words:
            clean_w = w.strip(".,;:?!'\"()[]")
            if clean_w in BILINGUAL_ACADEMIC_DICT:
                expansions.extend(BILINGUAL_ACADEMIC_DICT[clean_w])
        return text + (" " + " ".join(expansions) if expansions else "")

    def compute_query_similarity(self, query: str, sentences: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute similarity scores between a query and a list of candidate sentences,
        and return (similarity_scores, sentence_vectors).
        """
        if not sentences:
            return np.zeros(0), np.zeros((0, 0))

        if self._is_transformer and self._model is not None:
            q_vec = self.embed_texts([query])
            s_vecs = self.embed_texts(sentences)
            scores = np.dot(s_vecs, q_vec.T).flatten()
            return np.clip(scores, 0.0, 1.0), s_vecs

        # Fallback: Joint TF-IDF matrix over [query] + sentences
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize

        all_expanded = [self._expand_text(query)] + [self._expand_text(s) for s in sentences]
        vec = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
            max_features=2048,
        )
        all_matrix = vec.fit_transform(all_expanded).toarray()
        norm_all = normalize(all_matrix)

        q_vec = norm_all[0:1, :]
        s_vecs = norm_all[1:, :]

        scores = np.dot(s_vecs, q_vec.T).flatten()
        return np.clip(scores, 0.0, 1.0), s_vecs


_embedder_instance: Optional[MultilingualEmbedder] = None


def get_multilingual_embedder() -> MultilingualEmbedder:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = MultilingualEmbedder()
    return _embedder_instance
