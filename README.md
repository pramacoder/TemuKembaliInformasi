# Academic IR — Unified Multi-Corpus Academic Search Engine

> **Sistem Temu Kembali Informasi Dokumen Akademik Lintas Disiplin Ilmu Berbasis Machine Learning**  
> Mengimplementasikan pendekatan **Dual-Baseline: TF-IDF Vector Space Model (VSM)** dan **Okapi BM25** dengan **Document-Level Aggregation** (`max`, `max+2nd`, `topN_avg`) serta integrasi antarmuka modern **Next.js 15 (React 19)** dan backend berkecepatan tinggi **FastAPI**.

---

## 📌 Ringkasan Sistem (*Executive Summary*)

**Academic IR** dirancang untuk menyelesaikan masalah *information silo* dan *fragment redundancy* pada repositori akademik. Sistem ini menyatukan pencarian terhadap tiga pilar dokumen ilmiah:
1. **Bahan Kuliah (*Course Materials / OpenCourseWare*)**: Slide, silabus, dan Buku Rancangan Pengajaran (BRP) dari 14 fakultas OCW UI.
2. **Artikel Jurnal Ilmiah (*Research Papers*)**: Publikasi ilmiah mutakhir dari arXiv dan Directory of Open Access Journals (DOAJ).
3. **Karya Ilmiah Mahasiswa (*Theses / Dissertations*)**: Skripsi dan tugas akhir komputasi & sistem informasi.

### Karakteristik Korpus & Indeks Terkini
- **Total Dokumen:** 1.364 dokumen akademik.
- **Total Chunks Terindeks:** 57.202 potongan teks granular (jendela geser 200–400 kata, *overlap* 50 kata).
- **Ruang Kosakata (*Vocabulary Space*):** 1.969.538 term (kombinasi unigram dan bigram).
- **Dual Retrieval Engine:**
  - **Baseline A:** TF-IDF (Sublinear TF, Smooth IDF) + Cosine Similarity.
  - **Baseline B:** Okapi BM25 ($k_1=1.5, b=0.75$) dengan *inverted index* in-memory.
- **Document-Level Aggregation:** Mencegah satu skripsi tebal memonopoli hasil pencarian dengan mengagregasi skor potongan ke tingkat dokumen utuh via strategi `max+2nd` ($\lambda=0.3$).
- **Provenance Transparency:** Mendokumentasikan status akses korpus publik sebagai *benchmark proxy* melalui endpoint `/api/provenance`.

---

## 📊 Hasil Evaluasi & Benchmark Ilmiah

Berdasarkan pengujian otomatis pada **33 kueri akademik terstruktur** (mencakup 6 taksonomi kueri IREval) dengan **942 penilaian relevansi bergradasi (*qrels*)**:

| Metrik Evaluasi | Baseline A: TF-IDF (VSM) | Baseline B: BM25 Okapi | Selisih ($\Delta$) | Peningkatan Relatif |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Average Precision (MAP)** | **0.0832** | **0.1235** | **+0.0403** | **+48.4%** |
| **Mean Reciprocal Rank (MRR)** | **0.3990** | **0.4270** | **+0.0280** | **+7.0%** |
| **Precision@5 (P@5)** | **0.2667** | **0.2848** | **+0.0181** | **+6.8%** |
| **Precision@10 (P@10)** | **0.2182** | **0.2364** | **+0.0182** | **+8.3%** |
| **Recall@10 (R@10)** | **0.1186** | **0.1506** | **+0.0320** | **+27.0%** |
| **NDCG@10** | **0.2490** | **0.2992** | **+0.0502** | **+20.2%** |

### Benchmark Latensi Operasional (pada 56.881 chunks)
- **BM25 Okapi:** **P50 = 85,95 ms** | **P95 = 104,89 ms** (hampir 10x lebih cepat daripada TF-IDF VSM: P50 = 766,92 ms).
- Memenuhi target Service Level Agreement sistem ($\le 250$ ms) dengan margin yang aman.

