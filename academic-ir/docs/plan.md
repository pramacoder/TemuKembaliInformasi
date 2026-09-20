# PLAN.md — Eksekusi Tahap Awal Academic Corpus: Scraping → Data Collection

## 1. Tujuan

Tahap pertama proyek adalah **menghasilkan Academic Corpus yang benar-benar dapat digunakan**, bukan langsung membangun mesin pencarian.

Target arsitektur awal:

```text
                         ACADEMIC CORPUS
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
           MATERIAL         RESEARCH          THESIS
            CORPUS           CORPUS           CORPUS
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                         UNIFIED CORPUS
                               │
                               ▼
                         UNIFIED INDEX
```

Konsep pencarian yang dipilih:

```text
                    ┌──────────────────────┐
                    │      SEARCH BAR      │
                    │ "machine learning"   │
                    └──────────┬───────────┘
                               │
                               ▼
                       QUERY PROCESSING
                               │
                               ▼
                    ┌──────────────────────┐
                    │    UNIFIED INDEX     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
          MATERIAL          RESEARCH          THESIS
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                         TOP-K RESULTS
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
              Material      Research       Thesis
```

Satu query dapat mengembalikan tiga jenis dokumen sekaligus. Pengguna kemudian dapat melakukan filter berdasarkan `document_type`, bahasa, tahun, institusi, dan sumber.

---

# 2. Prinsip Utama Tahap Scraping

## 2.1 Jangan langsung melakukan scraping besar-besaran

Urutan eksekusi:

```text
Source Validation
      ↓
Small Pilot Collection
      ↓
Metadata Validation
      ↓
File/Text Download
      ↓
Extraction Validation
      ↓
Deduplication
      ↓
Corpus Organization
      ↓
Collection Report
      ↓
Scale Up
```

Tujuan pilot adalah memastikan pipeline bekerja sebelum mengunduh ribuan dokumen.

## 2.2 Gunakan sumber berdasarkan cara aksesnya

Prioritas:

1. Official API
2. OAI-PMH
3. Official bulk/data dump
4. Halaman publik yang memang menyediakan file
5. Scraping HTML hanya jika diperlukan dan diizinkan

Jangan bypass login, paywall, robots.txt, rate limit, atau kontrol akses.

---

# 3. Target Corpus

Untuk tahap awal, gunakan tiga corpus utama.

| Corpus | `document_type` | Isi |
|---|---|---|
| Material | `MATERIAL` | Materi kuliah, lecture notes, modul |
| Research | `RESEARCH` | Journal article, research paper, conference paper, preprint |
| Thesis | `THESIS` | Skripsi, tesis, disertasi, academic research report |

Jangan mencampur semua file ke satu folder tanpa metadata. Setiap dokumen harus memiliki identitas corpus.

Struktur:

```text
data/
├── raw/
│   ├── material/
│   ├── research/
│   └── thesis/
│
├── extracted/
│   ├── material/
│   ├── research/
│   └── thesis/
│
├── metadata/
│   ├── material.jsonl
│   ├── research.jsonl
│   └── thesis.jsonl
│
├── manifests/
│   ├── material_manifest.csv
│   ├── research_manifest.csv
│   └── thesis_manifest.csv
│
└── reports/
    ├── collection_report.md
    ├── extraction_report.csv
    └── duplicate_report.csv
```

---

# 4. Bahasa Corpus

Karena sebagian besar literatur akademik yang akan digunakan berbahasa Inggris, **English menjadi bahasa utama corpus**, tetapi sistem sebaiknya tetap menyimpan informasi bahasa.

Gunakan field:

```text
language
language_confidence
```

Contoh:

```json
{
  "language": "en",
  "language_confidence": 0.98
}
```

atau:

```json
{
  "language": "id",
  "language_confidence": 0.97
}
```

Jangan membuat preprocessing Bahasa Indonesia sebagai aturan wajib untuk semua dokumen.

Contoh masalah jika preprocessing Indonesia diterapkan ke jurnal Inggris:

