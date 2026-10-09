# Implementation Plan: Text Summarization for Academic IR

**Tujuan:** Menambahkan fitur text summarization ke sistem Academic Information Retrieval (IR) yang sudah ada tanpa merusak TF-IDF, BM25, Tolerant Retrieval, atau hybrid retrieval.

---

## 1. Tujuan dan Batasan

Fitur ini membantu pengguna memahami dokumen hasil pencarian secara cepat dan akurat. Ringkasan tidak boleh digunakan untuk menyamarkan hasil retrieval yang kurang relevan.

Bedakan tiga hal:
- **Retrieval relevance:** apakah dokumen sesuai dengan kebutuhan informasi pengguna.
- **Summary quality:** apakah ringkasan akurat mewakili konten dokumen.
- **Information sufficiency:** apakah teks sumber cukup untuk menjawab kueri pengguna.

> Ringkasan tidak membuat dokumen yang tidak relevan menjadi relevan.

---

## 2. Instruksi Awal untuk AI Coding Agent

Sebelum mengubah kode, lakukan audit repository dan laporkan:
1. Framework backend dan struktur modul (`FastAPI` di `academic-ir/app/api.py`, `src/retrieval/`).
2. Pipeline ekstraksi PDF/HTML/teks yang sudah ada.
3. Schema dokumen dan chunk pada SQLite (`academic_ir.db`), termasuk kolom `document_id`, `abstract`, `clean_text`, `raw_text`, halaman, dan chunk index.
4. Database/storage yang digunakan (tabel `documents`, `pages`, `chunks`).
5. Pipeline retrieval dan schema response hasil pencarian (`SearchResponse`, `SearchResultItem`, `TolerantMetadataResponse`).
6. API endpoint dan komponen UI hasil pencarian di frontend (`Next.js 15`, `search-bar.tsx`, `result-card.tsx`, `page.tsx`).
7. Konvensi testing, logging, konfigurasi, dan dependency (`requirements.txt`, `package.json`).
8. Ketersediaan teks abstrak atau ringkasan sebelumnya.

Setelah audit, ajukan rencana implementasi minimal yang sesuai arsitektur saat ini. Jangan rewrite repository, mengganti search engine, atau menambah database baru tanpa alasan kuat. Pertahankan semua fitur retrieval leksikal dan toleransi yang sudah berjalan stabil.

---

## 3. Fitur yang Dibangun

### 3.1 Document Summary (Prioritas Pertama)
Pengguna dapat memilih tombol **Lihat Ringkasan** pada setiap kartu hasil pencarian (*ResultCard*). Ringkasan mencakup poin-poin utama: latar belakang/topik, tujuan, metode/algoritma, temuan, dan kesimpulan jika benar-benar tersedia di teks sumber dokumen. Jangan mengarang atau mengisi bagian yang tidak didukung teks dokumen asli.

### 3.2 Query-Focused Summary (Tahap Berikutnya)
Ringkasan berfokus pada bagian dokumen yang menjawab kueri spesifik pengguna. Jika bukti tidak tersedia atau tidak mencukupi, sistem wajib menyatakan keterbatasan tersebut (*insufficient evidence*). Jangan menyimpulkan jawaban dari kueri saja atau dari potongan dokumen yang tidak relevan.

---

## 4. Strategi Menangani Perbedaan Bahasa (Language-Aware Strategy)

Dalam korpus akademik nyata, perbedaan bahasa antardokumen merupakan tantangan fundamental:
- **Bahan Kuliah (Material):** Campuran slide Bahasa Indonesia dan Bahasa Inggris.
- **Skripsi / Tesis (Thesis):** Mayoritas Bahasa Indonesia baku dengan istilah teknis serapan asing.
- **Jurnal Riset (Research Papers):** Sebagian besar Bahasa Inggris internasional, atau artikel nasional dwibahasa (abstrak Inggris, isi Indonesia).

> **Prinsip Utama:** Jangan langsung menerjemahkan seluruh dokumen ke satu bahasa sebelum pemrosesan. Sistem mendeteksi bahasa, memproses teks sesuai karakteristik kebahasaannya, lalu menghasilkan ringkasan dengan bahasa yang sesuai kebutuhan pengguna.

