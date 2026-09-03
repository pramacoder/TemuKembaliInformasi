import sqlite3
import os
import joblib
import scipy.sparse
from sklearn.feature_extraction.text import TfidfVectorizer

def build_index(db_path, output_dir):
    """
    Builds the TF-IDF index from the clean_text in the database.
    Saves the vectorizer, the tfidf matrix, and the list of document IDs to the output_dir.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print("Loading documents from database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We only use documents that have been successfully cleaned
    cursor.execute("SELECT document_id, clean_text FROM document_text WHERE clean_text IS NOT NULL AND clean_text != ''")
    records = cursor.fetchall()
    conn.close()
    
    if not records:
        print("Error: No processed documents found in the database.")
        return
        
    doc_ids = [r[0] for r in records]
    corpus = [r[1] for r in records]
    
    print(f"Loaded {len(corpus)} documents.")
    print("Building TF-IDF Index...")
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    print(f"TF-IDF Matrix shape: {tfidf_matrix.shape}")
    
    # Save the models
    vectorizer_path = os.path.join(output_dir, "tfidf_vectorizer.pkl")
    matrix_path = os.path.join(output_dir, "tfidf_matrix.npz")
    doc_ids_path = os.path.join(output_dir, "doc_ids.pkl")
    
    print("Saving index to disk...")
    joblib.dump(vectorizer, vectorizer_path)
    scipy.sparse.save_npz(matrix_path, tfidf_matrix)
    joblib.dump(doc_ids, doc_ids_path)
    
    print("Indexing complete!")

if __name__ == "__main__":
    # Ensure working directory is project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    
    DB_PATH = "database/archive.db"
    MODELS_DIR = "models"
    
    build_index(DB_PATH, MODELS_DIR)