```text
English document
      ↓
Indonesian stopword removal
      ↓
informasi penting dapat salah diperlakukan
```

Gunakan preprocessing yang mempertimbangkan bahasa dokumen.

---

# 5. Sumber Data Tahap Awal

## 5.1 MATERIAL — UI Open Courseware

Gunakan **UI Open Courseware** sebagai sumber material awal.

Website:

https://ocw.ui.ac.id/

OCW UI menyediakan materi kuliah secara daring dan menyatakan bahwa materi dapat diakses/diunduh secara gratis. Halaman utama juga mencantumkan materi seperti Academic Writing, Bioinformatics, Algoritma dan Pemrograman, dan lainnya.

Lisensi yang tercantum pada halaman utama OCW UI adalah Creative Commons BY-NC-SA, kecuali jika materi tertentu dinyatakan berbeda.

### Target

```text
OCW UI
  ↓
Course
  ↓
Course page
  ↓
Material/resource link
  ↓
PDF / document
  ↓
raw/material/
```

### Metadata minimum

```text
source = "OCW_UI"
document_type = "MATERIAL"
course
title
url
file_url
filename
language
license
downloaded_at
sha256
```

---

# 6. RESEARCH — CORE

Gunakan CORE sebagai sumber utama untuk research corpus.

CORE menyediakan akses mesin terhadap metadata dan full text research papers melalui API. CORE juga mengagregasi konten dari institutional repositories, subject repositories, preprint servers, dan jurnal.

Website:

https://core.ac.uk/

API:

https://core.ac.uk/services/api

### Strategi

Jangan mencoba mengunduh seluruh CORE.

Gunakan query/topik yang sesuai dengan bidang proyek:

```text
information retrieval
natural language processing
text mining
machine learning
information extraction
document retrieval
academic information retrieval
text classification
document similarity
```

Kemudian simpan hanya subset yang relevan.

### Target pilot

```text
100–300 research documents
```

Bukan jutaan dokumen.

### Metadata minimum

```text
source
document_type
title
authors
abstract
year
keywords
doi
url
fulltext_url
language
license
filename
sha256
downloaded_at
```

---

# 7. RESEARCH — DOAJ

DOAJ dapat digunakan sebagai sumber tambahan untuk artikel open access.

Website:

https://doaj.org/

DOAJ menyediakan OAI-PMH untuk metadata artikel dan journal. Feed OAI-PMH reguler terbuka untuk semua pengguna, dengan data yang diperbarui dalam periode sekitar 30 hari menurut dokumentasi DOAJ.

Endpoint OAI-PMH:

https://doaj.org/oai.article

### Strategi

Gunakan DOAJ terutama untuk:

```text
metadata artikel
        +
full-text URL
        ↓
download artikel yang memang tersedia secara terbuka
```

Jangan menganggap metadata DOAJ berarti isi artikel bebas digunakan. Simpan informasi lisensi dan cek hak penggunaan dokumen/full text.

### Target pilot

```text
100–300 research documents
```

DOAJ tidak perlu langsung dijadikan corpus utama jika CORE sudah memberikan cukup dokumen berkualitas untuk pilot.

---

# 8. THESIS — Institutional Repositories

Untuk thesis corpus, gunakan institutional repositories yang secara resmi menyediakan karya ilmiah secara terbuka.

Prioritas:

```text
University Repository
        ↓
Thesis / Undergraduate Thesis
        ↓
Public full-text PDF
```

Contoh target:

```text
repository universitas
institutional repository
open thesis repository
open dissertation repository
```

Untuk setiap repository, lakukan validasi terlebih dahulu:

- Apakah PDF dapat diakses publik?
- Apakah crawling diperbolehkan?
- Apakah terdapat robots.txt?
- Apakah ada batas request?
- Apakah lisensi/terms penggunaan jelas?
- Apakah metadata lengkap?
- Apakah file thesis benar-benar dapat diunduh?

### Target pilot

```text
50–150 thesis documents
```

Jangan mengejar jumlah besar sebelum kualitas metadata dan extraction terbukti.

