import sqlite3
import os

def get_metadata(db_path, search_results):
    """
    Takes search results [(doc_id, score), ...] and enriches them with metadata from SQLite.
    Returns a list of dictionaries with all document info.
    """
    if not search_results:
        return []
        
    conn = sqlite3.connect(db_path)
    # Return dictionary-like rows
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Extract IDs
    doc_ids = [res[0] for res in search_results]
    
    # Create the IN clause placeholders
    placeholders = ','.join(['?'] * len(doc_ids))
    
    query = f"""
        SELECT id, title, course, category, filename, file_path, source_url
        FROM documents
        WHERE id IN ({placeholders})
    """
    
    cursor.execute(query, doc_ids)
    rows = cursor.fetchall()
    conn.close()
    
    # Map DB results by ID for fast lookup
    metadata_map = {row['id']: dict(row) for row in rows}
    
    # Construct final enriched list, preserving the original ranking order
    enriched_results = []
    for rank, (doc_id, score) in enumerate(search_results, 1):
        if doc_id in metadata_map:
            doc_info = metadata_map[doc_id]
            doc_info['similarity'] = score
            doc_info['rank'] = rank
            enriched_results.append(doc_info)
            
    return enriched_results

if __name__ == "__main__":
    from search import SearchEngine
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(project_root, "database", "archive.db")
    
    engine = SearchEngine(models_dir=os.path.join(project_root, "models"))
    q = "manajemen risiko proyek"
    results = engine.search(q, top_k=3)
    
    enriched = get_metadata(db_path, results)
    
    for doc in enriched:
        print(f"[{doc['rank']}] Score: {doc['similarity']:.4f} | {doc['title']} ({doc['course']})")
