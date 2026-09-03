import os
import joblib
import scipy.sparse
from sklearn.metrics.pairwise import cosine_similarity
import sys

# Ensure we can import from preprocessing
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(project_root, "src"))
from preprocessing.cleaner import clean_text
from preprocessing.stemmer import get_nlp

class SearchEngine:
    def __init__(self, models_dir="models"):
        self.vectorizer = joblib.load(os.path.join(models_dir, "tfidf_vectorizer.pkl"))
        self.tfidf_matrix = scipy.sparse.load_npz(os.path.join(models_dir, "tfidf_matrix.npz"))
        self.doc_ids = joblib.load(os.path.join(models_dir, "doc_ids.pkl"))
        self.nlp = get_nlp()
        
    def search(self, query, top_k=10):
        """
        Takes a raw query, preprocesses it, and computes cosine similarity against the TF-IDF matrix.
        Returns a list of tuples: (doc_id, similarity_score)
        """
        # 1. Preprocess the query
        cleaned_query = clean_text(query)
        processed_query = self.nlp.process(cleaned_query)
        
        # 2. Transform query into TF-IDF vector
        query_vec = self.vectorizer.transform([processed_query])
        
        # 3. Compute cosine similarity
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # 4. Rank results
        top_indices = scores.argsort()[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = scores[idx]
            if score > 0: # Only return documents with some similarity
                results.append((self.doc_ids[idx], float(score)))
                
        return results

if __name__ == "__main__":
    engine = SearchEngine()
    query = "manajemen risiko proyek"
    print(f"Searching for: '{query}'")
    results = engine.search(query)
    for doc_id, score in results:
        print(f"[{score:.4f}] {doc_id}")