### A. Language Detection
- Deteksi bahasa dilakukan pada tingkat dokumen, dan bila perlu pada tingkat potongan teks (*chunk/section level*).
- Klasifikasi kode bahasa:
  - `en`: Bahasa Inggris.
  - `id`: Bahasa Indonesia.
  - `mixed`: Dokumen campuran (misalnya slide atau naskah dwibahasa).
- Simpan hasil deteksi di metadata dokumen: `language` dan `language_confidence` (misalnya memanfaatkan metadata yang sudah ada di tabel `documents` atau dideteksi ulang secara on-demand).

### B. Language-Aware Preprocessing
Preprocessing disesuaikan dengan bahasa sumber dokumen:
- **Tokenisasi Kalimat & Kata:** Menggunakan segmenter yang sadar struktur kalimat masing-masing bahasa.
- **Stopword Removal Khusus:**
  - Bahasa Indonesia: Daftar stopword bahasa Indonesia (misalnya Sastrawi / Tala).
  - Bahasa Inggris: Daftar stopword bahasa Inggris (misalnya NLTK).
- **Perlindungan Istilah Teknis:** Pertahankan istilah teknis, singkatan, nama metode, simbol matematika, dan nama algoritma (`TF-IDF`, `BERT`, `C++`, `CNN-BiLSTM`, `support vector machine`, `random forest`).
- **Aturan Stemming:** **Dilarang keras** menerapkan stemming Bahasa Indonesia (Sastrawi) pada teks Bahasa Inggris, dan sebaliknya.

### C. Multilingual Extractive Summarization (Bahasa Asli Sumber)
Untuk baseline utama, gunakan kombinasi **TF-IDF + TextRank + MMR** pada teks asli setiap dokumen tanpa menerjemahkan dokumen terlebih dahulu:
- Ringkasan mengekstraksi dan mempertahankan kalimat-kalimat paling representatif dari dokumen asli.
- Pendekatan ekstraktif tidak memerlukan model generatif/LLM multibahasa berukuran raksasa.
- Kualitas dan integritas makna istilah akademik tetap terlindungi dari kesalahan halusinasi terjemahan.

### D. Optional Cross-Language Summary (Ringkasan Lintas Bahasa)
Jika pengguna secara eksplisit meminta ringkasan dalam Bahasa Indonesia dari jurnal berbahasa Inggris (atau sebaliknya):
- Tambahkan tahap penerjemahan pada ringkasan ekstraktif akhir, atau gunakan model abstraktif multibahasa yang sesuai.
- Tahap ini bersifat **opsional (add-on)** karena menambah kompleksitas komputasi, latensi, dan risiko pergeseran makna istilah teknis.

---

## 5. Algoritma yang Direkomendasikan

Pendekatan bertahap dirancang dengan perpaduan algoritma berikut:

| Komponen | Algoritma / Teknologi | Penanganan & Peran Bahasa |
| :--- | :--- | :--- |
| **Deteksi Bahasa** | `fastText` language identification atau `langdetect` | Mengidentifikasi bahasa dokumen (`id`, `en`, atau `mixed`) beserta skor keyakinan. |
| **Preprocessing** | Tokenisasi kalimat & stopword per bahasa | Bahasa Indonesia dan Inggris diproses sesuai aturan leksikal masing-masing; istilah teknis dilindungi. |
| **Representasi Kalimat** | **TF-IDF (Sentence-Level)** | Dibangun dari teks dokumen dalam bahasa yang sama untuk merepresentasikan bobot informatif kalimat. |
| **Pemilihan Kalimat** | **TextRank (Graph Centrality)** | Membangun graf kesamaan antar-kalimat (Cosine Similarity) dan mengurutkan sentralitas kepentingan kalimat. |
| **Pengurangan Redundansi** | **Maximal Marginal Relevance (MMR)** | Menyeimbangkan relevansi kalimat terhadap dokumen dengan kebaruan informasi (*diversity*) untuk mengeliminasi kalimat berulang. |
| **Kueri Lintas Bahasa** | **Multilingual Sentence Embeddings** (e.g. `paraphrase-multilingual-MiniLM-L12-v2` / `LaBSE`) | Mencocokkan makna kueri (ID) dengan kalimat dokumen (EN) dalam ruang semantik bersama untuk *Query-Focused Summary*. |
| **Ringkasan Lintas Bahasa** | Model multibahasa atau modul penerjemah | Diterapkan hanya jika bahasa ringkasan yang diminta berbeda dari bahasa dokumen sumber. |