---

## 🏗️ Arsitektur Perangkat Lunak

```text
[ Pengguna / Browser ]
         │
         │ HTTP / JSON (Port 3000)
         ▼
[ Presentation Tier: Next.js 15 + Tailwind CSS + shadcn/ui ]
  - Search Bar dengan Debounce & Sanitasi Event
  - Filter Sidebar: Model Switcher (TF-IDF vs BM25) & Agregasi (max, max+2nd, topN_avg)
  - Result Cards: Label Kualitatif (Sangat Relevan/Relevan), Bukti Halaman, & Provenance
         │
         │ REST API (Port 8000)
         ▼
[ Application Tier: FastAPI Backend Server ]
  - /api/search      : Parameter retrieval_mode, aggregation_strategy, candidate_k
  - /api/provenance  : Metadata legalitas & sumber korpus
  - /api/health      : Health check status indeks
  - /api/stats       : Statistik agregat korpus
         │
         ├── Preprocessing Pipeline (Case folding, Stopwords Tala/NLTK, Stemming Sastrawi/Snowball)
         ├── Candidate Pool Selection (candidate_k = 500)
         ├── Document-Level Aggregation (src/retrieval/aggregation.py)
         │
         ▼
[ Persistence & Model Tier ]
  ├── SQLite Database (academic_ir.db) -> Metadata Dokumen, Halaman & Chunks
  ├── TF-IDF Vector Space Index        -> tfidf_vectorizer.pkl & tfidf_matrix.npz
  └── BM25 Okapi Index                 -> bm25_v1/bm25_index.pkl
```

---

## 🚀 Panduan Menjalankan Sistem Dari Nol (*Setup From Scratch*)

Berikut adalah instruksi lengkap untuk menyiapkan dan menjalankan seluruh sistem dari awal pada mesin atau perangkat baru.

### 1. Prasyarat Lingkungan (*Prerequisites*)
Pastikan perangkat Anda telah terinstal:
- **Git** (`git --version`)
- **Python 3.10+** (`python --version`)
- **Node.js 18+ atau 20+ LTS** (`node --version`) dan **npm**

---

### 2. Clone Repositori
```bash
git clone https://github.com/pramacoder/TemuKembaliInformasi.git
cd TemuKembaliInformasi
```

---

### 3. Setup Lingkungan Python & Dependensi Backend
Masuk ke direktori backend `academic-ir`:
```bash
cd academic-ir
```

Buat dan aktifkan virtual environment:
```powershell
# Di Windows (PowerShell):
python -m venv venv
.\venv\Scripts\activate

# Di macOS / Linux:
python3 -m venv venv
source venv/bin/activate
```

Install seluruh dependensi backend:
```bash
pip install -r requirements.txt
pip install rank-bm25
```

---

### 4. Pembangunan Basis Data & Indeks Model (*Build From Scratch*)

Jika Anda menjalankan dari nol (database belum ada):

#### A. Pengumpulan / Ingestion Data Korpus
Jalankan skrip panen data untuk mengisi database SQLite:
```bash
# Opsi 1: Panen korpus multi-sumber (OCW UI, arXiv, Repositori)
python scripts/harvest_large_corpus.py

# Opsi 2: Atau jalankan kolektor spesifik (misal OCW UI semua fakultas)
python scripts/collect_materials_all_prodi.py
```

#### B. Pembangunan Indeks TF-IDF
Latih dan bentuk representasi ruang vektor (*Vector Space Model*):
```bash
python scripts/build_index.py
```
*Output: Menghasilkan `models/tfidf_vectorizer.pkl`, `models/tfidf_matrix.npz`, dan `models/chunk_ids.pkl`.*

#### C. Pembangunan Indeks BM25
Bentuk indeks terbalik (*inverted index*) Okapi BM25:
```bash
python scripts/build_bm25_index.py
```
*Output: Menghasilkan `models/bm25_v1/bm25_index.pkl`.*