---

# 9. Struktur Metadata Unified

Walaupun sumber berbeda, seluruh dokumen harus dinormalisasi ke schema yang sama.

Gunakan:

```json
{
  "document_id": "DOC-000001",
  "document_type": "RESEARCH",
  "title": "...",
  "abstract": "...",
  "authors": [],
  "institution": "...",
  "department": "...",
  "course": null,
  "year": 2025,
  "language": "en",
  "language_confidence": 0.98,
  "keywords": [],
  "source": "CORE",
  "source_url": "...",
  "fulltext_url": "...",
  "local_path": "...",
  "file_type": "pdf",
  "file_size": 1234567,
  "page_count": 10,
  "license": "...",
  "sha256": "...",
  "extraction_method": "pymupdf",
  "extraction_status": "success",
  "collection_status": "complete",
  "collected_at": "..."
}
```

Field yang boleh `null`:

```text
abstract
authors
institution
department
course
keywords
doi
license
```

Jangan membuang dokumen hanya karena salah satu metadata tidak tersedia.

---

# 10. ID Dokumen

Jangan menggunakan filename sebagai primary identity.

Gunakan:

```text
document_id
```

Contoh:

```text
MAT-000001
MAT-000002

RES-000001
RES-000002

THS-000001
THS-000002
```

Kemudian gunakan hash untuk duplicate detection:

```text
sha256
```

Contoh:

```text
document_id = RES-000124
sha256 = 9f83...abc
```

Jika dua URL menghasilkan file dengan SHA-256 yang sama:

```text
URL A ──┐
        ├── same SHA256 → duplicate
URL B ──┘
```

---

# 11. Data Collection Pipeline

Implementasikan pipeline berikut:

```text
SOURCE
  │
  ▼
DISCOVERY
  │
  ├── URL
  ├── metadata
  └── source identifier
  │
  ▼
VALIDATION
  │
  ├── public?
  ├── allowed?
  ├── relevant?
  └── supported format?
  │
  ▼
DOWNLOAD
  │
  ├── PDF
  ├── HTML
  └── other
  │
  ▼
FILE VALIDATION
  │
  ├── status code
  ├── content type
  ├── file size
  └── readable?
  │
  ▼
HASH
  │
  ▼
DEDUPLICATION
  │
  ▼
TEXT EXTRACTION
  │
  ├── PyMuPDF
  └── OCR fallback
  │
  ▼
TEXT VALIDATION
  │
  ├── character count
  ├── word count
  └── extraction quality
  │
  ▼
LANGUAGE DETECTION
  │
  ▼
METADATA NORMALIZATION
  │
  ▼
SAVE
  │
  ├── raw/
  ├── extracted/
  └── metadata/
```

---

# 12. Tahap 1 — Buat Project Skeleton

Struktur:

```text
academic-ir/
│
├── data/
│   ├── raw/
│   ├── extracted/
│   ├── metadata/
│   ├── manifests/
│   └── reports/
│
├── src/
│   ├── collectors/
│   │   ├── ocw_ui.py
│   │   ├── core.py
│   │   ├── doaj.py
│   │   └── repository.py
│   │
│   ├── extraction/
│   │   ├── pdf.py
│   │   └── ocr.py
│   │
│   ├── normalization/
│   │   ├── metadata.py
│   │   └── language.py
│   │
│   ├── validation/
│   │   ├── files.py
│   │   └── corpus.py
│   │
│   └── dedup/
│       └── hash.py
│
├── scripts/
│   ├── collect_ocw.py
│   ├── collect_core.py
│   ├── collect_doaj.py
│   └── validate_corpus.py
│
├── config/
│   └── sources.yaml
│
├── requirements.txt
└── README.md
```

---

# 13. Tahap 2 — Dependencies

Minimal:

```text
requests
beautifulsoup4
pymupdf
pandas
numpy
scikit-learn
langdetect
tqdm
python-dotenv
```

Untuk OCR fallback, tambahkan:

```text
pytesseract
```

dan engine OCR yang sesuai pada environment.

