import sqlite3
import os
import multiprocessing
from tqdm import tqdm

def process_single_document(args):
    """
    Function to process a single document in a separate process.
    We need to re-import and initialize stemmer in each process.
    """
    doc_id, text = args
    
    # Lazy import to avoid PicklingError and heavy initialization in main thread
    from cleaner import clean_text
    from stemmer import get_nlp
    
    nlp = get_nlp()
    cleaned = clean_text(text)
    processed = nlp.process(cleaned)
    return doc_id, processed

def main():
    # Ensure working directory is project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    
    # We must add src to path to import local modules if needed
    import sys
    sys.path.append(os.path.join(project_root, "src"))
    sys.path.append(os.path.join(project_root, "src", "preprocessing"))
    
    DB_PATH = "database/archive.db"
    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all documents that haven't been processed yet
    cursor.execute("SELECT id, raw_text FROM document_text WHERE clean_text IS NULL OR clean_text = ''")
    documents = cursor.fetchall()
    
    if not documents:
        print("No documents need processing.")
        return
        
    print(f"Found {len(documents)} documents to process. This may take a while with Sastrawi...")
    
    # Number of workers
    num_workers = max(1, multiprocessing.cpu_count() - 1)
    print(f"Using {num_workers} processes.")
    
    # Process in parallel
    results = []
    with multiprocessing.Pool(num_workers) as pool:
        for result in tqdm(pool.imap_unordered(process_single_document, documents), total=len(documents)):
            results.append(result)
            
            # Save in batches of 10 to not lose progress
            if len(results) >= 10:
                cursor.executemany("UPDATE document_text SET clean_text = ? WHERE id = ?", 
                                  [(text, doc_id) for doc_id, text in results])
                conn.commit()
                results.clear()
                
    # Save any remaining
    if results:
        cursor.executemany("UPDATE document_text SET clean_text = ? WHERE id = ?", 
                          [(text, doc_id) for doc_id, text in results])
        conn.commit()
        
    conn.close()
    print("Corpus processing complete!")

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()
