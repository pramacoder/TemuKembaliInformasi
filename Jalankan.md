# Panduan Menjalankan & Mengembangkan Sistem Academic IR

Sistem Information Retrieval (IR) akademik ini terdiri dari dua komponen utama:
1. **Backend API**: FastAPI (Python) yang memuat database SQLite dan indeks TF-IDF (18.704 chunks, 771.589 fitur kosakata).
2. **Frontend UI**: Next.js 15 (React 19, Tailwind CSS, shadcn/ui).

---

## 🟢 Status Layanan Saat Ini

Kedua layanan saat ini **sudah aktif dan berjalan di background**:

| Layanan | URL Akses | Keterangan |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | Antarmuka pencarian dokumen akademik |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | Server FastAPI & mesin temu kembali |
| **Dokumentasi API (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Dokumentasi interaktif REST API |
| **Health Check API** | [http://localhost:8000/api/health](http://localhost:8000/api/health) | Cek status indeks & database |

---

## 📊 Statistik Korpus Terkini

Sistem saat ini menggunakan **SQLite** (`database/academic_ir.db`) sebagai basis data terpusat:
- **Dokumen Kuliah (MATERIAL)**: 250 dokumen (Fasilkom UI + FMIPA UI)
- **Paper Riset (RESEARCH)**: 169 dokumen (arXiv cs.IR, cs.CL, cs.AI, DOAJ)
- **Skripsi & Tesis (THESIS)**: 121 dokumen (Undip & UIN Malang Repositories)
- **Total Dokumen**: 540 dokumen
- **Total Chunks Terindeks**: 18.704 chunks
- **Ukuran Kosakata VSM TF-IDF**: 771.589 terms (unigram + bigram)

---

## 📚 Cara Menambah Bahan Kuliah (Material) dari Semua Prodi / Fakultas

Sebelumnya, materi kuliah hanya mengambil dari **Fakultas Ilmu Komputer (Fasilkom - Category 12)**. Sekarang telah tersedia script khusus [`scripts/collect_materials_all_prodi.py`](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/collect_materials_all_prodi.py) yang dapat memanen materi kuliah dari **seluruh fakultas dan prodi** di OpenCourseWare Universitas Indonesia.

### Daftar ID Fakultas yang Didukung:
- `2` : Fakultas Kedokteran (FK)
- `4` : Fakultas Matematika & Ilmu Pengetahuan Alam (FMIPA)
- `5` : Fakultas Teknik (FT)
- `7` : Fakultas Ekonomi dan Bisnis (FEB)
- `8` : Fakultas Ilmu Pengetahuan Budaya (FIB)
- `9` : Fakultas Psikologi
- `10`: Fakultas Ilmu Sosial & Ilmu Politik (FISIP)
- `11`: Fakultas Kesehatan Masyarakat (FKM)
- `13`: Fakultas Ilmu Keperawatan (FIK)
- `17`: Fakultas Farmasi (FF)
- `18`: Fakultas Ilmu Administrasi (FIA)

### Perintah Menjalankan Scraping Bahan Kuliah:

#### A. Panen dari SEMUA Fakultas Sekaligus:
```powershell
cd academic-ir
.\venv\Scripts\python scripts/collect_materials_all_prodi.py --faculty all --max-courses 3 --limit-per-course 5
```

#### B. Panen dari Fakultas Tertentu (Contoh: Kedokteran, Teknik, atau Ekonomi):
```powershell
cd academic-ir
# Mengambil materi Fakultas Kedokteran (Category 2)
.\venv\Scripts\python scripts/collect_materials_all_prodi.py --faculty 2

# Mengambil materi Fakultas Ekonomi & Bisnis (Category 7)
.\venv\Scripts\python scripts/collect_materials_all_prodi.py --faculty 7

# Mengambil materi Fakultas Teknik (Category 5)
.\venv\Scripts\python scripts/collect_materials_all_prodi.py --faculty 5
```

Script di atas otomatis:
1. Menemukan mata kuliah dari fakultas terkait.
2. Mengunduh berkas materi (PDF maupun slide presentasi PPTX).
3. Mengekstrak teks, membersihkan stopword, dan mendeteksi bahasa.
4. Memotong menjadi chunks dan menyimpannya ke tabel `documents`, `pages`, dan `chunks` di SQLite.
5. Membangun ulang indeks TF-IDF secara otomatis.

---

## 📥 Cara Melakukan Scraping Riset & Tesis

```powershell
cd academic-ir
# Panen batch riset (arXiv) dan tesis (OAI-PMH) sekaligus:
.\venv\Scripts\python scripts/harvest_large_corpus.py --research 100 --thesis 100
```

---

## 🚀 Cara Menjalankan Manual di Masa Mendatang

Jika terminal ditutup atau komputer di-restart:

### 1. Jalankan Backend (FastAPI)
```powershell
cd academic-ir
.\venv\Scripts\activate
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Jalankan Frontend (Next.js)
```powershell
cd academic-ir\academic-ir-frontend
npm run dev
```

Buka browser di **http://localhost:3000** untuk menggunakan sistem pencarian.