Catatan:

- `requests` → HTTP request
- `BeautifulSoup` → parsing HTML
- `PyMuPDF` → PDF extraction
- `pandas` → manifest/metadata
- `langdetect` → language detection awal
- `tqdm` → progress
- `python-dotenv` → API key
- `pytesseract` → OCR fallback

---

# 14. Tahap 3 — Configuration

Jangan hard-code semua URL dan parameter di source code.

Gunakan:

```yaml
sources:

  ocw_ui:
    enabled: true
    type: material
    base_url: "https://ocw.ui.ac.id/"

  core:
    enabled: true
    type: research
    api_key_env: "CORE_API_KEY"

  doaj:
    enabled: true
    type: research

  repositories:
    enabled: false
    type: thesis
```

Keuntungan:

```text
ubah sumber
    ↓
ubah config
    ↓
tidak perlu mengubah pipeline utama
```

---

# 15. Tahap 4 — Pilot Scraping MATERIAL

Jangan langsung mengambil semua course.

Ambil beberapa course terlebih dahulu.

Contoh:

```text
3–5 courses
```

Untuk setiap course:

```text
course page
   ↓
find resource links
   ↓
filter PDF/document
   ↓
download
   ↓
save metadata
```

Output yang diharapkan:

```text
data/raw/material/
├── MAT-000001.pdf
├── MAT-000002.pdf
├── MAT-000003.pdf
└── ...
```

Dan:

```text
data/metadata/material.jsonl
```

---

# 16. Tahap 5 — Pilot Scraping RESEARCH

Mulai dari CORE.

Target:

```text
100 documents
```

Gunakan query relevan terhadap project.

Contoh:

```text
"information retrieval"
"document retrieval"
"text mining"
"information extraction"
"natural language processing"
"document similarity"
```

Jangan memasukkan semua paper hanya karena mengandung kata `machine learning`.

Gunakan relevance filtering awal.

Contoh:

```text
query/topic relevance
        ↓
metadata screening
        ↓
full text available?
        ↓
download
```

---

# 17. Tahap 6 — Pilot DOAJ

Setelah CORE pipeline berhasil:

```text
DOAJ
 ↓
OAI-PMH metadata
 ↓
filter relevant records
 ↓
full-text URL
 ↓
download allowed/open full text
 ↓
normalize
```

Target awal:

```text
50–100 documents
```

Tujuannya bukan menambah jumlah sebanyak mungkin, tetapi menguji apakah dua source research dapat masuk ke schema yang sama.

---

# 18. Tahap 7 — Pilot THESIS

Pilih 1 repository terlebih dahulu.

Jangan langsung banyak repository.

Target:

```text
50 thesis
```

Pipeline:

```text
Repository
   ↓
search/browse
   ↓
metadata
   ↓
public PDF
   ↓
download
   ↓
hash
   ↓
extract
   ↓
language detection
   ↓
metadata normalization
```

Jika satu repository berhasil, baru tambahkan repository kedua.

---

# 19. Tahap 8 — PDF Validation

Setiap PDF harus diperiksa.

Minimal:

```text
HTTP status = 200
Content-Type sesuai
file size > minimum
PDF dapat dibuka
page_count > 0
```

Kemudian extraction:

```text
PDF
 ↓
PyMuPDF
 ↓
text
```

Hitung:

```text
character_count
word_count
page_count
```

Contoh aturan sederhana:

```text
word_count < 100
       ↓
suspect extraction failure
       ↓
OCR fallback
```

Threshold tersebut adalah parameter awal dan perlu diuji pada dataset nyata.

---

# 20. Tahap 9 — Extraction Quality

Buat status:

```text
SUCCESS
PARTIAL
FAILED
OCR_REQUIRED
```

Contoh:

```json
{
  "document_id": "RES-000123",
  "extraction_status": "SUCCESS",
  "extraction_method": "pymupdf",
  "word_count": 6240
}
```

Jika PDF scan:

```json
{
  "document_id": "THS-000031",
  "extraction_status": "OCR_REQUIRED",
  "extraction_method": "ocr"
}
```

