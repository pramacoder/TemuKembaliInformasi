# Academic IR — Information Retrieval System

Sistem Information Retrieval (IR) untuk pencarian dokumen akademik multi-korpus menggunakan algoritma **TF-IDF + Vector Space Model (VSM) + Cosine Similarity**. Sistem ini dilengkapi dengan **Backend API modern (FastAPI)** dan **Antarmuka Web interaktif (Next.js 15, Tailwind CSS, & shadcn/ui)** serta opsi UI klasik via **Streamlit**.

---

## 🌟 Fitur Utama

- **Unified Multi-Corpus Search**: Mencari di seluruh korpus akademik (Bahan Kuliah OCW UI, Riset Ilmiah, & Skripsi/Thesis) dalam satu query.
- **Chunk-Level Retrieval**: Menampilkan potongan dokumen (*chunks*) paling relevan lengkap dengan nomor halaman, tingkat kemiripan (*similarity score*), serta metadata dokumen.
- **Bilingual / Language-Aware Preprocessing**: Preprocessing otomatis untuk dokumen berbahasa Indonesia (Sastrawi Stemmer) dan bahasa Inggris (NLTK Porter Stemmer).
- **Modern Web Interface**: Dibangun dengan Next.js 15 (App Router), Tailwind CSS v3, dan komponen shadcn/ui lengkap dengan filter korpus, facet tahun, dan sorting relevansi.
- **RESTful API Backend**: Endpoint cepat berbasis FastAPI (`/api/search`, `/api/stats`, `/api/health`) dengan CORS terkonfigurasi.
- **Pre-indexed Database & Models**: Basis data SQLite (`academic_ir.db`) dan matriks TF-IDF sudah disertakan, sehingga aplikasi dapat langsung dijalankan tanpa perlu proses *crawling* atau pelatihan ulang.

---

## 🏗️ Arsitektur Sistem

```text
                                 [ Next.js 15 Frontend ]
                                            │
                                            │ HTTP / JSON (Port 3000 -> 8000)
                                            ▼
                                  [ FastAPI Backend ]
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
       [ TFIDFIndex (VSM) ]                                    [ SQLite Database ]
  - tfidf_vectorizer.pkl (247k vocab)                     - 9,684 Document Chunks
  - tfidf_matrix.npz (9.6k x 247k)                        - Metadata Dokumen & Korpus
  - chunk_ids.pkl                                         - Path Dokumen & Halaman
```

---

## 📋 Prasyarat Sistem (Prerequisites)

Sebelum menjalankan aplikasi di perangkat baru, pastikan telah menginstal:

1. **Git**: Untuk meng-clone repositori.
2. **Python**: Versi `3.10` atau lebih baru (`python --version`).
3. **Node.js**: Versi `18.x` atau `20.x` LTS (`node --version`) beserta `npm`.

---

## 🚀 Panduan Menjalankan di Perangkat Lain (Step-by-Step)

### 1. Clone Repositori

Buka terminal / PowerShell, kemudian jalankan:

```bash
git clone https://github.com/pramacoder/TemuKembaliInformasi.git
cd TemuKembaliInformasi
```

---

### 2. Setup & Jalankan Backend (FastAPI)

Masuk ke direktori `academic-ir`:

```bash
cd academic-ir
```

#### A. Buat Virtual Environment & Install Dependensi

**Di Windows (PowerShell / Command Prompt):**
```powershell
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
.\venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt
```

**Di macOS / Linux:**
```bash
# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate

# Install dependensi
pip install -r requirements.txt
```

#### B. Setup Environment Variables (Opsional)
Jika ingin menggunakan scraper CORE API untuk crawling tambahan:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
*(Catatan: Jika hanya untuk menjalankan pencarian dan web, langkah ini tidak wajib karena database dan model sudah tersedia).*

#### C. Jalankan Server FastAPI

Pastikan virtual environment masih aktif, lalu jalankan:

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

Server backend akan berjalan di:
- **API URL:** `http://localhost:8000`
- **Swagger UI (Dokumentasi Interaktif):** `http://localhost:8000/docs`
- **Kesehatan Sistem:** `http://localhost:8000/api/health`

---

### 3. Setup & Jalankan Frontend (Next.js 15)

Buka jendela terminal / PowerShell **baru** (biarkan backend tetap menyala di terminal pertama).

Navigasikan ke folder frontend:

```bash
cd academic-ir/academic-ir-frontend
```

#### A. Install Dependensi Frontend

Jalankan perintah berikut:

```bash
npm install --legacy-peer-deps
```

*(Catatan: Menggunakan flag `--legacy-peer-deps` direkomendasikan untuk menghindari konflik peer dependensi React 19 / Next 15).*

#### B. Jalankan Server Development Frontend

```bash
npm run dev
```