#### D. Membangun Ground Truth & Menjalankan Evaluasi Benchmark
```bash
# Bangun 942 penilaian relevansi ground truth untuk 33 kueri
python scripts/build_comprehensive_qrels.py

# Eksekusi full benchmark TF-IDF vs BM25 (menghasilkan tabel komparasi & analisis galat)
python scripts/run_full_benchmark.py

# Eksekusi uji latensi P50/P95/P99
python scripts/benchmark_latency.py
```

---

### 5. Menjalankan Backend API (FastAPI)
Pastikan virtual environment aktif di direktori `academic-ir`:
```powershell
python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```
- Endpoint API siap melayani di: `http://127.0.0.1:8000`
- Dokumentasi Swagger interaktif: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

---

### 6. Menjalankan Frontend Web (Next.js 15)
Buka terminal baru, masuk ke direktori frontend:
```bash
cd academic-ir/academic-ir-frontend
```

Install dependensi Node.js:
```bash
npm install
```

Jalankan server pengembangan:
```bash
npm run dev
```

Buka peramban (*browser*) Anda pada:
👉 **`http://localhost:3000`**

---

## 📂 Struktur Direktori Proyek

```text
TemuKembaliInformasi/
├── README.md                              ← Dokumentasi Utama Sistem
├── LAPORAN_PROJECT_TAHAP_1.md             ← Laporan Akademik Lengkap Tahap I
│
└── academic-ir/
    ├── app/
    │   ├── api.py                         ← FastAPI REST Controller
    │   └── bm25_loader.py                 ← Lazy Loader Singleton BM25
    │
    ├── src/
    │   ├── collectors/                    ← Scraper OCW UI, arXiv, Repositori
    │   ├── database/                      ← Skema & Operasi SQLite
    │   ├── preprocessing/                 ← Pipeline Tokenisasi, Stopwords, Stemmer
    │   ├── indexing/                      ← TF-IDF CSR Matrix Indexer
    │   ├── retrieval/
    │   │   ├── search.py                  ← TF-IDF Search Engine & Pre-filtering
    │   │   ├── bm25.py                    ← Okapi BM25 Retrieval Engine
    │   │   └── aggregation.py             ← Modul Agregasi Dokumen (max, max+2nd, topN)
    │   └── evaluation/
    │       └── metrics.py                 ← P@K, R@K, MAP, NDCG@K, MRR
    │
    ├── evaluation/
    │   ├── queries.csv                    ← 33 Kueri Benchmark (Kategori A-F)
    │   ├── qrels.csv                      ← 942 Penilaian Relevansi Ground Truth
    │   ├── judging_guide.md               ← Panduan Penilaian Relevansi
    │   └── results/                       ← Laporan Evaluasi & Error Analysis
    │
    ├── data/
    │   ├── manifests/                     ← Metadata Manifest (material, research, thesis)
    │   └── provenance/                    ← corpus_sources.json (Legalitas & Akses Data)
    │
    ├── models/                            ← Serialisasi Model TF-IDF & BM25
    ├── scripts/                           ← Skrip Ingestion, Indexing, & Benchmark
    │
    └── academic-ir-frontend/              ← Frontend Next.js 15
        ├── src/
        │   ├── app/                       ← Next.js App Router (page.tsx, layout.tsx)
        │   ├── components/                ← SearchBar, FilterSidebar, ResultCard
        │   └── lib/api.ts                 ← Client API Fetcher
        └── package.json
```

---

## 📜 Lisensi & Etika Data

- Sistem ini mematuhi standar etika penambangan data publik (*polite scraping rate-limiting* dan kepatuhan `robots.txt`).
- Korpus publik digunakan secara transparan sebagai *reproducible benchmark proxy*.
- Lisensi kode terbuka untuk keperluan pendidikan dan riset akademik.
