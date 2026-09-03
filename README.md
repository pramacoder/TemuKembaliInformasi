# 📚 Penelusur Arsip Akademik & Proposal Universitas

> **Sistem Information Retrieval** berbasis **TF-IDF + Vector Space Model** untuk penelusuran dokumen PDF akademik dari OCW/OASE Universitas Indonesia.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-Metadata-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/Sumber-CC%20BY--NC--SA-lightgrey?style=for-the-badge)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

## Daftar Isi

- [Tentang Proyek](#tentang-proyek)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Fitur Utama](#fitur-utama)
- [Teknologi yang Digunakan](#teknologi-yang-digunakan)
- [Struktur Proyek](#struktur-proyek)
- [Struktur Database](#struktur-database)
- [Instalasi](#instalasi)
- [Penggunaan](#penggunaan)
- [Pipeline Detail](#pipeline-detail)
- [Dataset](#dataset)
- [Roadmap Pengembangan](#roadmap-pengembangan)
- [Lisensi & Atribusi](#lisensi--atribusi)

---

## Tentang Proyek

Sistem ini adalah **mesin pencari dokumen akademik** yang dirancang untuk:

1. **Penelusuran Arsip** — Mencari materi kuliah, modul, dan referensi dari OCW UI berdasarkan query teks bebas.
2. **Deteksi Kemiripan Proposal** — Menemukan dokumen akademik yang memiliki topik serupa dengan proposal mahasiswa yang sedang diperiksa, membantu proses persetujuan dan mencegah duplikasi penelitian.

> **Prinsip utama:** HTML hanya digunakan sebagai *discovery layer* untuk menemukan dan mengunduh PDF. Dataset utama adalah **PDF** itu sendiri, bukan halaman web.

---

## Arsitektur Sistem

```
                        SUMBER DATA
                            |
               +------------v------------+
               |    Website OCW/OASE UI  |
               +------------+------------+
                            |
                      Web Scraping
                  (Requests + BeautifulSoup)
                            |
                            v
                     +-------------+
                     |  PDF Files  |  <-- Dataset Utama
                     +------+------+
                            |
               +------------v------------+
               |   PDF Text Extraction   |
               |        PyMuPDF          |
               +------------+------------+
                            |
                            v
                 +--------------------+
                 | Text Preprocessing |
                 |  - Case Folding    |
                 |  - Cleaning        |
                 |  - Tokenization    |
                 |  - Stopword Removal|
                 |  - Stemming (ID)   |
                 +--------+-----------+
                          |
                          v
                    +----------+
                    |  TF-IDF  |
                    +-----+----+
                          |
                          v
                 +-----------------+
                 |  Vector Space   |
                 |     Model       |
                 +--------+--------+
                          |
                   Cosine Similarity
                          |
                          v
                 +-----------------+
                 | Ranking / Top-K |
                 +--------+--------+
                          |
                          v
                 +-----------------+
                 | Web Application |
                 | Search & Result |
                 +-----------------+
```

### Tiga Lapisan Data

| Lapisan | Isi | Tujuan |
|---------|-----|--------|
| **PDF Original** | File PDF asli yang diunduh | Sumber dokumen; dapat dibuka pengguna |
| **Extracted Text** | Hasil ekstraksi teks mentah dari PDF | Input preprocessing & TF-IDF |
| **Vector Index** | Matriks TF-IDF | Pencarian cosine similarity |

---

## Fitur Utama

- **Full-text Search** — Cari di seluruh korpus dokumen dengan query teks bebas Bahasa Indonesia
- **Ranking Relevansi** — Hasil diurutkan berdasarkan *cosine similarity* tertinggi
- **Filter Mata Kuliah** — Saring hasil pencarian berdasarkan mata kuliah atau kategori
- **Akses PDF Langsung** — Setiap hasil pencarian terhubung ke file PDF aslinya
- **Deteksi Kemiripan Proposal** — Bandingkan dokumen baru terhadap seluruh arsip yang ada
- **Metadata Lengkap** — Setiap dokumen dilengkapi dengan judul, mata kuliah, sumber URL, jumlah halaman, dan lain-lain

---

## Teknologi yang Digunakan

### Wajib (Core Stack)

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| **Bahasa** | Python 3.10+ | Bahasa utama seluruh pipeline |
| **Scraping** | Requests | HTTP request ke OCW/OASE UI |
| **HTML Parsing** | BeautifulSoup4 | Menemukan link PDF di halaman web |
| **PDF Processing** | PyMuPDF (`fitz`) | Ekstraksi teks dari file PDF |
| **NLP Indonesia** | Sastrawi | Stopword removal & stemming Bahasa Indonesia |
| **IR Engine** | scikit-learn | TF-IDF vectorizer & cosine similarity |
| **Komputasi** | NumPy | Operasi vektor dan matriks |
| **Metadata DB** | SQLite | Menyimpan metadata dokumen |
| **PDF Storage** | Local File System | Menyimpan file PDF asli |
| **UI Prototype** | Streamlit | Antarmuka pencarian cepat |
| **Version Control** | Git | Kontrol versi kode |

### Opsional (Pengembangan Lanjut)

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| **OCR** | Tesseract + pytesseract | Ekstraksi PDF hasil scan/gambar |
| **Vector Indexing** | FAISS | Indexing ANN untuk dataset sangat besar |
| **Backend API** | FastAPI + Uvicorn | REST API untuk integrasi frontend |
| **Frontend** | React / Next.js | Antarmuka web yang lebih lengkap |
| **DB Skala Besar** | PostgreSQL | Jika dataset melebihi kapasitas SQLite |
| **Cloud Storage** | S3-compatible | Penyimpanan PDF di cloud |

---

## Struktur Proyek

```
TemuKembaliInformasi/
|
+-- README.md                    <- Dokumentasi proyek ini
+-- requirements.txt             <- Daftar dependensi Python
+-- .gitignore
|
+-- ocw_ui_scraper.py            <- Scraper OCW UI (PDF-only mode)
+-- scraper.log                  <- Log hasil scraping
|
+-- dataset_ocw_ui/              <- Hasil scraping
|   +-- Manajemen_Proyek_TI/
|   |   +-- materi_01.pdf
|   |   +-- ...
|   +-- IKI20230_Sistem_Operasi/
|   |   +-- ...
|   +-- Aljabar_Linier/
|   +-- [... 16 mata kuliah ...]
|   |
|   +-- all_metadata.json        <- Metadata semua dokumen
|   +-- documents.jsonl          <- Corpus teks dokumen (JSON Lines)
|
+-- src/                         <- Source code utama [PLANNED]
|   +-- preprocessing/
|   |   +-- cleaner.py           <- Cleaning & tokenization
|   |   +-- stemmer.py           <- Sastrawi wrapper
|   |
|   +-- indexing/
|   |   +-- tfidf.py             <- TF-IDF vectorizer
|   |   +-- vsm.py               <- Vector Space Model
|   |
|   +-- retrieval/
|   |   +-- search.py            <- Cosine similarity search
|   |   +-- ranking.py           <- Pengurutan hasil
|   |
|   +-- api/
|       +-- main.py              <- FastAPI endpoint
|
+-- app/                         <- Streamlit UI [PLANNED]
|   +-- streamlit_app.py
|
+-- database/                    <- SQLite database [PLANNED]
|   +-- archive.db
|
+-- models/                      <- Saved TF-IDF index [PLANNED]
|   +-- tfidf_vectorizer.pkl
|   +-- tfidf_matrix.npz
|
+-- notebooks/                   <- Eksperimen & analisis [PLANNED]
    +-- 01_exploratory_analysis.ipynb
    +-- 02_preprocessing_pipeline.ipynb
    +-- 03_retrieval_evaluation.ipynb
```

---

## Struktur Database

### Tabel `documents`

```sql
CREATE TABLE documents (
    id          TEXT PRIMARY KEY,      -- e.g. "OCW_00001"
    title       TEXT NOT NULL,
    course      TEXT,                  -- Nama mata kuliah
    category    TEXT,                  -- Kategori/Fakultas
    filename    TEXT,
    file_path   TEXT,                  -- Path ke PDF lokal
    source_url  TEXT,                  -- URL asal OCW/OASE
    author      TEXT,
    year        INTEGER,
    page_count  INTEGER,
    file_size   INTEGER,               -- Bytes
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabel `document_text`

```sql
CREATE TABLE document_text (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT REFERENCES documents(id),
    page        INTEGER,
    raw_text    TEXT,                  -- Teks hasil ekstraksi PyMuPDF
    clean_text  TEXT                   -- Teks setelah preprocessing
);
```

### Contoh Metadata Dokumen

```json
{
  "id": "OCW_00001",
  "title": "Pengantar Manajemen Proyek TI",
  "course": "Manajemen Proyek TI",
  "source": "OCW UI",
  "source_url": "https://ocw.ui.ac.id/course/view.php?id=...",
  "filename": "pengantar_manajemen_proyek.pdf",
  "file_path": "dataset_ocw_ui/Manajemen_Proyek_TI/pengantar.pdf",
  "page_count": 25
}
```

---

## Instalasi

### Prasyarat

- Python 3.10 atau lebih baru
- pip

### 1. Clone Repository

```bash
git clone https://github.com/<username>/TemuKembaliInformasi.git
cd TemuKembaliInformasi
```

### 2. Buat Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
```

Atau install manual (core stack):

```bash
# Scraping & PDF
pip install requests beautifulsoup4 lxml pymupdf tqdm

# NLP & IR
pip install PySastrawi scikit-learn numpy

# UI
pip install streamlit
```

Untuk komponen opsional:

```bash
# OCR
pip install pytesseract
# Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki

# FastAPI backend
pip install fastapi uvicorn

# FAISS (vector indexing untuk dataset besar)
pip install faiss-cpu
```

---

## Penggunaan

### 1. Scraping Dataset dari OCW UI

```bash
python ocw_ui_scraper.py
```

Skrip ini akan:
- Mengambil daftar mata kuliah dari Fasilkom UI (category ID = 12)
- Mengunduh semua file PDF yang ditemukan
- Mengekstrak teks menggunakan PyMuPDF
- Menyimpan metadata ke `all_metadata.json` dan `documents.jsonl`

> **Catatan:** Hanya file PDF yang diunduh. Forum, tugas HTML, video, dan link lain diabaikan.

### 2. Build TF-IDF Index *(segera hadir)*

```bash
python src/indexing/tfidf.py --input dataset_ocw_ui/documents.jsonl
```

### 3. Jalankan Aplikasi Streamlit *(segera hadir)*

```bash
streamlit run app/streamlit_app.py
```

Buka browser di `http://localhost:8501`.

### 4. Jalankan FastAPI Backend *(segera hadir)*

```bash
uvicorn src.api.main:app --reload
```

**Contoh request:**

```http
GET /search?q=manajemen+risiko+proyek&top_k=5
```

**Contoh response:**

```json
[
  {
    "rank": 1,
    "document_id": "OCW_00042",
    "title": "Manajemen Risiko dalam Proyek TI",
    "course": "Manajemen Proyek TI",
    "similarity": 0.82,
    "file_path": "dataset_ocw_ui/Manajemen_Proyek_TI/manajemen_risiko.pdf"
  },
  {
    "rank": 2,
    "document_id": "OCW_00015",
    "title": "Project Lifecycle & Risk Management",
    "course": "Manajemen Proyek TI",
    "similarity": 0.74,
    "file_path": "..."
  }
]
```

---

## Pipeline Detail

### A. Web Scraping

```
Website OCW UI
     |
     +-- GET category page (Fasilkom, ID=12)
     |       +-- Daftar mata kuliah
     |
     +-- GET course page (course/view.php?id=X)
     |       +-- Semua link resource
     |
     +-- Filter: hanya link yang mengarah ke .pdf
             |
             +-- Download PDF --> simpan di dataset_ocw_ui/<Matkul>/
```

### B. Text Preprocessing

```python
# Contoh pipeline preprocessing
text = "Penggunaan Algoritma Backtracking dalam Pemecahan Masalah"

# 1. Case folding
text = text.lower()
# -> "penggunaan algoritma backtracking dalam pemecahan masalah"

# 2. Cleaning (hapus angka, simbol, whitespace berlebih)
text = re.sub(r'[^a-z\s]', '', text)

# 3. Tokenization
tokens = text.split()
# -> ["penggunaan", "algoritma", "backtracking", "dalam", "pemecahan", "masalah"]

# 4. Stopword removal (Sastrawi)
tokens = [t for t in tokens if t not in stopwords]
# -> ["algoritma", "backtracking", "pemecahan", "masalah"]

# 5. Stemming (Sastrawi)
tokens = [stemmer.stem(t) for t in tokens]
# -> ["algoritma", "backtrack", "pecah", "masalah"]
```

### C. TF-IDF & Vector Space Model

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Build index
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(corpus)  # shape: (n_docs, n_terms)

# Query
query_vec = vectorizer.transform([preprocessed_query])

# Cosine similarity
scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

# Ranking: ambil Top-K dokumen teratas
top_k_idx = scores.argsort()[::-1][:K]
```

### D. Mode Deteksi Kemiripan Proposal

```
Proposal Mahasiswa (PDF baru)
         |
         v
  Text Extraction + Preprocessing
         |
         v
  TF-IDF transform (pakai index yang sudah ada)
         |
         v
  Cosine Similarity vs. seluruh arsip
         |
         v
  Top-10 Dokumen Paling Mirip
  (beserta skor kemiripan)
```

---

## Dataset

Dataset saat ini terdiri dari dokumen PDF yang dikumpulkan dari **OCW Universitas Indonesia**, Fakultas Ilmu Komputer, meliputi 16 mata kuliah:

| # | Mata Kuliah |
|---|-------------|
| 1 | Aljabar Linier |
| 2 | Analisis dan Perancangan Sistem Informasi |
| 3 | Dasar-Dasar Arsitektur Komputer |
| 4 | Dasar-Dasar Pemrograman 1 |
| 5 | Dasar-Dasar Pemrograman 2 (Java) |
| 6 | IKI10400 Prinsip-Prinsip Sistem Informasi |
| 7 | IKI10610 Matematika Diskret 2 |
| 8 | IKI20230 Sistem Operasi |
| 9 | IKI80050T Metodologi Penelitian |
| 10 | IKI81404T Perancangan Sistem Informasi |
| 11 | IKI82406T Perencanaan Strategis Sistem Informasi |
| 12 | IKI83403T Data Mining and Business Intelligence |
| 13 | Manajemen Proyek TI |
| 14 | Pemrograman Fungsional |
| 15 | Pemrograman Logika |
| 16 | Sistem Interaksi (Human Computer Interaction) |

> **Lisensi Sumber:** Creative Commons BY-NC-SA — Universitas Indonesia, Fakultas Ilmu Komputer.

---

## Formula Utama

### TF-IDF

```
TF-IDF(t, d) = TF(t, d) x log(N / df(t))

Keterangan:
  t      = term (kata)
  d      = dokumen
  N      = total jumlah dokumen dalam korpus
  df(t)  = jumlah dokumen yang mengandung term t
```

### Cosine Similarity

```
sim(d, q) = (d . q) / (||d|| x ||q||)

Keterangan:
  d     = vektor TF-IDF dokumen
  q     = vektor TF-IDF query
  Nilai : 0 (tidak mirip) hingga 1 (identik)
```

---

## Roadmap Pengembangan

### Versi 1.0 — Core IR System *(dalam pengerjaan)*

- [x] Web scraper OCW UI (PDF-only mode)
- [x] Pengumpulan dataset awal (16 mata kuliah)
- [ ] Text preprocessing pipeline (Sastrawi)
- [ ] TF-IDF indexing (scikit-learn)
- [ ] Cosine similarity search
- [ ] SQLite metadata database
- [ ] Streamlit UI prototype

### Versi 1.1 — Enhanced Search

- [ ] Filter pencarian berdasarkan mata kuliah
- [ ] Pagination hasil pencarian
- [ ] Mode deteksi kemiripan proposal
- [ ] Export hasil ke CSV/Excel

### Versi 2.0 — Production Ready

- [ ] FastAPI REST backend
- [ ] React/Next.js frontend
- [ ] OCR untuk PDF hasil scan (Tesseract)
- [ ] FAISS vector indexing (jika dataset > 5.000 dokumen)
- [ ] Evaluasi IR: Precision@K, Recall, MAP, NDCG
- [ ] Docker deployment

---

## Lisensi & Atribusi

- **Kode sumber:** [MIT License](LICENSE)
- **Dataset OCW UI:** [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
  - Atribusi: **Universitas Indonesia, Fakultas Ilmu Komputer** via [ocw.ui.ac.id](https://ocw.ui.ac.id)

---

*Dibangun dengan Python · TF-IDF · Vector Space Model · Cosine Similarity*