> **Catatan Penting:** TextRank, TF-IDF, dan MMR berbasis bag-of-words tidak otomatis memahami kesetaraan semantik antarbahasa (*cross-lingual semantics*). Oleh karena itu, dipisahkan secara tegas antara:
> 1. **Meringkas dokumen utuh dalam bahasa aslinya** (cukup dengan TextRank + TF-IDF + MMR).
> 2. **Mencari kalimat yang relevan terhadap kueri dalam bahasa yang berbeda** (memerlukan Multilingual Sentence Embeddings).

---

## 6. Penanganan Skenario Kueri dan Dokumen Berbeda Bahasa

Contoh kasus riil:
- **Kueri Pengguna:** *"metode klasifikasi sentimen berbasis aspek"* (Bahasa Indonesia)
- **Dokumen Ditemukan:** Jurnal internasional berbahasa Inggris yang membahas *"aspect-based sentiment analysis"*.

Dua skenario penanganan:

### Skenario A — Ringkasan Dokumen Biasa (Single Document Summary)
- Sistem meringkas jurnal berbahasa Inggris dalam **Bahasa Inggris asli**.
- Menggunakan pipeline **TextRank + TF-IDF + MMR**.
- Pengguna mendapatkan ringkasan ekstraktif orisinal yang bebas distorsi terjemahan.

### Skenario B — Ringkasan Berdasarkan Kueri Lintas Bahasa (Cross-Lingual Query-Focused Summary)
- Pengguna ingin membaca ringkasan dari bagian jurnal Inggris yang menjawab kueri Bahasa Indonesia miliknya.
- TF-IDF leksikal biasa tidak cukup andal karena tidak ada irisan kata persis (*zero lexical overlap* antara "klasifikasi sentimen" dan "sentiment classification").
- **Solusi Arsitektural:**
  1. Gunakan **Multilingual Sentence Embeddings** (keluarga Sentence Transformers yang mendukung ID dan EN, misalnya `paraphrase-multilingual-MiniLM-L12-v2`).
  2. Hitung Cosine Similarity semantik antara embedding kueri pengguna dan embedding tiap kalimat kandidat dalam dokumen.
  3. Terapkan algoritma **MMR (Maximal Marginal Relevance)** untuk menyeimbangkan skor relevansi semantik terhadap kueri dan keberagaman informasi antar-kalimat terpilih:
     $$MMR = \arg\max_{S_i \in C \setminus S} \left[ \lambda \cdot \text{Sim}_1(S_i, Q) - (1 - \lambda) \cdot \max_{S_j \in S} \text{Sim}_2(S_i, S_j) \right]$$
  4. Tampilkan kalimat-kalimat terpilih beserta halaman sumber aslinya.

---

## 7. Arsitektur Alur Sistem Text Summarization

```text
                        Dokumen Akademik
              (PDF, Jurnal, Skripsi, Materi Kuliah)
                               │
                               ▼
               Teks Ekstraksi (DB: pages / chunks)
                               │
                               ▼
                        Deteksi Bahasa
               (fastText / langdetect: id, en, mixed)
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       Bahasa Indonesia                  Bahasa Inggris
               │                               │
    Preprocessing Indonesia           Preprocessing Inggris
    (Sastrawi stopwords, dsb.)       (NLTK stopwords, dsb.)
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
                 TextRank + TF-IDF + MMR
               (Ekstraksi Kalimat Kunci &
                 Penghilangan Redundansi)
                               │
                               ▼
             Ringkasan Ekstraktif (Bahasa Sumber)
                               │
               ┌───────────────┴───────────────┐
               │                               │
       Skenario A: Normal              Skenario B: Lintas Bahasa
       (Document Summary)              (Query-Focused Cross-Lingual)
               │                               │
               ▼                               ▼
       Output Ringkasan Baku          Multilingual Sentence Embeddings
       (Dilengkapi Bukti Halaman)     (Cocokkan Kueri ID ↔ Dokumen EN)
                                               │
                                               ▼
                                      Output Bukti Terpilih + MMR
```

