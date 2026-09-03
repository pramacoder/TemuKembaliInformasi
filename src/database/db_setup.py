import sqlite3
import os

def create_database(db_path="database/archive.db"):
    """Creates the SQLite database and necessary tables."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id          TEXT PRIMARY KEY,
        title       TEXT NOT NULL,
        course      TEXT,
        category    TEXT,
        filename    TEXT,
        file_path   TEXT,
        source_url  TEXT,
        author      TEXT,
        year        INTEGER,
        page_count  INTEGER,
        file_size   INTEGER,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create document_text table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS document_text (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id TEXT REFERENCES documents(id),
        page        INTEGER,
        raw_text    TEXT,
        clean_text  TEXT
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    create_database("database/archive.db")
