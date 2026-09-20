# Academic IR System

Sistem Information Retrieval untuk dokumen akademik menggunakan **TF-IDF + Vector Space Model + Cosine Similarity**.

## Fitur

- **Unified Search** — Satu search bar untuk semua corpus (Material, Research, Thesis)
- **Chunk-Level Retrieval** — Hasil menunjukkan halaman dan snippet yang relevan
- **Language-Aware** — Preprocessing adaptif untuk English dan Indonesian
- **Proposal Similarity** — Upload proposal PDF, temukan dokumen serupa
- **Evaluasi** — Precision@K, Recall@K, MAP, NDCG

## Arsitektur

```
User Query → Preprocessing → TF-IDF Transform → Cosine Similarity → Ranking → Results
                                                                        ↑
Corpus PDFs → Extraction → Chunking → Preprocessing → TF-IDF Index ────┘
```

## Corpus Types

| Type | Source | ID Prefix |
|---|---|---|
| MATERIAL | OCW UI | MAT-XXXXXX |
| RESEARCH | CORE, DOAJ | RES-XXXXXX |
| THESIS | Institutional Repo | THS-XXXXXX |

## Quick Start

```bash
# 1. Setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Initialize database
python -c "from src.database.models import init_database; init_database()"

# 3. Collect data (example: OCW UI)
python scripts/collect_ocw.py

# 4. Build index
python scripts/build_index.py

# 5. Run web UI
streamlit run app/streamlit_app.py
```

## Tech Stack

- **Python 3.10+**
- **PyMuPDF** — PDF extraction
- **scikit-learn** — TF-IDF + cosine similarity
- **Sastrawi** — Indonesian NLP
- **NLTK** — English NLP
- **langdetect** — Language detection
- **SQLite** — Metadata storage
- **Streamlit** — Web UI