### Struktur Modul yang Disarankan pada Backend (`academic-ir/src/summarization/`):
```text
academic-ir/src/summarization/
├── __init__.py
├── schemas.py           # Pydantic models (SummaryRequest, SummaryResponse, ProvenanceItem)
├── lang_detect.py       # Language detection (fastText / langdetect wrapper)
├── preprocessing.py     # Language-aware sentence splitter & stopword handler
├── textrank.py          # TF-IDF sentence representation & TextRank graph solver
├── mmr.py               # Maximal Marginal Relevance redundancy filter
├── embeddings.py        # Multilingual sentence embeddings (Sentence-Transformers)
├── service.py           # Facade orchestrator (cache, pipeline coordination)
├── storage.py           # SQLite cache adapter (tabel document_summaries)
├── validation.py        # Faithfulness check, length guards, empty text guard
└── evaluation.py        # Evaluation metrics (ROUGE, coverage, latency benchmarks)
```

---

## 8. Tahap Implementasi Terperinci

### Phase 0 --- Repository Audit
- [ ] Audit skema SQLite `academic_ir.db`: manfaatkan tabel `documents`, `pages`, dan `chunks`.
- [ ] Verifikasi format kolom bahasa yang sudah ada (`documents.language`).
- [ ] Identifikasi dependency baru yang ringan di `requirements.txt` (misalnya `langdetect`, `networkx` untuk TextRank, `scikit-learn` yang sudah tersedia).
- [ ] Pastikan pipeline retrieval BM25 dan TF-IDF tidak terganggu.

### Phase 1 --- Schema dan API Contract
Definisikan schema respons yang menyimpan metadata provenans lengkap:
```json
{
  "document_id": "DOC-1364",
  "summary_type": "document",
  "summary_text": "Penelitian ini menyajikan...",
  "language": "id",
  "detected_source_language": "id",
  "algorithm": "textrank_tfidf_mmr",
  "key_sentences": [
    {
      "text": "Kalimat penting pertama...",
      "page_number": 3,
      "score": 0.88
    }
  ],
  "source_pages": [1, 3],
  "status": "generated",
  "processing_time_ms": 42.5,
  "created_at": "2026-10-09T10:00:00Z"
}
```

Endpoint FastAPI yang disiapkan:
- `GET /api/documents/{document_id}/summary` — Mengambil ringkasan dari cache atau generate on-demand.
- `POST /api/documents/{document_id}/summary` — Generate ulang ringkasan dengan konfigurasi parameter (panjang, rasio).
- `POST /api/documents/{document_id}/query-summary` — Query-focused summary berbasis kueri pengguna.

### Phase 2 --- Language Detection & Language-Aware Preprocessing
- Implementasikan `lang_detect.py` untuk mengidentifikasi bahasa dokumen/teks.
- Bangun `preprocessing.py`:
  - Tokenisasi kalimat menggunakan regex aman terhadap singkatan/akronim ilmiah (`Dr.`, `et al.`, `No.`, dll.).
  - Stopword filtering dwibahasa terpisah.
  - Perlindungan istilah teknis dan simbol khusus.

### Phase 3 --- Extractive Baseline (TF-IDF + TextRank + MMR)
- Bangun representasi TF-IDF tingkat kalimat (*sentence-level TF-IDF*).
- Bangun graf keterhubungan antar-kalimat berbobot Cosine Similarity.
- Hitung skor PageRank / TextRank untuk menemukan kalimat paling sentral.
- Terapkan MMR untuk memilih Top-K kalimat berperingkat tinggi yang memiliki divergensi informasi (tidak saling mengulang ide yang sama).
- Pertahankan pemetaan halaman fisik dokumen (`page_number`).