Jangan menghapus PDF asli ketika extraction gagal.

---

# 21. Tahap 10 — Deduplication

Lakukan dua level.

## Level 1 — Exact duplicate

```text
SHA-256
```

Jika:

```text
hash_A == hash_B
```

maka file identik.

## Level 2 — Near duplicate

Untuk tahap awal belum perlu rumit.

Gunakan kombinasi:

```text
normalized title
+
authors
+
year
+
DOI
```

Contoh:

```text
same DOI → kemungkinan dokumen yang sama
```

Near-duplicate berbasis isi dapat ditambahkan setelah corpus awal berhasil dikumpulkan.

---

# 22. Tahap 11 — Unified Manifest

Semua corpus harus dapat digabung:

```text
material_manifest.csv
research_manifest.csv
thesis_manifest.csv
```

menjadi:

```text
unified_manifest.csv
```

Contoh:

```text
document_id,document_type,title,language,year,source,local_path,sha256,status
MAT-000001,MATERIAL,...,en,2024,OCW_UI,...,abc...,complete
RES-000001,RESEARCH,...,en,2025,CORE,...,def...,complete
THS-000001,THESIS,...,id,2023,Repository,...,ghi...,complete
```

**Inilah fondasi Unified Index nantinya.**

---

# 23. Database: Jangan MongoDB Dulu

Untuk tahap collection awal, gunakan:

```text
Filesystem
+
SQLite
+
JSONL/CSV manifest
```

Struktur:

```text
PDF → filesystem

metadata → SQLite

raw metadata → JSONL

TF-IDF index → nanti
```

MongoDB belum diperlukan.

Alasannya:

```text
PDF ≠ harus MongoDB
```

PDF adalah file binary. Setelah diekstrak:

```text
document
 ├── metadata
 ├── pages
 └── text
```

Data tersebut tetap dapat disimpan secara efisien dengan filesystem + SQLite.

MongoDB baru dipertimbangkan jika struktur metadata menjadi sangat nested/dinamis dan kebutuhan query memang membutuhkan document database.

---

# 24. SQLite Schema Awal

Buat tabel:

```sql
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    document_type TEXT NOT NULL,
    title TEXT,
    abstract TEXT,
    authors TEXT,
    institution TEXT,
    department TEXT,
    course TEXT,
    year INTEGER,
    language TEXT,
    language_confidence REAL,
    keywords TEXT,
    source TEXT,
    source_url TEXT,
    fulltext_url TEXT,
    local_path TEXT,
    file_type TEXT,
    file_size INTEGER,
    page_count INTEGER,
    license TEXT,
    sha256 TEXT UNIQUE,
    extraction_method TEXT,
    extraction_status TEXT,
    collection_status TEXT,
    collected_at TEXT
);
```

Untuk tahap collection, ini sudah cukup.

---

# 25. Kriteria "Data Berhasil Dikoleksi"

Tahap scraping **belum dianggap selesai hanya karena file PDF berhasil didownload**.

Sebuah dokumen dianggap `READY_FOR_INDEXING` jika:

```text
[✓] document_id tersedia
[✓] document_type tersedia
[✓] title tersedia atau dapat diekstrak
[✓] source tersedia
[✓] source_url tersedia
[✓] file tersimpan
[✓] SHA-256 tersedia
[✓] PDF valid
[✓] text berhasil diekstrak
[✓] extraction_status = SUCCESS/OCR
[✓] language terdeteksi
[✓] tidak duplicate
[✓] metadata tersimpan
```

Status:

```text
DOWNLOADED
    ↓
VALIDATED
    ↓
EXTRACTED
    ↓
NORMALIZED
    ↓
DEDUPLICATED
    ↓
READY_FOR_INDEXING
```

---

# 26. Target Dataset MVP

Jangan mengejar corpus besar terlebih dahulu.

Target MVP:

| Corpus | Target awal |
|---|---:|
| MATERIAL | 100–200 |
| RESEARCH | 200–400 |
| THESIS | 50–100 |
| **TOTAL** | **350–700** |