Aplikasi frontend sekarang dapat diakses melalui browser di:
👉 **[http://localhost:3000](http://localhost:3000)**

---

### 4. (Alternatif) Menjalankan Streamlit UI

Jika ingin mencoba antarmuka alternatif berbasis Streamlit:

1. Buka terminal di folder `academic-ir/` dan aktifkan virtual environment.
2. Jalankan perintah:
   ```bash
   streamlit run app/streamlit_app.py
   ```
3. Akses di browser pada `http://localhost:8501`.

---

## 📂 Struktur Direktori Proyek

```text
TemuKembaliInformasi/
├── README.md                           # Dokumentasi utama proyek
├── .gitignore                          # Konfigurasi ignore git
├── academic-ir/
│   ├── app/
│   │   ├── api.py                      # FastAPI Backend Server (Endpoint /api/search, /api/stats)
│   │   └── streamlit_app.py            # Aplikasi antarmuka Streamlit alternatif
│   ├── database/
│   │   └── academic_ir.db              # Database SQLite (9,600+ chunks terindeks)
│   ├── models/                         # Serialized TF-IDF Index & Vocabulary
│   │   ├── chunk_ids.pkl               # Mapping ID chunk
│   │   ├── tfidf_matrix.npz            # Matriks sparse TF-IDF (Scipy)
│   │   ├── tfidf_vectorizer.pkl        # Fitted Scikit-Learn Vectorizer
│   │   └── index_metadata.json         # Info versi, vocab size, & parameter
│   ├── data/
│   │   ├── manifests/                  # CSV manifest metadata dokumen
│   │   ├── reports/                    # Laporan evaluasi retrieval (JSON)
│   │   └── raw/                        # File PDF mentah (diabaikan dari Git karena ukuran besar)
│   ├── src/
│   │   ├── database/                   # Model ORM / SQLite schema & queries
│   │   ├── indexing/                   # Modul pembangunan indeks TF-IDF
│   │   ├── preprocessing/              # Stemmer, tokenisasi, stopword Sastrawi/NLTK
│   │   └── retrieval/                  # Mesin ranking Cosine Similarity & Search Engine
│   ├── scripts/
│   │   ├── build_index.py              # Script membangun indeks dari database
│   │   ├── collect_ocw.py              # Scraper materi OCW UI
│   │   └── evaluate.py                 # Evaluasi metriks MAP, MRR, Precision@K
│   ├── requirements.txt                # Dependensi Python
│   └── academic-ir-frontend/           # Frontend Next.js 15
│       ├── src/
│       │   ├── app/                    # Next.js App Router (layout, globals.css, page.tsx)
│       │   ├── components/             # UI Components (ResultCard, FilterSidebar, SearchBar)
│       │   │   └── ui/                 # shadcn/ui components (Card, Button, Badge, Dialog, dll)
│       │   └── lib/                    # API client (`api.ts`), tipe data, utilities
│       ├── package.json                # Dependensi Node.js
│       └── tailwind.config.ts          # Konfigurasi Tailwind CSS v3
```

---

## 🔄 Membangun Ulang Indeks (Opsional)

Jika Anda menambahkan dokumen baru atau ingin mengubah parameter TF-IDF (seperti ukuran n-gram atau min_df), Anda dapat melatih ulang indeks:

```bash
cd academic-ir
python scripts/build_index.py
python scripts/build_bm25_index.py
```

---

## 📊 Eksperimen Benchmark & Evaluasi Lanjutan (Revisi Tahap 2)

Sistem telah dilengkapi dengan *evaluation suite* komprehensif berstandar Cranfield yang menguji 33 kueri akademik terstruktur:

1. **Full Benchmark (TF-IDF vs BM25 + Granular Breakdown):**
   ```bash
   python scripts/run_full_benchmark.py
   ```
   Menghasilkan laporan perbandingan lengkap, analisis galat (`error_analysis.jsonl`), serta rincian metrik per kategori kueri dan per korpus (`granular_evaluation.json`).

2. **Uji Signifikansi Statistik (Wilcoxon Signed-Rank Test):**
   ```bash
   python scripts/statistical_significance.py
   ```
   Menghitung signifikansi berpasangan, ukuran efek (*rank-biserial correlation*), dan selang kepercayaan bootstrap 95%.

3. **Studi Ablasi Komponen (*Ablation Ladder* E0–E5):**
   ```bash
   python scripts/run_ablation.py
   ```
   Menguji kontribusi bertingkat dari TF-IDF, BM25, Title Boost, hingga Query Expansion.

4. **Penyetelan Hyperparameter BM25 (Grid Search Dev/Test Split):**
   ```bash
   python scripts/tune_bm25_params.py
   ```
   Mencari parameter $k_1$ dan $b$ optimal pada Development Set (Q01–Q22) dan mengujinya secara independen pada Test Set (Q23–Q33).

5. **Pengujian Efek Query Drift pada Query Expansion:**
   ```bash
   python src/retrieval/query_expansion.py eval
   ```

6. **Benchmark Latensi Komparatif (*Apple-to-Apple*):**
   ```bash
   python scripts/benchmark_latency.py
   ```

---

## 🛠️ Panduan Penyelesaian Masalah (Troubleshooting)

1. **Error: `fetch failed` atau hasil pencarian tidak keluar di Frontend:**
   - Pastikan backend FastAPI sedang aktif di `http://localhost:8000`.
   - Cek `http://localhost:8000/api/health` di browser untuk memastikan statusnya `"healthy"`.
2. **Error `EADDRINUSE: address already in use`:**
   - Port 3000 atau 8000 sedang digunakan oleh proses lain. Matikan proses sebelumnya atau ubah port saat menjalankan (`uvicorn app.api:app --port 8001` atau `npm run dev -- -p 3001`).
3. **NLTK Data Missing:**
   - Jika muncul peringatan punkt/stopwords dari NLTK, jalankan di Python:
     ```python
     import nltk
     nltk.download('punkt')
     nltk.download('stopwords')
     ```
