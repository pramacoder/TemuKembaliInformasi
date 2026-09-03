import sqlite3
import json
import os
from tqdm import tqdm

def find_file_path(base_dir, course_name, doc_id):
    # Try to find the file dynamically if it exists
    # Replace invalid chars in course_name that might have been removed by scraper
    safe_course_name = course_name.replace(" ", "_").replace(":", "").replace("/", "_")
    course_dir = os.path.join(base_dir, safe_course_name)
    
    # Try exact course name first
    if not os.path.exists(course_dir):
        # The scraper might have cleaned it slightly differently.
        # Let's search inside dataset_ocw_ui for any match
        course_dir = None
        for d in os.listdir(base_dir):
            if os.path.isdir(os.path.join(base_dir, d)) and d.lower() == safe_course_name.lower():
                course_dir = os.path.join(base_dir, d)
                break
                
    if not course_dir or not os.path.exists(course_dir):
        # Still can't find course dir, let's just search all dirs
        for d in os.listdir(base_dir):
            full_d = os.path.join(base_dir, d)
            if os.path.isdir(full_d):
                for f in os.listdir(full_d):
                    if doc_id in f and f.endswith(".pdf"):
                        return os.path.join(full_d, f).replace("\\", "/")
        return ""
        
    # Check if we can find by ID in course dir
    for f in os.listdir(course_dir):
        if doc_id in f and f.endswith(".pdf"):
            return os.path.join(course_dir, f).replace("\\", "/")
            
    return ""

def migrate_metadata(db_path, metadata_path, dataset_dir):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        resources = data.get("resources", [])
        
        for res in tqdm(resources, desc="Migrating metadata"):
            doc_id = res.get("id")
            course_name = res.get("course_name", "")
            title = res.get("title", "")
            
            # Reconstruct file path
            file_path = find_file_path(dataset_dir, course_name, doc_id)
            filename = os.path.basename(file_path) if file_path else f"{title.replace(' ', '_')}_{doc_id}.pdf"
            
            cursor.execute('''
            INSERT OR IGNORE INTO documents 
            (id, title, course, category, filename, file_path, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                doc_id,
                title,
                course_name,
                res.get("category", "Fasilkom UI"), 
                filename,
                file_path,
                res.get("source_url", "")
            ))
            
    conn.commit()
    conn.close()

def migrate_documents_text(db_path, jsonl_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Migrating document text"):
            if not line.strip():
                continue
            doc = json.loads(line)
            doc_id = doc.get("id")
            text = doc.get("text", "")
            
            if doc_id and text:
                cursor.execute('''
                INSERT INTO document_text (document_id, raw_text)
                VALUES (?, ?)
                ''', (doc_id, text))
                
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Ensure working directory is project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(project_root)
    
    DB_PATH = "database/archive.db"
    METADATA_PATH = "dataset_ocw_ui/all_metadata.json"
    JSONL_PATH = "dataset_ocw_ui/documents.jsonl"
    DATASET_DIR = "dataset_ocw_ui"
    
    # Run setup if not exists
    from db_setup import create_database
    if not os.path.exists(DB_PATH):
        create_database(DB_PATH)
        
    print("Starting migration...")
    migrate_metadata(DB_PATH, METADATA_PATH, DATASET_DIR)
    migrate_documents_text(DB_PATH, JSONL_PATH)
    print("Migration complete.")