Tujuan MVP:

1. membuktikan ingestion pipeline;
2. membuktikan unified metadata;
3. menguji extraction;
4. menguji deduplication;
5. memastikan English + Indonesian dapat ditangani;
6. menyiapkan data untuk TF-IDF/VSM.

Setelah pipeline stabil, baru scale-up.

---

# 27. Target Dataset Setelah Pipeline Stabil

Contoh target tahap berikutnya:

```text
MATERIAL
500–2,000

RESEARCH
1,000–5,000

THESIS
500–2,000
```

Tidak perlu memaksakan angka tertentu. Jumlah akhir harus mengikuti kapasitas storage, kualitas data, izin akses, dan kebutuhan eksperimen.

**Kualitas dan konsistensi metadata lebih penting daripada jumlah PDF semata.**

---

# 28. Unified Search: Konsep Sistem

Setelah corpus selesai:

```text
                         SEARCH BAR
                              │
                              ▼
                        Query Processing
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Language Detect      Normalization
                    │                   │
                    └─────────┬─────────┘
                              ▼
                       UNIFIED INDEX
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
           MATERIAL        RESEARCH        THESIS
               │              │              │
               └──────────────┼──────────────┘
                              ▼
                       COSINE SIMILARITY
                              │
                              ▼
                         GLOBAL TOP-K
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
         MATERIAL          RESEARCH           THESIS
```

Artinya user tidak perlu memilih corpus terlebih dahulu.

Contoh query:

```text
"deep learning for medical image classification"
```

hasil:

```text
1. Research — CNN for Medical Image Classification
2. Material — Deep Learning Lecture Notes
3. Thesis — Medical Image Classification Using CNN
4. Research — Transfer Learning...
5. Material — Neural Network Module
```

Semua berasal dari satu unified search.

---

# 29. Jangan Menghapus `document_type`

Walaupun search bar unified, metadata tetap harus menyimpan:

```text
MATERIAL
RESEARCH
THESIS
```

Karena UI dapat menyediakan filter:

```text
Search:
[ machine learning __________________ ]

Filter:
☑ All
☐ Material
☐ Research
☐ Thesis

Language:
☑ English
☐ Indonesian

Year:
[2021] – [2026]

Source:
☑ OCW UI
☑ CORE
☑ DOAJ
☑ Repository
```

Default:

```text
All
```

Jadi konsepnya:

> **Unified retrieval, separated metadata.**

Bukan:

> semua data dicampur tanpa identitas.

---

# 30. English sebagai Bahasa Utama

Gunakan English sebagai bahasa utama untuk retrieval experiment, tetapi jangan memaksa semua corpus menjadi English.

Corpus:

```text
English
   │
   ├── Research
   ├── Material
   └── Thesis

Indonesian
   │
   ├── Research
   └── Thesis
```

Untuk baseline pertama:

```text
TF-IDF
+
unigram
+
bigram
+
English stopword
```

Kemudian evaluasi corpus Indonesia secara terpisah.

Untuk multilingual retrieval, tahap berikutnya dapat menggunakan:

```text
language-aware preprocessing
```

dan kemudian membandingkannya dengan pendekatan multilingual.

---

# 31. Search Result Schema

Nantinya hasil retrieval minimal:

```json
{
  "rank": 1,
  "document_id": "RES-000123",
  "document_type": "RESEARCH",
  "title": "Information Retrieval ...",
  "score": 0.8234,
  "language": "en",
  "year": 2025,
  "source": "CORE",
  "page": 4,
  "snippet": "..."
}
```

Perhatikan:

```text
score
+
document_type
+
source
+
page
+
snippet
```

Ini penting agar search engine tidak hanya mengatakan:

```text
"Dokumen ditemukan."
```

tetapi juga menunjukkan **mengapa dan di mana informasi relevan ditemukan**.

---

# 32. Tahapan Eksekusi yang Harus Dikerjakan Sekarang

## Sprint 1 — Setup

