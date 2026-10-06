# Panduan Penilaian Relevansi — Qrels Judging Guide
## Academic IR System Evaluation

> **Dokumen ini** adalah panduan bagi penilai (judge) dalam memberikan skor relevansi dokumen
> terhadap kueri pencarian untuk keperluan evaluasi sistem temu kembali informasi (IR).

---

## Skala Relevansi (Graded Relevance Scale)

Setiap pasangan (kueri, dokumen) dinilai pada skala 0–3:

| Nilai | Label | Kriteria |
|:-----:|:------|:---------|
| **3** | **Highly Relevant** | Dokumen membahas topik kueri secara mendalam sebagai bahasan utama. Jika pengguna mencari topik ini, dokumen ini adalah jawaban ideal. |
| **2** | **Relevant** | Dokumen membahas topik kueri secara substansial tetapi bukan sebagai fokus utama, atau membahas subtopik yang sangat berkaitan. |
| **1** | **Marginally Relevant** | Dokumen menyebutkan atau menyinggung topik kueri sebagai referensi pendukung, bukan bahasan utama. |
| **0** | **Non-Relevant** | Dokumen tidak memiliki kaitan substantif dengan kueri. Kecocokan kata mungkin ada tapi tidak bermakna. |

---

## Prinsip Penilaian

### 1. Nilai berdasarkan kebutuhan informasi, BUKAN kecocokan kata
Kueri `"sistem operasi"` terhadap dokumen tentang `"sistem operasi pada smartphone"` = **relevan (2)** walaupun konteksnya berbeda dari kueri umum.

Kueri `"sistem operasi"` terhadap dokumen yang menyebutkan OS hanya dalam satu kalimat = **marginal (1)**.

### 2. Konten lebih penting dari judul
Judul dokumen yang mengandung kata kueri tidak otomatis berarti relevan jika isinya tidak membahas topik tersebut.

### 3. Panjang dokumen tidak berpengaruh pada relevansi
Dokumen 5 halaman yang fokus pada topik bisa lebih relevan dari dokumen 100 halaman yang hanya menyentuh topik selintas.

### 4. Bahasa bukan halangan
Dokumen berbahasa Inggris tetap dinilai relevan jika isinya membahas topik yang sama dengan kueri berbahasa Indonesia.

---

## Contoh Penilaian

### Kueri: `"data clustering K-means"`

| Dokumen | Relevansi | Alasan |
|:--------|:---------:|:-------|
| Slide kuliah "Data Mining: Clustering Methods" — Bab K-Means Clustering | **3** | Membahas K-Means secara mendalam sebagai topik utama |
| Paper "Comparative Study of Clustering Algorithms" — termasuk K-Means | **2** | Membahas K-Means tapi sebagai salah satu dari beberapa metode |
| Skripsi "Segmentasi Pelanggan menggunakan K-Means" | **2** | Aplikasi K-Means, relevan walaupun fokus pada domain spesifik |
| Materi kuliah "Statistik Deskriptif" — menyebut clustering di 1 kalimat | **1** | Hanya disebut selintas, bukan bahasan utama |
| Materi "Pemrograman Python Dasar" | **0** | Tidak ada kaitan dengan clustering |

---

## Format File Qrels

Format CSV: `query_id,document_id,relevance`

Hanya cantumkan dokumen yang **bukan 0** (non-relevant). Dokumen yang tidak ada dalam qrels dianggap 0.

```csv
query_id,document_id,relevance
Q01,MAT-000001,3
Q01,THD-000042,2
Q01,RES-000123,1
Q02,MAT-000015,3
...
```

---

## Prosedur Penilaian

1. **Baca teks kueri** dan pahami kebutuhan informasi di baliknya.
2. **Buka dokumen** via `local_path` atau `source_url` yang tersedia di database.
3. **Baca setidaknya abstrak/judul/bagian pertama** dokumen.
4. **Nilai relevansi** menggunakan skala 0–3.
5. **Catat dokumen dengan relevansi 1, 2, atau 3** saja ke dalam qrels.csv.

---

## Catatan Khusus untuk Evaluasi Ini

- **Corpus ini adalah benchmark publik**, bukan OASE Udayana. Nilai relevansi berdasarkan kebutuhan informasi akademik umum mahasiswa perguruan tinggi.
- **Kueri lintas bahasa (Q25-Q29)**: Nilai relevansi dokumen Bahasa Inggris yang membahas konsep yang sama dengan kueri Bahasa Indonesia sebagai **relevan (2 atau 3)**.
- **Kueri dengan constraint (Q30-Q33)**: Dokumen harus memenuhi constraint (tahun, tipe, topik) untuk mendapat nilai > 0.
- Jika ragu antara dua nilai, pilih nilai yang **lebih rendah** (konservatif).

---

*Panduan ini disiapkan untuk Academic IR System Evaluation — Kelompok [Nama]*