### Phase 4 --- Dokumen Panjang dan Hierarchical Summarization
- Untuk skripsi tebal (100–300 halaman):
  - Prioritaskan bagian awal (abstrak, pendahuluan) dan bagian akhir (kesimpulan/saran).
  - Terapkan *section-wise summarization*: ringkas tiap bab/bagian penting, lalu gabungkan dengan MMR tingkat atas.
  - Abaikan daftar pustaka, lembar pengesahan, dan lampiran dari pembentukan ringkasan.

### Phase 5 --- Query-Focused Summary & Multilingual Sentence Embeddings
- Implementasikan pencocokan kueri ke kalimat menggunakan Multilingual Sentence Embeddings.
- Selesaikan Skenario B: Kueri Bahasa Indonesia dapat menarik bukti kalimat relevan dari paper berbahasa Inggris.
- Gabungkan dengan MMR untuk menyusun rangkuman jawaban berbasis bukti (*evidence-based answer summary*).

### Phase 6 --- Integrasi Antarmuka (Next.js 15)
- Tambahkan tombol **Lihat Ringkasan** pada kartu hasil pencarian (`ResultCard`).
- Sediakan popover/modal yang menampilkan:
  - Tab ringkasan dokumen (*Document Summary*) vs ringkasan berbasis kueri (*Query-Focused*).
  - Teks ringkasan dengan penanda nomor halaman asal kalimat.
  - Badge bahasa dokumen dan algoritma yang digunakan.
  - Loading skeleton state dan penanganan error/dokumen kosong.

---

## 9. Validasi dan Pencegahan Halusinasi

1. **Integritas Ekstraktif:** Karena baseline utama adalah ekstraktif, setiap kalimat yang muncul dijamin 100% merupakan kalimat autentik dari dokumen asli (0% halusinasi generatif).
2. **Pengecekan Teks Rusak / Minim:**
   - Jika dokumen memiliki total kata $< 50$ kata, kembalikan status `insufficient_text` dengan pesan informatif.
3. **Pemberitahuan Transparan:**
   - Berikan catatan pada UI: *"Ringkasan disusun secara ekstraktif dari teks dokumen asli menggunakan algoritma TextRank & MMR."*
4. **Pencegahan Korupsi Akronim:**
   - Simbol dan istilah serapan tidak boleh terpotong dalam pemecahan kalimat.

---

## 10. Evaluasi Summarization dan Dampak Perbedaan Bahasa

Evaluasi summarization wajib dipisahkan secara independen dari evaluasi retrieval IR.

### A. Protokol Evaluasi Terpisah per Kelompok Bahasa
Jangan hanya menghitung skor agregat rata-rata. Pisahkan analisis evaluasi ke dalam kelompok:
1. **Kelompok Dokumen Bahasa Indonesia** (Skripsi, modul OCW lokal).
2. **Kelompok Dokumen Bahasa Inggris** (Paper arXiv, DOAJ).
3. **Kelompok Dokumen Campuran (`mixed`)** (Slide kuliah dwibahasa).
4. **Kelompok Kueri Lintas Bahasa** (Kueri ID ↔ Dokumen EN).

### B. Dimensi Evaluasi yang Dinilai
- **Kualitas Ringkasan Dokumen (Document Summary):**
  - *Informativeness / Coverage:* Seberapa baik ringkasan mencakup ide pokok dan temuan kunci.
  - *Readability & Coherence:* Keterbacaan dan kelancaran alur kalimat.
  - *Non-Redundancy:* Efektivitas MMR dalam menekan kalimat duplikat atau repetisi makna.
  - *Faithfulness:* Bebas dari distorsi makna dokumen sumber.
- **Kualitas Query-Focused Summary:**
  - *Query Relevance:* Derajat keterkaitan bukti kalimat yang dipilih terhadap maksud kueri pengguna.