- [ ] Buat repository/project
- [ ] Buat struktur folder
- [ ] Buat virtual environment
- [ ] Install dependencies
- [ ] Buat `sources.yaml`
- [ ] Buat SQLite database
- [ ] Buat schema `documents`

**Output:**

```text
Project skeleton siap
```

---

## Sprint 2 — MATERIAL

- [ ] Buat collector OCW UI
- [ ] Ambil 3–5 course
- [ ] Temukan resource/PDF
- [ ] Download 100–200 dokumen
- [ ] Hitung SHA-256
- [ ] Extract text
- [ ] Detect language
- [ ] Simpan metadata
- [ ] Validasi manifest

**Output:**

```text
MATERIAL corpus siap
```

---

## Sprint 3 — RESEARCH

- [ ] Daftar CORE API
- [ ] Buat API client
- [ ] Tentukan 5–10 topik
- [ ] Ambil metadata
- [ ] Filter relevance
- [ ] Download subset full text
- [ ] Extract
- [ ] Hash
- [ ] Language detection
- [ ] Normalize

**Output:**

```text
RESEARCH corpus siap
```

---

## Sprint 4 — DOAJ

- [ ] Test OAI-PMH
- [ ] Ambil metadata
- [ ] Filter topik
- [ ] Validasi full-text URL
- [ ] Download sample
- [ ] Normalize ke schema unified

**Output:**

```text
Second research source berhasil masuk pipeline
```

---

## Sprint 5 — THESIS

- [ ] Pilih 1 institutional repository
- [ ] Validasi access/robots/license
- [ ] Buat collector
- [ ] Ambil 50–100 thesis
- [ ] Download PDF
- [ ] Extract
- [ ] Hash
- [ ] Language detection
- [ ] Normalize

**Output:**

```text
THESIS corpus siap
```

---

## Sprint 6 — Unified Corpus

- [ ] Gabungkan manifest
- [ ] Validasi document ID
- [ ] Cek duplicate
- [ ] Cek missing metadata
- [ ] Cek failed extraction
- [ ] Buat collection report
- [ ] Tandai `READY_FOR_INDEXING`

**Output:**

```text
UNIFIED CORPUS
350–700 documents
```

---

# 33. Collection Report

Buat report otomatis:

```text
ACADEMIC CORPUS COLLECTION REPORT
==================================

Total documents:
xxx

MATERIAL:
xxx

RESEARCH:
xxx

THESIS:
xxx

Language:
English: xxx
Indonesian: xxx
Other: xxx

Extraction:
Success: xxx
OCR: xxx
Failed: xxx

Duplicate:
Exact duplicate: xxx
Near duplicate: xxx

Source:
OCW UI: xxx
CORE: xxx
DOAJ: xxx
Repository: xxx

Ready for indexing:
xxx
```

Report ini akan sangat berguna ketika menjelaskan dataset dalam laporan tugas/TA.

---

# 34. Quality Gate Sebelum Masuk Unified Index

Gunakan aturan:

```text
                    DOCUMENT
                        │
                        ▼
                 File Valid?
                  /        \
                NO          YES
                │             │
              REJECT          ▼
                         Text Extracted?
                          /          \
                        NO            YES
                        │               │
                       OCR              ▼
                        │          Language?
                        │               │
                        └───────┬───────┘
                                ▼
                           Duplicate?
                           /       \
                         YES        NO
                         │           │
                      MERGE          ▼
                                READY_FOR_INDEXING
```

Dokumen yang gagal jangan langsung dihapus.

Simpan statusnya agar masalah dapat ditelusuri.

---

# 35. Definition of Done

Tahap **Scraping → Data Collection** dianggap selesai apabila:

```text
[✓] 3 corpus tersedia
[✓] setiap dokumen punya document_id
[✓] metadata menggunakan unified schema
[✓] file original tersimpan
[✓] hash tersedia
[✓] duplicate terdeteksi
[✓] text berhasil diekstrak
[✓] OCR fallback tersedia
[✓] language terdeteksi
[✓] source dan URL tersimpan
[✓] license/access information disimpan jika tersedia
[✓] unified_manifest.csv tersedia
[✓] SQLite terisi
[✓] collection report tersedia
[✓] minimal 350 dokumen pilot siap
```

Baru setelah semua ini selesai, lanjut ke:

```text
UNIFIED CORPUS
      ↓
PREPROCESSING
      ↓
CHUNKING
      ↓
TF-IDF
      ↓
VSM
      ↓
COSINE SIMILARITY
      ↓
UNIFIED INDEX
      ↓
SEARCH ENGINE
```

---

# 36. Arsitektur Akhir yang Ditargetkan

```text
                    ┌──────────────────────┐
                    │    ACADEMIC SOURCES  │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
       OCW UI                 CORE                 DOAJ
      MATERIAL             RESEARCH              RESEARCH
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                     Institutional
                      Repositories
                               │
                               ▼
                            THESIS
                               │
                               ▼
                    ┌─────────────────────┐
                    │   DATA COLLECTION   │
                    └──────────┬──────────┘
                               ▼
                       VALIDATION
                               ▼
                         DEDUPLICATION
                               ▼
                       TEXT EXTRACTION
                               ▼
                       LANGUAGE DETECTION
                               ▼
                     METADATA NORMALIZATION
                               ▼
                    ┌─────────────────────┐
                    │   UNIFIED CORPUS    │
                    │                     │
                    │ MATERIAL             │
                    │ RESEARCH             │
                    │ THESIS               │
                    └──────────┬──────────┘
                               ▼
                         PREPROCESSING
                               ▼
                            CHUNKING
                               ▼
                            TF-IDF
                               ▼
                       UNIFIED SPARSE INDEX
                               ▼
                       ┌───────────────┐
                       │   SEARCH BAR  │
                       └───────┬───────┘
                               ▼
                         GLOBAL RANKING
                               ▼
                         TOP-K RESULTS
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
             MATERIAL       RESEARCH        THESIS
```

---

# 37. Catatan Sumber dan Akses

Sumber resmi yang digunakan sebagai dasar rencana:

- UI Open Courseware: https://ocw.ui.ac.id/
- CORE: https://core.ac.uk/
- CORE API: https://core.ac.uk/services/api
- CORE Data: https://core.ac.uk/data
- DOAJ: https://doaj.org/
- DOAJ OAI-PMH: https://doaj.org/docs/oai-pmh/
- DOAJ Terms: https://doaj.org/terms/

Catatan penting:

- CORE menyediakan akses mesin ke metadata dan full text melalui API dan juga menyediakan dataset untuk pemrosesan di infrastruktur sendiri.
- DOAJ menyediakan metadata artikel melalui OAI-PMH dan endpoint lain; metadata artikel tersedia dengan CC0 menurut terms DOAJ, tetapi hak cipta atas karya yang dideskripsikan tetap merupakan hal yang terpisah.
- OCW UI menyatakan materi dapat diakses/diunduh secara gratis dan mencantumkan lisensi Creative Commons BY-NC-SA kecuali dinyatakan berbeda pada materi tertentu.
- Untuk institutional repositories, validasi aturan akses, robots.txt, terms, dan lisensi repository sebelum collection.

---

# 38. Prinsip Desain Final

Gunakan prinsip berikut sepanjang pengembangan:

```text
ONE SEARCH BAR
        +
MULTIPLE CORPORA
        +
UNIFIED METADATA
        +
PRESERVED DOCUMENT TYPE
        +
LANGUAGE-AWARE PROCESSING
        +
PROVENANCE
        +
DEDUPLICATION
        =
ACADEMIC IR SYSTEM
```

Jangan membangun:

```text
Material Search
Research Search
Thesis Search
```

sebagai tiga search engine terpisah.

Bangun:

```text
                    ONE SEARCH
                         │
                         ▼
                  UNIFIED INDEX
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      MATERIAL        RESEARCH        THESIS
```

dengan `document_type` sebagai metadata/filter, bukan sebagai batas search engine.