- **Kinerja Komputasi & Efisiensi:**
  - Waktu pemrosesan ringkasan (*latency per summary*, target: $< 150$ ms untuk extractive TextRank+MMR).
  - Konsumsi memori RAM / CPU.
  - Efektivitas cache hit rate pada SQLite.

---

## 11. Testing Wajib (Test Suite)

- [ ] **Test Language Detection:** Deteksi akurat teks murni ID, EN, dan teks pendek.
- [ ] **Test Language-Aware Preprocessing:** Stopword ID diterapkan pada teks ID; stopword EN pada teks EN; istilah teknis tetap utuh.
- [ ] **Test TextRank Core:** Konvergensi graf, penanganan graf terputus, dan pemeringkatan bobot kalimat.
- [ ] **Test MMR Redundancy Filter:** Pemilihan kalimat pertama relevan dan penolakan kalimat kedua yang hampir identik.
- [ ] **Test Edge Cases:** Teks dokumen kosong, dokumen dengan 1 kalimat saja, dokumen dengan banyak tabel/angka saja.
- [ ] **Test Caching & Storage:** Ringkasan yang sudah digenerate tersimpan di SQLite dan langsung dikembalikan pada pemanggilan kedua (< 5 ms).
- [ ] **Test Source Mapping:** Nomor halaman pada kalimat ringkasan cocok dengan nomor halaman fisik di tabel `pages`.
- [ ] **Test Non-Interference:** Indeks BM25 dan TF-IDF retrieval tetap berjalan normal 100%.

---

## 12. Acceptance Criteria

Fitur Text Summarization diterima apabila:
1. Seluruh fungsi penelusuran leksikal (BM25, TF-IDF) dan Tolerant Retrieval tetap berjalan normal tanpa regresi.
2. Pengguna dapat membuka ringkasan dokumen langsung dari kartu hasil pencarian di antarmuka web.
3. Deteksi bahasa bekerja otomatis untuk menentukan aturan preprocessing yang tepat.
4. Ringkasan dokumen ekstraktif berhasil diekstrak menggunakan **TextRank + TF-IDF + MMR** dalam bahasa asli dokumen.
5. Nomor halaman sumber dan skor relevansi kalimat ditampilkan secara transparan pada setiap ringkasan.
6. Redundansi kalimat berhasil ditekan secara efektif oleh MMR.
7. Dokumen dengan kueri lintas bahasa dapat ditarik bagian pentingnya menggunakan Multilingual Embeddings / representasi semantik.
8. Sistem caching di SQLite bekerja dengan baik sehingga ringkasan tidak dikomputasi ulang secara berulang.
9. Kasus dokumen pendek/kosong ditangani dengan pesan informasi yang santun tanpa kegagalan server (*no 500 error*).
10. Evaluasi kualitas dan latensi didokumentasikan secara terpisah berdasarkan kategori bahasa.

---

## 13. Instruksi Final untuk AI Coding Agent

1. **Audit terlebih dahulu, implementasi setelahnya.** Mulai dengan memeriksa schema database `academic_ir.db` dan endpoint API yang ada.
2. **Kembangkan secara modular:** Tempatkan kode summarization di folder tersendiri `src/summarization/` agar terpisah rapi dari mesin perankingan retrieval.
3. **Pertahankan pipeline yang ada:** Jangan merombak TF-IDF, BM25, Tolerant Retrieval, atau skema database utama.
4. **Patuhi urutan bertahap:**
   $$\text{Audit Repository} \rightarrow \text{Deteksi Bahasa} \rightarrow \text{Preprocessing Leksikal} \rightarrow \text{TextRank + TF-IDF + MMR} \rightarrow \text{Storage/Cache} \rightarrow \text{API & UI} \rightarrow \text{Multilingual Query Summary} \rightarrow \text{Evaluasi}$$
5. **Utamakan efisiensi komputasi lokal:** Baseline ekstraktif TextRank + MMR harus ringan, cepat, dan dapat dijalankan di CPU lokal tanpa memerlukan GPU berbayar.
