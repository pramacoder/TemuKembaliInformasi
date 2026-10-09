# LAPORAN PROJECT TAHAP I: ANALISIS DAN DESAIN SISTEM
## PENGEMBANGAN PERANGKAT LUNAK TEMU KEMBALI INFORMASI AKADEMIK MULTI-KORPUS BERBASIS LEXICAL RETRIEVAL (DUAL-BASELINE: TF-IDF VSM & OKAPI BM25 DENGAN DOCUMENT-LEVEL AGGREGATION)

---

**Mata Kuliah:** Temu Kembali Informasi / Rekayasa Perangkat Lunak Berbasis Kecerdasan Buatan  
**Tugas:** Tugas Kelompok I — Project Team-Based Tahap I  
**Topik Kasus:** Sistem Temu Kembali Informasi Dokumen Akademik Lintas Disiplin Ilmu (*Unified Multi-Corpus Academic Search Engine*)  
**Instansi:** Program Studi Ilmu Komputer / Informatika  
**Tahun Akademik:** 2026/2027  

**Disusun Oleh: Kelompok [Nama Kelompok]**
- [Nama Mahasiswa 1] — [NIM 1]
- [Nama Mahasiswa 2] — [NIM 2]
- [Nama Mahasiswa 3] — [NIM 3]
- [Nama Mahasiswa 4] — [NIM 4]

---

## RINGKASAN EKSEKUTIF (*ABSTRACT*)

Ledakan informasi di ranah akademik menimbulkan tantangan *information overload* yang nyata. Mahasiswa, dosen, dan peneliti sering menghadapi fenomena *academic silo*, di mana materi perkuliahan (*lecture slides/materials*), artikel jurnal penelitian (*research papers*), dan tugas akhir/skripsi (*theses/dissertations*) tersimpan pada repositori terpisah dengan format dokumen PDF tanpa indeksasi teks granular. Mesin pencari komersial umum kerap hanya mengindeks judul atau meta-tag dokumen, gagal memberikan nomor halaman spesifik dan sering menghasilkan redundansi fragmen dari satu dokumen yang sama.

Proyek ini mengembangkan **Academic IR**, sebuah perangkat lunak sistem temu kembali informasi (*Information Retrieval System*) berbasis penelusuran leksikal (*Lexical Retrieval*) yang menerapkan arsitektur **Dual-Baseline**: **Baseline A (TF-IDF Vector Space Model dengan Cosine Similarity)** dan **Baseline B (Okapi BM25 dengan normalisasi panjang dokumen $k_1=1.5, b=0.75$)** yang dilengkapi modul **Document-Level Aggregation** (`max+2nd`) untuk mengeliminasi bias dominasi dokumen panjang. Sistem ini mengintegrasikan korpus terpadu berskala representatif yang terdiri dari **1.364 dokumen akademik** dengan **56.881 potongan teks granular (*chunks*)** dan ruang kosakata (*vocabulary space*) sebanyak **1.969.538 term**. Pengujian empiris pada **33 kueri benchmark** menunjukkan keunggulan numerik BM25 dibanding TF-IDF: peningkatan **MAP (+48.4%, 0.1235 vs 0.0832)**, peningkatan **NDCG@10 (+20.2%, 0.2992 vs 0.2490)**, serta latensi pencarian sekitar 9x lebih cepat pada lingkungan lokal (**P50: 83.71 ms vs 751.84 ms**). Uji signifikansi statistik formal menggunakan uji non-parametrik **Wilcoxon signed-rank test** menghasilkan nilai $p = 0.0684$ pada NDCG@10 (95% CI: $[+0.0057, +0.1036]$), yang mengindikasikan keunggulan empiris yang kuat namun belum melampaui batas signifikansi baku ($\alpha = 0.05$) pada ukuran sampel 33 kueri.

Sebagai peningkatan lanjutan pada arsitektur temu kembali informasi (Revisi Tahap II), sistem diperkaya dengan modul **Tolerant Retrieval** yang berfungsi sebagai lapisan normalisasi dan pemulihan kueri (*Query Normalization & Recovery Layer*) sebelum tahap retrieval leksikal BM25. Lapisan ini menangani kesalahan pengetikan (*typo tolerance* melalui Damerau-Levenshtein distance), variasi ejaan akademik (`analisa` → `analisis`), ekspansi singkatan (`NLP` → `Natural Language Processing`), dan perlindungan istilah teknis bernilai khusus (`C++`, `.NET`, `TF-IDF`). Sistem menerapkan prinsip **Exact-First Priority**, di mana kueri eksak selalu dieksekusi terlebih dahulu dan mekanisme *fallback* hanya dipicu jika hasil penelusuran awal minim atau nihil. Seluruh transformasi kueri didukung oleh transparansi *audit log* (*explainability*) dan diintegrasikan secara interaktif pada antarmuka *Search Bar* (Next.js 15) melalui fitur *real-time live suggestions dropdown*, selektor mode toleransi instan (*Auto / Always / Off*), serta banner pemulihan hasil (*recovery banner*).

Untuk mengatasi dilema penyajian pada sistem temu kembali informasi (*The Passage Dilemma in IR*)—di mana pemeringkatan matematis memerlukan pengindeksan berbasis potongan (*passage/chunk-level indexing*) guna mencegah dilusi term, namun pengguna membutuhkan pembacaan dokumen utuh—sistem bertransformasi dari sekadar penyaji fragmen teks menjadi **Full Document Delivery Platform**. Kartu hasil pencarian menyajikan identitas dokumen utuh, meliputi abstrak resmi dokumen, total halaman fisik, serta pemetaan nomor halaman spesifik yang membahas kueri pengguna (`Relevan di Hal. 1, 2, 4...`). Sistem mengintegrasikan modul pembaca dokumen utuh (**In-App Full Document Reader**) melalui endpoint `GET /api/documents/{document_id}/pages` yang mengakses lebih dari **50.218 halaman fisik asli** dari basis data SQLite. Pembaca dokumen ini mendukung navigasi halaman fisik, *continuous scrolling*, tombol pintasan (*quick-jump*) ke halaman relevan, penyorotan kata kunci kueri (*query term highlighting*), serta perpindahan instan ke fitur peringkasan cerdas.

Melengkapi kemampuan temu kembali informasi hingga tingkat pemahaman isi, sistem mengintegrasikan modul **Text Summarization** (*Language-Aware Extractive & Query-Focused Summarization*). Modul ini mengatasi tantangan heterogenitas bahasa korpus (skripsi bahasa Indonesia, paper riset bahasa Inggris, dan materi kuliah dwibahasa) tanpa melakukan penerjemahan paksa ke satu bahasa. Sistem mengimplementasikan algoritma **TextRank** (graf kemiripan kosinus antar-kalimat berbasis *Power Iteration PageRank*) yang dipadukan dengan **Maximal Marginal Relevance (MMR, $\lambda=0.70$)** untuk mengeliminasi redundansi pengulangan ide dan menyajikan alur ringkasan kronologis berdasar dokumen asli. Selain itu, sistem mendukung **Query-Focused Cross-Lingual Evidence Extraction** menggunakan representasi semantik multibahasa untuk mengekstrak kalimat-kalimat bukti yang secara presisi menjawab kueri pengguna (misalnya kueri berbahasa Indonesia pada paper berbahasa Inggris). Seluruh ringkasan dilengkapi atribusi nomor halaman fisik asli (*traceability*, 100% bebas halusinasi) dan diakselerasi melalui persistensi *caching* SQLite tabel `document_summaries` dengan latensi akses secepat **1,7–2,1 ms**. Laporan ini menyajikan analisis kebutuhan, arsitektur berlapis, pemodelan UML, perancangan basis data, flowchart perankingan, evaluasi Cranfield (*P@K, R@K, MAP, NDCG, MRR*), studi ablasi, validasi toleransi kueri, desain pembaca dokumen utuh, serta desain dan evaluasi komprehensif modul peringkasan teks.

---

# I. PENDAHULUAN

### 1.1 Latar Belakang
Kegiatan tridharma perguruan tinggi di era digital menghasilkan volume dokumen ilmiah dan pedagogis yang sangat masif. Dokumen akademik umumnya terbagi menjadi tiga pilar utama:
1. **Bahan Kuliah (*Lecture Materials / OpenCourseWare*)**: Berupa slide presentasi dan buku rancangan pengajaran yang digunakan dalam transfer pengetahuan dasar hingga lanjut di ruang kelas.
2. **Artikel Jurnal Ilmiah (*Research Papers*)**: Publikasi ilmiah mutakhir yang memuat kebaruan metodologi, eksperimen, dan temuan teoritis.
3. **Karya Ilmiah Mahasiswa (*Theses and Dissertations*)**: Skripsi, tesis, dan disertasi yang mengkaji aplikasi metode pada studi kasus spesifik.

Meskipun ketiga pilar ini saling melengkapi, implementasi repositori akademik saat ini memiliki sejumlah kelemahan mendasar:
- **Pemisahan Sistem (*Information Silos*)**: Mahasiswa harus membuka portal OCW untuk bahan kuliah, membuka Google Scholar/Scopus untuk riset, dan membuka repositori institusi terpisah untuk skripsi. Tidak tersedia pencarian terpadu (*unified search*) yang mampu menyajikan relasi ketiga jenis dokumen dalam satu kueri.
- **Keterbatasan Granularitas (*Document-Level vs. Chunk-Level*)**: Dokumen akademik berupa PDF berukuran besar (seringkali mencapai puluhan hingga ratusan halaman). Mesin pencari tradisional hanya mengembalikan dokumen utuh tanpa memberi tahu pada halaman atau paragraf mana topik yang dicari dibahas.
- **Karakteristik Teks Dwibahasa (*Bilingual Nature*)**: Literatur akademik di Indonesia bercampur antara Bahasa Indonesia dan Bahasa Inggris, menuntut pipeline pemrosesan teks yang sadar bahasa (*language-aware preprocessing*).

Untuk menjawab permasalahan tersebut, diperlukan pengembangan perangkat lunak sistem temu kembali informasi akademik berbasis *Machine Learning* yang mampu mengekstraksi, memotong (*chunking*), merepresentasikan teks ke dalam ruang vektor matematika multidimensi, serta meranking relevansi dokumen secara cepat dan presisi.

### 1.2 Rumusan Masalah
Berdasarkan latar belakang di atas, rumusan masalah dalam pengembangan perangkat lunak ini dirumuskan sebagai berikut:
1. Bagaimana merancang arsitektur sistem temu kembali informasi yang mampu mengintegrasikan tiga jenis korpus akademik (Bahan Kuliah, Riset, dan Skripsi) dalam satu antarmuka kueri terpadu?
2. Bagaimana membangun pipeline pemrosesan teks dwibahasa (*bilingual text preprocessing*) dan segmentasi dokumen (*chunking*) berbasis halaman untuk mengindeks dokumen PDF akademik?
3. Bagaimana menerapkan algoritma *Machine Learning* berbasis Vector Space Model (VSM) dengan pembobotan TF-IDF dan Cosine Similarity serta Okapi BM25 untuk menghasilkan perankingan dokumen akademik yang relevan secara matematis?
4. Bagaimana merancang skema basis data relasional dan antarmuka web interaktif yang responsif untuk menampilkan hasil pencarian beserta cuplikan (*snippet*), nomor halaman, dan metadata dokumen?
5. Bagaimana merancang instrumen evaluasi sistem yang komprehensif, mencakup pengujian fungsionalitas perangkat lunak (*Black-box Testing*) dan evaluasi metrik kinerja Information Retrieval (*Precision, Recall, MAP, NDCG*)?
6. Bagaimana menjembatani dilema penyajian temu kembali informasi (*The Passage Dilemma*) agar sistem tidak hanya mengembalikan potongan teks (*chunks*) terisolasi, melainkan mampu menyajikan dokumen utuh multi-halaman secara interaktif (*In-App Full Document Reader*) dengan navigasi halaman dan penyorotan kata kunci kueri?

### 1.3 Tujuan Pengembangan Perangkat Lunak
Tujuan dari proyek pengembangan perangkat lunak ini adalah:
1. Menganalisis kebutuhan fungsional dan non-fungsional sistem temu kembali informasi akademik terpadu (*Unified Academic IR*).
2. Merancang arsitektur perangkat lunak berbasis layanan mikro/terpisah (*decoupled architecture*) yang memisahkan frontend interaktif (Next.js), backend REST API (FastAPI), dan mesin temu kembali informasi berbasis Python.
3. Merancang pipeline *preprocessing*, *feature extraction*, dan *training* model TF-IDF VSM serta indeks Okapi BM25 untuk memproses lebih dari 56.000 *chunks* teks akademik nyata.
4. Merancang skema basis data relasional (SQLite) yang efisien untuk menyimpan metadata dokumen, teks per halaman fisik asli (50.218 halaman), dan unit pencarian granular (*chunks*).
5. Merancang antarmuka pengguna modern dengan fitur penyaringan segi (*faceted filtering*), pencarian instan, penanganan toleransi kueri (*Tolerant Retrieval*), dan modul pembaca dokumen utuh interaktif (*In-App Full Document Reader*).
6. Menyusun rencana pengujian perangkat lunak (*Black-box testing*) dan perancangan eksperimen evaluasi model Information Retrieval berstandar benchmark ilmiah.
7. Mengembangkan modul pembaca dokumen utuh dan peringkasan cerdas ekstraktif (*Text Summarization TextRank + MMR*) untuk mempercepat pemahaman isi literatur ilmiah oleh pengguna secara terintegrasi.

### 1.4 Deskripsi Singkat Aplikasi
Aplikasi yang dikembangkan diberi nama **Academic IR** (*Academic Information Retrieval System*). Aplikasi ini merupakan mesin pencari akademik cerdas berbasis web yang memungkinkan pengguna mengetik kueri pencarian bebas (misalnya: *"analisis perancangan sistem informasi use case diagram"*, *"hukum gauss elektrostatis"*, atau *"metode penelitian komparatif"*). 

Sistem secara otomatis memproses kueri melalui pipeline NLP dwibahasa, menerapkan normalisasi toleran (*Tolerant Retrieval* untuk typo, variasi ejaan, dan singkatan), menghitung derajat relevansi leksikal menggunakan model probabilistik Okapi BM25 atau TF-IDF Cosine Similarity, dan mengagregasi skor tingkat dokumen (`max+2nd`). Sistem menyajikan daftar hasil pencarian terbaik (*Top-K results*) yang dilengkapi judul dokumen, kategori korpus (*Material / Research / Thesis*), abstrak dokumen utuh resmi, cuplikan kontekstual (*smart snippet*), peta sebaran halaman relevan, serta tombol aksi **"Baca Dokumen Lengkap"**. Melalui tombol ini, pengguna dapat membaca seluruh halaman fisik dokumen secara langsung di dalam aplikasi (*In-App Full Document Reader*) lengkap dengan penyorotan kata kunci kueri (*keyword highlighting*), navigasi halaman fleksibel, serta peralihan satu klik ke modul peringkasan AI ekstraktif (*TextRank + MMR*).

---

# II. TINJAUAN PUSTAKA

### 2.1 Teori dan Konsep Sistem Temu Kembali Informasi (*Information Retrieval*)
Sistem Temu Kembali Informasi (*Information Retrieval / IR*) didefinisikan oleh Manning, Raghavan, dan Schütze (2008) sebagai sistem yang bertugas menemukan materi (biasanya dokumen) yang bersifat tidak terstruktur (biasanya teks) yang memenuhi kebutuhan informasi dari kumpulan koleksi besar yang disimpan secara komersial atau institusional. Berbeda dengan basis data relasional yang menggunakan pencocokan pasti (*exact match SQL query*), sistem IR menangani ketidakpastian semantik kueri manusia menggunakan model perankingan berbasis probabilitas atau kemiripan ruang vektor (*relevance ranking*).

### 2.2 Model Ruang Vektor (*Vector Space Model — VSM*)
*Vector Space Model* yang dipelopori oleh Gerard Salton (Salton & Buckley, 1988) merupakan landasan utama dalam bidang IR dan pemrosesan teks klasik machine learning. Dalam VSM, baik dokumen ($d$) maupun kueri pengguna ($q$) direpresentasikan sebagai vektor berdimensi-$V$ di dalam ruang matematika berdimensi tinggi:
$$\vec{d} = (w_{1,d}, w_{2,d}, \dots, w_{V,d})$$
$$\vec{q} = (w_{1,q}, w_{2,q}, \dots, w_{V,q})$$
di mana $V$ adalah ukuran perbendaharaan kata (*vocabulary size*) dari seluruh koleksi dokumen, dan $w_{t,d}$ merupakan bobot numerik term $t$ dalam dokumen $d$.

### 2.3 Pembobotan Kata: TF-IDF (*Term Frequency – Inverse Document Frequency*)
Pembobotan kata menggunakan skema TF-IDF menggabungkan dua intuisi statistika bahasa:
1. **Term Frequency ($TF_{t,d}$)**: Seberapa sering term $t$ muncul dalam dokumen $d$. Untuk mencegah dominasi frekuensi kata yang sangat tinggi, digunakan fungsi logaritmik (*Sublinear Term Frequency*):
   $$TF_{sublinear}(t, d) = 1 + \ln(TF(t, d)) \quad \text{jika } TF(t, d) > 0, \quad \text{dan } 0 \text{ jika sebaliknya}$$
2. **Inverse Document Frequency ($IDF_t$)**: Mengukur kelangkaan kata di seluruh koleksi korpus dokumen. Kata yang muncul di hampir semua dokumen (seperti kata umum) diberi bobot rendah, sedangkan kata khusus (seperti istilah teknis) diberi bobot tinggi:
   $$IDF(t, D) = \ln\left(\frac{1 + |D|}{1 + DF(t)}\right) + 1$$
   di mana $|D|$ adalah total dokumen/chunk dalam koleksi, dan $DF(t)$ adalah jumlah dokumen yang memuat term $t$.

Bobot akhir term $t$ dalam dokumen $d$ adalah:
$$W(t, d) = TF_{sublinear}(t, d) \times IDF(t, D)$$

Selain unigram (kata tunggal), sistem mengadopsi representasi n-gram $(1, 2)$ yang mencakup unigram dan bigram (pasangan dua kata berurutan, misalnya: *"machine learning"*, *"use case"*). Hal ini mempertahankan keterikatan frasa kontekstual tanpa kehilangan fleksibilitas representasi statistik kata dasar.

### 2.4 Pengukuran Kemiripan Sudut (*Cosine Similarity*)
Untuk mengukur derajat relevansi antara vektor kueri $\vec{q}$ dan vektor dokumen/chunk $\vec{d}$, digunakan metrik *Cosine Similarity*, yaitu kosinus dari sudut antara kedua vektor dalam ruang berdimensi $V$:
$$\text{Cosine Similarity}(\vec{q}, \vec{d}) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\|_2 \|\vec{d}\|_2} = \frac{\sum_{i=1}^{V} w_{i,q} w_{i,d}}{\sqrt{\sum_{i=1}^{V} w_{i,q}^2} \sqrt{\sum_{i=1}^{V} w_{i,d}^2}}$$
Nilai kesamaan berkisar antara $0.0$ (tidak memiliki kata yang beririsan sama sekali) hingga $1.0$ (relevansi sempurna atau vektor identik). Melalui normalisasi Euclidean ($L2$-norm), panjang dokumen tidak mendistorsi skor pencarian, sehingga dokumen berukuran panjang tidak mendominasi dokumen pendek secara tidak adil.

```
                    Vektor Dokumen d
                          ▲
                         / 
                        /  Sudut θ
                       / ) 
                      /────────────────▶ Vektor Kueri q
                     Panjang L2 disetarakan
               Cosine Sim = cos(θ) ∈ [0, 1]
```

### 2.4.1 Model Probabilistik Okapi BM25 (*Baseline B*)
Sebagai baseline kedua yang lebih kuat, sistem mengimplementasikan **Okapi BM25** (Robertson & Jones, 1976). BM25 mengatasi dua keterbatasan utama TF-IDF standar:
1. **Saturasi Frekuensi Term (*Term Frequency Saturation*)**: Peningkatan frekuensi kata tidak meningkatkan skor secara tak terbatas; parameter $k_1$ mengatur titik jenuh frekuensi kata.
2. **Normalisasi Panjang Dokumen (*Document Length Normalization*)**: Parameter $b$ menghukum dokumen yang panjangnya di atas rata-rata korpus agar tidak mendominasi dokumen pendek secara tidak adil.

Formula matematis Okapi BM25 untuk kueri $Q = \{q_1, q_2, \dots, q_n\}$ terhadap dokumen $D$:
$$BM25(D, Q) = \sum_{i=1}^{n} IDF(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
di mana $f(q_i, D)$ adalah frekuensi kemunculan term $q_i$ dalam $D$, $|D|$ adalah panjang dokumen dalam kata, $\text{avgdl}$ adalah rata-rata panjang dokumen di seluruh korpus, dan parameter standar yang digunakan adalah $k_1 = 1.5$ serta $b = 0.75$.

### 2.5 Text Preprocessing Dwibahasa (*Bilingual Pipeline*)
Korpus akademik di Indonesia memiliki karakteristik dwibahasa (*Indonesian–English*). Tahapan pemrosesan teks meliputi:
1. **Case Folding & Cleansing**: Mengubah semua karakter teks menjadi huruf kecil (*lowercase*) serta menghapus karakter non-alfanumerik, tanda baca asing, dan spasi redundan.
2. **Tokenisasi**: Memotong aliran karakter menjadi token kata individual.
3. **Penyaringan Stopwords (*Stopword Removal*)**: Menghilangkan kata sambung dan kata umum yang tidak memiliki bobot pembeda informasi. Digunakan daftar *stopword* Bahasa Indonesia dari Tala (123 kata) dan daftar *stopword* Bahasa Inggris dari NLTK (198 kata).
4. **Stemming / Lematisasi**: Mengembalikan kata berimbuhan ke bentuk dasarnya.
   - **Teks Bahasa Indonesia**: Menggunakan algoritma **Sastrawi** (pengembangan algoritma Nazief & Adriani) yang akurat memotong prefiks, infiks, sufiks, dan konfiks morfologi bahasa Indonesia.
   - **Teks Bahasa Inggris**: Menggunakan **Snowball Stemmer / Porter Stemmer** dari pustaka NLTK yang efisien dalam menangani morfologi derivasional bahasa Inggris.

### 2.6 Strategi Segmentasi Dokumen (*Granular Chunking Strategy*)
Dokumen akademik dalam format PDF memiliki kelemahan jika diindeks secara utuh: topik di awal dokumen akan tercampur dengan topik di akhir dokumen, dan kueri spesifik akan menghasilkan skor TF-IDF yang terdilusi. Oleh karena itu, diterapkan teknik segmentasi (*chunking*) berbasis halaman dengan jendela geser (*sliding window*) berukuran 200–400 kata dengan *overlap* 50 kata. Setiap unit *chunk* terasosiasi secara presisi dengan nomor halaman dokumen sumber (`page_start` dan `page_end`), sehingga sistem dapat mengarahkan pengguna langsung ke halaman yang memuat jawaban kueri.

### 2.6.1 Teori Agregasi Dokumen (*Document-Level Aggregation*)
Meskipun pengindeksan dilakukan pada tingkat *chunk*, kebutuhan nyata pengguna adalah menemukan **dokumen utuh** beserta bukti halaman terbaiknya, bukan puluhan pecahan dari dokumen yang sama. Tanpa modul agregasi, satu skripsi tebal (100+ halaman) dapat memonopoli peringkat 1 hingga 5 (*chunk duplication bias*).

Oleh karena itu, sistem merancang modul **Document-Level Aggregation** dengan tiga strategi penggabungan skor:
1. **Strategi Max (`max`)**:
   $$Score(D) = \max_{c \in D} S(c)$$
   Hanya mengambil skor potongan tertinggi sebagai representasi dokumen.
2. **Strategi Max + 2nd Best (`max+2nd` — Default)**:
   $$Score(D) = S(c_{(1)}) + \lambda \cdot S(c_{(2)})$$
   dengan bobot $\lambda = 0.3$. Strategi ini memberikan bonus moderat jika dokumen memiliki lebih dari satu bagian yang sangat relevan, sekaligus menjaga keseimbangan agar dokumen tebal tidak mendominasi.
3. **Strategi Rata-rata Top-N Terbobot (`topN_avg`)**:
   $$Score(D) = \frac{\sum_{i=1}^{N} \frac{1}{i} S(c_{(i)})}{\sum_{i=1}^{N} \frac{1}{i}}, \quad N = 3$$
   Menghitung rata-rata harmonik berbobot dari 3 potongan teratas.

### 2.6.2 Dilema Penyajian dalam Passage Retrieval: Passage Scoring vs. Full Document Delivery
Dalam literatur temu kembali informasi klasik maupun modern, segmentasi dokumen menjadi bagian-bagian lebih kecil (*passage retrieval*) diakui secara luas sebagai pendekatan paling efektif untuk menangani dokumen teks berukuran besar (Callan, 1994; Kaszkiel & Zobel, 1997). Dokumen akademik (skripsi 100+ halaman, modul kuliah, buku referensi) memiliki cakupan topik yang heterogen. Jika seluruh dokumen diindeks sebagai satu kesatuan teks raksasa, muncul dua kendala matematis serius:
1. **Pengeceran Term (*Term Dilution*)**: Istilah kueri spesifik yang hanya muncul 3–5 kali pada satu subbab penting akan memiliki frekuensi relatif yang amat kecil dibanding total puluhan ribu kata dalam dokumen, sehingga skor BM25/TF-IDF dokumen tersebut terdilusi drastis.
2. **Penalti Panjang Dokumen (*Document Length Penalty*)**: Komponen normalisasi panjang dokumen pada Okapi BM25 ($\frac{|D|}{\text{avgdl}}$) akan memberikan penalti berat pada dokumen tebal, menyebabkan artikel 5 halaman mengalahkan disertasi 150 halaman meskipun disertasi tersebut memuat pembahasan yang jauh lebih mendalam.

Namun demikian, sistem IR yang **hanya mengembalikan potongan teks (*raw chunks*)** kepada pengguna menimbulkan degradasi pengalaman pengguna (*User Experience / UX degradation*):
- **Kehilangan Konteks Naratif (*Loss of Global Context*)**: Pengguna hanya disajikan 200–300 kata tanpa mengetahui posisi bagian tersebut di dalam struktur hierarki dokumen (apakah bagian dari latar belakang, kajian teori, metodologi, atau temuan).
- **Friksi Akses Dokumen (*High Access Friction*)**: Pengguna harus berpindah ke aplikasi pembaca PDF eksternal dan mencari secara manual kata kunci yang dicari, menghilangkan efisiensi penelusuran.
- **Ketiadaan Representasi Makro**: Tanpa abstrak resmi dokumen utuh, pengguna kesulitan mengevaluasi apakah dokumen tersebut layak dibaca lebih lanjut.

Untuk menyelesaikan dilema tersebut, **Academic IR** menerapkan prinsip **"Index by Passage for Mathematical Accuracy, Present as Whole Document for Human Consumption"** (Indeksasi berbasis potongan untuk presisi perankingan, penyajian berbasis dokumen utuh untuk pemahaman pengguna):
- **Di Balik Layar (Backend Engine)**: Pemeringkatan matematis tetap dihitung pada granularitas *chunk* dengan agregasi dokumen `max+2nd` agar akurasi P@K, MAP, dan NDCG tetap maksimal tanpa bias panjang dokumen.
- **Di Hadapan Pengguna (Frontend & API)**: Hasil pencarian dirangkum sebagai satu kartu dokumen utuh yang menampilkan **Abstrak Resmi Dokumen**, total halaman fisik dokumen, dan badge sebaran halaman yang relevan dengan topik kueri (`Relevan di Hal. 1, 4, 12...`).
- **Modul Pembaca Terpadu (*In-App Full Document Reader*)**: Pengguna dapat membaca keseluruhan halaman fisik dokumen secara langsung di dalam aplikasi melalui endpoint `GET /api/documents/{document_id}/pages`, lengkap dengan navigasi antar-halaman (*pagination / continuous scroll*), tombol pintasan (*jump*) ke halaman-halaman relevan, serta penyorotan kata kunci kueri (*query-term highlighting*) di seluruh teks dokumen asli.

### 2.7 Desain Evaluasi Sistem Temu Kembali Informasi
Kinerja sistem IR diukur menggunakan metrik evaluasi baku berbasis *ground truth* (*Query Relevance Judgments / Qrels*):
1. **Precision@K (P@K)**: Proporsi dokumen relevan di antara $K$ dokumen teratas yang dikembalikan sistem:
   $$P@K = \frac{\text{Jumlah dokumen relevan di top-}K}{K}$$
2. **Recall@K (R@K)**: Proporsi dokumen relevan yang berhasil ditemukan dari seluruh total dokumen relevan yang ada di koleksi:
   $$R@K = \frac{\text{Jumlah dokumen relevan di top-}K}{\text{Total seluruh dokumen relevan untuk kueri tersebut}}$$
3. **Mean Reciprocal Rank (MRR)**: Mengukur seberapa cepat pengguna menemukan dokumen relevan pertama ($MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$). Nilai $1.0$ berarti dokumen relevan selalu berada di peringkat pertama.
4. **Mean Average Precision (MAP)**: Rata-rata dari nilai *Average Precision* (AP) untuk kumpulan kueri uji ($Q$), yang memberikan bobot lebih tinggi pada dokumen relevan yang berada di peringkat atas:
   $$MAP = \frac{1}{|Q|} \sum_{q \in Q} AP(q) = \frac{1}{|Q|} \sum_{q \in Q} \left( \frac{1}{R_q} \sum_{k=1}^{N} P@k \times \text{rel}(k) \right)$$
5. **Normalized Discounted Cumulative Gain (NDCG@K)**: Mengukur kualitas perankingan berdasarkan relevansi bergradasi (*graded relevance*, skala 0–3) dengan mendiskon kontribusi dokumen di posisi bawah:
   $$DCG@K = \sum_{i=1}^{K} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}, \quad NDCG@K = \frac{DCG@K}{IDCG@K}$$

### 2.8 Alasan Pemilihan Metode Berdasarkan Riset Terdahulu
Alasan ilmiah mendasari pemilihan arsitektur **Dual-Baseline (TF-IDF VSM + Okapi BM25) dengan Document-Level Aggregation**:
1. **Komparasi Standar Ilmiah (*Scientific Benchmarking*)**: Manning et al. (2008) menekankan bahwa evaluasi IR yang valid memerlukan pembanding (*baseline comparison*). Menghadirkan TF-IDF bersama BM25 menjawab pertanyaan riset fundamental mengenai efektivitas normalisasi panjang dokumen pada literatur akademik.
2. **Efisiensi Komputasi pada Skala Korpus Besar**: Baik TF-IDF (SciPy CSR) maupun BM25 (Inverted Index) memiliki kecepatan pencarian sub-detik ($< 100$ ms pada BM25) pada puluhan ribu dokumen tanpa memerlukan akselerasi GPU yang mahal.
3. **Transparansi dan Ketiadaan Halusinasi (*Explainability*)**: Model berbasis leksikal bersifat deterministik dan matematis; setiap dokumen yang muncul didukung oleh bukti potongan teks dan nomor halaman fisik dokumen asli.
4. **Eliminasi Bias Dokumen Panjang**: Adanya modul agregasi dokumen menjamin bahwa hasil pencarian beragam (*diverse*) dan adil antara slide perkuliahan ringkas dan buku teks/skripsi tebal.

### 2.9 Tolerant Retrieval: Typo Correction, Fuzzy Matching, dan Pemulihan Kueri Akademik
Manning et al. (2008) mendefinisikan *Tolerant Retrieval* sebagai teknik untuk menangani ketidaksempurnaan kueri pemakai yang timbul akibat kesalahan pengetikan (*typos*), variasi ejaan fonetik, maupun variasi format penulisan istilah khusus. Pada sistem temu kembali informasi akademik, ketergantungan murni pada pencocokan leksikal (*exact lexical match*) kerap menghasilkan fenomena *zero hits* (nihil hasil) ketika pengguna melakukan salah ketik satu huruf (misalnya: `"menggunkan"` alih-alih `"menggunakan"`, atau `"sentimen analisi"` alih-alih `"sentimen analisis"`).

Arsitektur Tolerant Retrieval yang diterapkan mengadopsi prinsip-prinsip utama sebagai berikut:
1. **Bukan Pengganti BM25 (*Pre-Retrieval Normalization Layer*)**: Tolerant Retrieval tidak menggantikan fungsi Okapi BM25 sebagai mesin perankingan utama. Modul ini beroperasi sebelum tahap *retrieval* untuk menormalisasi dan memulihkan representasi teks kueri:
   $$\text{Kueri Pengguna} \xrightarrow{\text{Analisis & Normalisasi}} \text{Kueri Baku / Efektif} \xrightarrow{\text{Okapi BM25}} \text{Perankingan Relevansi}$$
2. **Prinsip Prioritas Pencarian Eksak (*Exact-First Priority*)**: Untuk mencegah peningkatan *false positive*, sistem mengeksekusi pencarian eksak terlebih dahulu. Mekanisme *tolerant fallback* hanya dipicu apabila hasil pencarian eksak minim ($< 3$ dokumen) atau nilai skor kemiripan tertinggi berada di bawah ambang batas kecukupan (*adequacy threshold*).
3. **Pencocokan Fuzzy Damerau-Levenshtein Cepat**: Menggunakan jarak edit Damerau-Levenshtein yang menghitung operasi penyisipan (*insertion*), penghapusan (*deletion*), substitusi (*substitution*), dan transposisi dua karakter bersebelahan (*transposition*). Indeks panjang kata dan bigram atas 26.000+ kosa kata korpus menjamin waktu komputasi sub-milidetik ($< 2$ ms).
4. **Perlindungan Istilah Teknis (*Protected Technical Terms*)**: Simbol dan istilah pemrograman/akademik tertentu seperti `C++`, `C#`, `.NET`, `TF-IDF`, dan `R²` dilindungi oleh *tokenizer khusus* agar tidak mengalami distorsi karakter akibat pembersihan tanda baca standar.
5. **Ekspansi Singkatan dan Standarisasi Ejaan**: Memetakan singkatan akademik baku (misalnya: `NLP` $\rightarrow$ `Natural Language Processing`, `SVM` $\rightarrow$ `Support Vector Machine`, `APSI` $\rightarrow$ `Analisis dan Perancangan Sistem Informasi`) serta variasi ejaan bahasa Indonesia (`analisa` $\rightarrow$ `analisis`, `metoda` $\rightarrow$ `metode`, `sistim` $\rightarrow$ `sistem`).
6. **Transparansi dan Penjelasan (*Explainability & Audit Log*)**: Setiap transformasi kueri mencatat skor keyakinan (*confidence score* $\in [0.0, 1.0]$) dan riwayat perubahan kata (`source` $\rightarrow$ `target`) yang dapat diinspeksi pengguna pada antarmuka web.

### 2.10 Text Summarization: Graph Centrality (TextRank), Redundansi (MMR), dan Pendekatan Lintas Bahasa
Peringkasan teks otomatis (*Automatic Text Summarization*) merupakan salah satu pilar pemrosesan bahasa alami (NLP) yang bertujuan mengompresi dokumen panjang ke dalam representasi ringkas tanpa menghilangkan informasi esensial (Manning et al., 2008). Di ranah sistem temu kembali informasi akademik, penambahan fitur peringkasan teks berfungsi menjembatani jarak antara *retrieval* (menemukan dokumen) dan *comprehension* (memahami isi dokumen secara cepat).

Peringkasan teks secara umum terbagi menjadi dua paradigma:
1. **Peringkasan Abstraktif (*Abstractive Summarization*)**: Menghasilkan kalimat-kalimat baru hasil parafrasa menggunakan model generatif (seperti LLM/Transformer). Walaupun fleksibel, pendekatan ini rentan terhadap fenomena halusinasi (*factual hallucination*), memerlukan komputasi GPU yang mahal, dan kehilangan keterlacakan rujukan nomor halaman asli (*loss of page-level provenance*).
2. **Peringkasan Ekstraktif (*Extractive Summarization*)**: Mengidentifikasi dan mengekstrak kalimat-kalimat paling representatif langsung dari dokumen asli tanpa mengubah struktur kata. Pendekatan ini menjamin **100% kesahihan faktual (*zero hallucination*)**, dapat dikaitkan langsung dengan nomor halaman fisik dokumen sumber, serta sangat efisien dijalankan di lingkungan CPU (*low latency*).

Oleh karena itu, sistem ini mengadopsi pendekatan ekstraktif berbasis graf dengan kombinasi tiga pilar algoritma:
1. **Algoritma TextRank (Mihalcea & Tarau, 2004)**: Merupakan algoritma berbasis graf yang diadaptasi dari PageRank (Brin & Page, 1998). Kalimat-kalimat dokumen diposisikan sebagai simpul graf (*vertices* $V$), dan derajat keterkaitan antar-kalimat direpresentasikan sebagai sisi berbobot (*weighted edges* $E$). Bobot sisi $W_{ij}$ dihitung menggunakan kemiripan sudut kosinus (*Cosine Similarity*) dari representasi vektor TF-IDF kalimat:
   $$W_{ij} = \frac{\vec{S_i} \cdot \vec{S_j}}{\|\vec{S_i}\|_2 \|\vec{S_j}\|_2}$$
   Skor sentralitas TextRank dihitung secara iteratif menggunakan metode *Power Iteration* hingga konvergen dengan faktor redaman (*damping factor*) $d=0.85$:
   $$TR(S_i) = (1 - d) + d \sum_{S_j \in \text{Adj}(S_i)} \frac{W_{ji}}{\sum_{S_k \in \text{Adj}(S_j)} W_{jk}} TR(S_j)$$
   Kalimat yang memiliki koneksi semantik kuat dengan banyak kalimat penting lainnya akan memperoleh skor sentralitas tertinggi.
2. **Eliminasi Redundansi dengan Maximal Marginal Relevance (MMR) (Carbonell & Goldstein, 1998)**: Kelemahan utama pemeringkat graf murni adalah kecenderungan memilih beberapa kalimat yang membicarakan gagasan yang serupa (mengandung kata kunci dominan yang sama). Untuk mencegah pengulangan informasi, diterapkan metode MMR yang menyeimbangkan antara tingkat kepentingan/relevansi kalimat dengan kebaruan (*novelty*) terhadap kalimat yang telah terpilih sebelumnya ke dalam himpunan ringkasan $S$:
   $$MMR = \arg\max_{S_i \in C \setminus S} \left[ \lambda \cdot \text{Score}(S_i) - (1 - \lambda) \cdot \max_{S_j \in S} \text{Sim}(S_i, S_j) \right]$$
   di mana parameter $\lambda \in [0.0, 1.0]$ berfungsi mengatur *trade-off* keberagaman (nilai default empiris: $\lambda = 0.70$). Kalimat yang terpilih kemudian diurutkan kembali secara kronologis (*chronological reordering*) mengikuti alur asli kemunculannya di dokumen agar ringkasan mengalir runut dan alami.
3. **Peringkasan Berbasis Kueri Lintas Bahasa (*Query-Focused Cross-Lingual Evidence Extraction*)**: Pada skenario penelusuran di mana kueri pengguna (misalnya Bahasa Indonesia) mencari bukti dari artikel jurnal (Bahasa Inggris), pencocokan leksikal murni tidak memadai. Digunakan representasi ruang vektor semantik bersama (*multilingual shared semantic space*) yang memproyeksikan kueri $\vec{q}$ dan kandidat kalimat $\vec{s}_i$ ke ruang representasi yang sama, sehingga bukti kalimat yang paling menjawab kueri dapat diekstraksi secara presisi tanpa perlu menerjemahkan seluruh korpus secara paksa.

---

# III. ANALISIS DAN DESAIN SISTEM

## 3.1 Data yang Digunakan

### 3.1.1 Sumber Data Riil
Data yang digunakan dalam proyek ini merupakan dokumen akademik riil yang diperoleh secara legal dan etis dari sumber publik terbuka:
1. **OpenCourseWare Universitas Indonesia (OCW UI)** (`https://ocw.ui.ac.id`): Repositori bahan ajar resmi yang mencakup 14 fakultas lintas disiplin ilmu (Kedokteran, Teknik, MIPA, Ilmu Komputer, Hukum, Ekonomi & Bisnis, dll.).
2. **arXiv Open Access Scientific Archive** (`https://arxiv.org/api`): Repositori artikel riset pracetak berskala global dalam bidang Computer Science, Artificial Intelligence, dan Information Systems yang diakses via arXiv REST API.
3. **Directory of Open Access Journals (DOAJ)** & **CORE API**: Basis data artikel jurnal terakreditasi internasional yang menyediakan teks lengkap (*open-access full text*).
4. **Repositori Institusi Karya Ilmiah**: Kumpulan skripsi dan tesis mahasiswa yang dipublikasikan pada repositori institusi pendidikan tinggi.

### 3.1.2 Teknik Pengumpulan dan Ekstraksi Data
Pipeline pengumpulan data (*data ingestion pipeline*) dirancang secara modular:
1. **Automated Crawler & Collector**: Menggunakan pustaka `requests` dan `BeautifulSoup4` dengan sistem *rate-limiting* santun (delay 0.5–1 detik), penanganan sertifikat SSL, dan pencegahan duplikasi berbasis enkripsi SHA-256.
2. **PDF Text Extraction**: Menggunakan pustaka canggih `PyMuPDF` (`fitz`) dan `pdfplumber` untuk mengekstrak teks asli per halaman secara terstruktur.
3. **Deduplikasi Cerdas**: Setiap file PDF dihitung nilai hash SHA-256-nya sebelum disimpan. Jika hash telah ada di basis data, berkas dilewati (*duplicate skip*).

### 3.1.3 Karakteristik dan Statistik Data Terkini
Berdasarkan eksekusi pengumpulan data aktual yang tersimpan di dalam basis data [academic_ir.db](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/database/academic_ir.db):

| Kategori Korpus | Deskripsi Data | Format Sumber | Jumlah Dokumen | Jumlah Chunks Terindeks |
| :--- | :--- | :---: | :---: | :---: |
| **MATERIAL** | Bahan kuliah, slide, silabus, dan BRP dari 14 fakultas OCW UI | PDF, PPTX | 1.074 dokumen | 47.388 chunks |
| **RESEARCH** | Artikel jurnal ilmiah dan riset internasional (arXiv & CORE) | PDF | 169 dokumen | 5.776 chunks |
| **THESIS** | Skripsi, tesis, dan laporan tugas akhir komputasi & sistem informasi | PDF | 121 dokumen | 4.038 chunks |
| **TOTAL SISTEM** | **Koleksi Korpus Akademik Terpadu (*Unified Academic Corpus*)** | **PDF** | **1.364 dokumen** | **57.202 chunks** |

- **Total Ukuran Kosakata (*Vocabulary Size*):** **1.969.538 term** (kombinasi unigram dan bigram).
- **Dimensi Matriks TF-IDF:** Matriks *sparse* berukuran $(56.881 \times 1.969.538)$ baris dan kolom.

---

## 3.2 Analisis Kebutuhan Sistem

### 3.2.1 Kebutuhan Fungsional (*Functional Requirements*)
Kebutuhan fungsional mendefinisikan layanan operasional yang wajib disediakan oleh sistem perangkat lunak:

| Kode Kebutuhan | Nama Kebutuhan | Deskripsi Fungsional |
| :---: | :--- | :--- |
| **FR-01** | Pencarian Multi-Korpus Terpadu | Pengguna dapat memasukkan kata kunci kueri dalam bahasa Indonesia maupun Inggris untuk mencari seluruh kategori korpus sekaligus. |
| **FR-02** | Pemrosesan Kueri Dinamis | Sistem memproses teks kueri melalui pipeline pembersihan, penghapusan stopword dwibahasa, dan pemotongan kata dasar (*stemming*). |
| **FR-03** | Perankingan Relevansi Kosinus | Sistem menghitung bobot TF-IDF kueri, mengalikan dengan matriks korpus, dan mengembalikan dokumen dengan skor kemiripan tertinggi. |
| **FR-04** | Penyaringan Segi (*Faceted Filtering*) | Pengguna dapat menyaring hasil pencarian berdasarkan jenis dokumen (`MATERIAL`, `RESEARCH`, `THESIS`), rentang tahun publikasi, dan fakultas/departemen. |
| **FR-05** | Granularitas Nomor Halaman | Sistem menyajikan nomor halaman spesifik tempat ditemukannya potongan teks (*chunk*) yang relevan pada dokumen PDF. |
| **FR-06** | Pembuatan Cuplikan Cerdas (*Smart Snippet*) | Sistem membuat ringkasan cuplikan kontekstual dengan menyorot (*highlight*) term kueri yang cocok di dalam teks. |
| **FR-07** | Tampilan Detail Dokumen | Pengguna dapat melihat metadata komprehensif dokumen (penulis, abstrak, institusi, tahun, status ekstraksi, lisensi). |
| **FR-08** | Tautan Dokumen Sumber | Sistem menyediakan tautan langsung untuk mengunduh dokumen lokal atau mengakses URL repositori sumber asli. |
| **FR-09** | Pemantauan Kesehatan Sistem (*Health Check*) | Sistem menyediakan endpoint API `/api/health` dan `/api/stats` untuk memantau status indeks, jumlah memori, dan statistik korpus. |
| **FR-10** | Pengelolaan Koleksi Data | Administrator/pengembang dapat menjalankan skrip otomatis untuk memperbarui korpus, mengekstrak PDF baru, dan melatih ulang indeks TF-IDF. |
| **FR-11** | Tolerant Retrieval & Adaptive Fallback (Tahap II) | Sistem secara adaptif mendeteksi typo, variasi ejaan, dan singkatan; memprioritaskan pencarian eksak leksikal, dan memicu pemulihan kueri jika hasil eksak minim/nihil. |
| **FR-12** | Rekomendasi Kueri Cerdas (*Live Typo Autocomplete*) | Bilah pencarian (*Search Bar*) menampilkan dropdown saran kueri real-time, prompt "Mungkin maksud Anda", dan filter mode toleransi (*Auto / Always / Off*). |
| **FR-13** | Transparansi Transformasi (*Explainability Audit Log*) | Sistem menyediakan modal dialog audit log yang memaparkan riwayat transformasi kata (`source` $\rightarrow$ `target`), tingkat keyakinan (*confidence*), dan jenis transformasi. |
| **FR-14** | Peringkasan Teks Ekstraktif (*Document TextRank + MMR*) | Sistem menyediakan ringkasan intisari dokumen berbasis graf sentralitas kalimat TextRank dan eliminasi redundansi MMR yang sadar bahasa (*language-aware*). |
| **FR-15** | Ekstraksi Bukti Relevan Kueri Lintas Bahasa (*Query-Focused Evidence*) | Pengguna dapat melihat bukti kalimat-kalimat dokumen yang paling relevan menjawab kueri pencarian (termasuk kueri bahasa Indonesia pada dokumen berbahasa Inggris). |
| **FR-16** | Keterlacakan Nomor Halaman & Caching Ringkasan | Setiap butir kalimat ringkasan menyertakan nomor halaman fisik dokumen sumber asli dan diakselerasi melalui persistensi cache SQLite untuk akses instan (< 5 ms). |
| **FR-17** | Pembaca Dokumen Utuh Multi-Halaman (*In-App Full Document Reader*) | Pengguna dapat membaca keseluruhan halaman fisik dokumen langsung di aplikasi web melalui endpoint `/api/documents/{id}/pages`, dengan kontrol pagination, continuous scroll, dan penyorotan istilah kueri. |
| **FR-18** | Penyajian Dokumen Utuh & Peta Halaman Relevan | Kartu hasil pencarian menyajikan identitas dokumen utuh: abstrak resmi dokumen, total halaman fisik, serta pill nomor halaman yang relevan (`Relevan di Hal. X, Y, Z`). |

### 3.2.2 Kebutuhan Non-Fungsional (*Non-Functional Requirements*)
Kebutuhan non-fungsional menetapkan batasan kualitas arsitektural perangkat lunak:

| Dimensi Kualitas | Parameter & Batasan Kebutuhan |
| :--- | :--- |
| **Kinerja (*Performance*)** | Waktu respons pencarian rata-rata (*query response time*) harus di bawah **250 milidetik** untuk pencarian pada 57.000+ chunks. |
| **Skalabilitas (*Scalability*)** | Arsitektur backend FastAPI dan indeks CSR *sparse matrix* harus mampu menangani penambahan hingga 100.000+ chunks tanpa penurunan memori kritis. |
| **Ketersediaan (*Availability*)** | API backend dan antarmuka web beroperasi dengan arsitektur nir-status (*stateless service*) yang mudah di-deploy ulang. |
| **Kegunaan (*Usability*)** | Antarmuka pengguna mengadopsi standar modern *responsive design* berbasis Tailwind CSS & komponen shadcn/ui dengan waktu muat halaman (*First Contentful Paint*) < 1.0 detik. |
| **Integritas Data (*Data Integrity*)** | Integritas dokumen dijamin melalui verifikasi enkripsi SHA-256 dan relasi kunci asing (*Foreign Key*) pada skema basis data SQLite. |

---

## 3.3 Desain Sistem

### 3.3.1 Arsitektur Sistem (*System Architecture*)
Perangkat lunak Academic IR dirancang menggunakan arsitektur berlapis modular (*Three-Tier Decoupled Architecture with Tolerant Pre-Retrieval Layer*):
1. **Presentation Tier (Frontend)**: Dibangun menggunakan **Next.js 15 (React 19)**, **Tailwind CSS**, dan pustaka antarmuka **shadcn/ui**, berkomunikasi secara asinkron (*REST/JSON*) ke backend pada port 3000. Dilengkapi *Live Suggestions Dropdown*, *Tolerant Mode Selector* (*Auto/Always/Off*), *Recovery Banner*, *Audit Log Dialog*, serta modal pembaca dokumen utuh (**In-App Full Document Reader Dialog**) dan modal peringkasan cerdas (**Summary Dialog**).
2. **Application & Service Tier (Backend)**: Menggunakan **FastAPI (Python 3.10+)** pada port 8000 yang mengorkestrasi:
   - **Tolerant Retrieval Subsystem (`src/retrieval/tolerant/`)**: Modul normalisasi kueri, pencocokan fuzzy Damerau-Levenshtein, penanganan singkatan/ejaan, perlindungan istilah teknis, serta pengendali *adaptive fallback*.
   - **Primary Lexical Retrieval Engine**: Mesin perankingan dual-baseline **Okapi BM25** dan **TF-IDF Vector Space Model** yang terintegrasi dengan modul agregasi dokumen (`max+2nd`).
   - **Full Document Delivery & Reader Service**: Endpoint `GET /api/documents/{document_id}/pages` untuk menyajikan seluruh teks halaman fisik dengan indikator kecocokan istilah kueri (*has_match*).
   - **Text Summarization Subsystem (`src/summarization/`)**: Peringkasan ekstraktif TextRank + MMR dan ekstraksi bukti semantik lintas bahasa.
3. **Data & Model Tier (Persistence Layer)**: Terdiri dari basis data relasional **SQLite (`academic_ir.db`)** untuk metadata dokumen (1.364 baris), teks halaman fisik (`pages` - 50.218 baris), unit pencarian granular (`chunks` - 57.202 baris), dan cache ringkasan (`document_summaries`), serta serialisasi indeks **BM25 (`models/bm25_v1/`)** dan **TF-IDF (`models/`)**.

```mermaid
graph TD
    subgraph Presentation_Tier [Presentation Tier - Port 3000]
        UI[Next.js 15 Web Application]
        SB[Search Bar: Live Typo Autocomplete]
        TMS[Tolerant Mode Selector: Auto/Always/Off]
        FT[Faceted Filters Sidebar]
        RB[Tolerant Recovery Banner]
        AUD[Explainability Audit Dialog]
        RC[Result Cards: Full Abstract & Matched Pages]
        RDR[In-App Document Reader: DocumentReaderDialog]
        SUMM_UI[AI Summarization Dialog: SummaryDialog]
    end

    subgraph Application_Tier [Application & IR Service Tier - Port 8000]
        API[FastAPI REST API Server]
        
        subgraph Tolerant_Layer [Tolerant Retrieval Layer: Tahap II]
            TPROC[Tolerant Query Processor]
            FUZZY[Fast Damerau-Levenshtein Matcher]
            FBC[Exact-First Fallback Controller]
            DICT[Abbreviation & Protected Terms Dict]
        end
        
        QP[Query Preprocessing Pipeline]
        BM25_ENG[Okapi BM25 Primary Engine]
        TFIDF_ENG[TF-IDF VSM Secondary Engine]
        AGG[Document-Level Aggregator: max+2nd]
        SNIP[Smart Snippet Generator]
        PAGES_API[Pages Reader Endpoint: /api/documents/id/pages]
        SUMM_ENG[TextRank + MMR Summarizer Engine]
    end

    subgraph Storage_Tier [Data & Model Persistence Tier]
        DB[(SQLite Database - academic_ir.db)]
        DOCS[Table: documents - 1,364 rows]
        PAGES[Table: pages - 50,218 rows]
        CHUNKS[Table: chunks - 57,202 rows]
        CACHE_SUMM[Table: document_summaries]
        
        BM25_IDX[BM25 Inverted Index: 56.8k Chunks]
        TFIDF_IDX[TF-IDF Matrix & Vectorizer: 1.9M Vocab]
    end

    UI -->|HTTP GET /api/tolerant/suggest| API
    UI -->|HTTP GET /api/search?tolerant_mode=...| API
    RDR -->|HTTP GET /api/documents/id/pages?q=...| PAGES_API
    SUMM_UI -->|HTTP GET /api/documents/id/summary| SUMM_ENG
    
    API --> TPROC
    TPROC --> FUZZY
    TPROC --> DICT
    TPROC --> FBC
    
    FBC -->|1. Exact Query First| BM25_ENG
    FBC -->|2. Fallback Normalized Query if Zero/Poor Hits| BM25_ENG
    
    BM25_ENG --> BM25_IDX
    API --> TFIDF_ENG
    TFIDF_ENG --> TFIDF_IDX
    
    BM25_ENG --> AGG
    TFIDF_ENG --> AGG
    AGG -->|Fetch Document Metadata & Matched Pages| DB
    PAGES_API -->|Stream All Pages| PAGES
    SUMM_ENG -->|Read Pages & Cache Summary| CACHE_SUMM
    
    DB --> DOCS
    DB --> PAGES
    DB --> CHUNKS
    AGG --> SNIP
    API -->|JSON Results + Tolerant Audit Metadata| UI
```

---

### 3.3.2 Pemodelan Sistem Machine Learning (UML)

#### A. Use Case Diagram
Diagram use case memodelkan interaksi antara dua aktor utama (*Mahasiswa/Peneliti* dan *Administrator Sistem*) dengan kapabilitas fungsional perangkat lunak:

```mermaid
graph LR
    User((Pengguna / Peneliti))
    Admin((Administrator Sistem))

    UC1[Pencarian Kueri Terpadu]
    UC2[Filter Berdasarkan Jenis Korpus]
    UC3[Filter Berdasarkan Fakultas / Tahun]
    UC4[Melihat Cuplikan Teks & Nomor Halaman]
    UC5[Membuka Detail & Tautan Sumber Dokumen]
    UC6[Monitoring Statistik Korpus & Health]
    UC7[Menjalankan Scraper & Pengumpulan Data]
    UC8[Melatih & Memperbarui Indeks TF-IDF]

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5

    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
```

#### B. Sequence Diagram (Alur Pencarian Real-Time)
Diagram sekuensial menggambarkan interaksi pertukaran pesan antar-objek saat pengguna melakukan pencarian dokumen:

```mermaid
sequenceDiagram
    autonumber
    actor Pengguna
    participant UI as Next.js Frontend
    participant API as FastAPI Backend
    participant Pipe as Preprocessing Pipeline
    participant SE as Search Engine
    participant TF as TF-IDF Index (Model)
    participant DB as SQLite Database

    Pengguna->>UI: Mengetik kueri "analisis use case" & tekan Cari
    UI->>API: GET /api/search?q=analisis+use+case&top_k=20
    API->>Pipe: transform(query_text)
    Note over Pipe: Case folding, Stopwords removal, Sastrawi/NLTK Stemming
    Pipe-->>API: clean_query_text
    API->>SE: search(clean_query, top_k=20)
    SE->>TF: transform([clean_query])
    TF-->>SE: query_vector (1 x 1,969,538)
    SE->>TF: compute_cosine_similarity(query_vector, matrix)
    TF-->>SE: array of similarity scores & top_k chunk_indices
    SE->>DB: get_chunks_and_docs_by_ids(chunk_ids)
    DB-->>SE: rows (metadata dokumen, nomor halaman, teks chunk)
    SE->>SE: generate_snippets(clean_text, query_tokens)
    SE-->>API: ranked_results_list
    API-->>UI: 200 OK (JSON Response)
    UI-->>Pengguna: Merender Kartu Hasil dengan Skor, Halaman, & Tautan
```

---

### 3.3.3 Rancangan Basis Data (Entity Relationship Diagram — ERD)
Basis data dirancang menggunakan SQLite dengan skema terpusat yang mendukung penyimpanan terstruktur dari tingkat dokumen makro hingga unit *chunk* mikro:

```mermaid
erDiagram
    DOCUMENTS ||--o{ PAGES : "has many (1:N)"
    DOCUMENTS ||--o{ CHUNKS : "has many (1:N)"
    DOCUMENTS ||--o{ INGESTION_LOGS : "tracks (1:N)"
    DOCUMENTS ||--o{ DOCUMENT_SUMMARIES : "caches (1:N)"

    DOCUMENTS {
        text document_id PK "Contoh: MAT-000259"
        text document_type "MATERIAL / RESEARCH / THESIS"
        text title "Judul Dokumen Lengkap"
        text abstract "Abstrak Dokumen"
        text authors "JSON Array Penulis"
        text institution "Universitas / Penerbit"
        text department "Fakultas / Program Studi"
        text course "Nama Mata Kuliah (Khusus Material)"
        integer year "Tahun Terbit"
        text language "id / en"
        real language_confidence "Tingkat keyakinan bahasa"
        text keywords "JSON Array Kata Kunci"
        text source "OCW_UI / ARXIV / DOAJ / REPO"
        text source_url "Tautan Web Sumber"
        text fulltext_url "Tautan Unduh PDF"
        text local_path "Path Penyimpanan Berkas Lokal"
        text file_type "pdf / pptx"
        integer file_size "Ukuran berkas dalam bytes"
        integer page_count "Jumlah Halaman"
        text sha256 UK "Hash Integritas & Unik"
        text extraction_status "SUCCESS / FAILED"
        text collection_status "READY_FOR_INDEXING"
        text collected_at "Timestamp Pengambilan"
    }

    PAGES {
        integer id PK "Auto Increment"
        text document_id FK "Relasi ke DOCUMENTS"
        integer page_number "Nomor Halaman Fisik (1-N)"
        text raw_text "Teks Asli Hasil Ekstraksi PDF"
        text clean_text "Teks Setelah Normalisasi"
        integer word_count "Jumlah Kata Halaman"
    }

    CHUNKS {
        text chunk_id PK "Contoh: CHK-MAT-000259-001"
        text document_id FK "Relasi ke DOCUMENTS"
        integer page_start "Nomor Halaman Awal"
        integer page_end "Nomor Halaman Akhir"
        integer chunk_index "Urutan Indeks Chunk"
        text raw_text "Teks Asli Chunk"
        text clean_text "Teks Bersih Siap Indeks"
        integer word_count "Jumlah Kata Chunk"
    }

    INGESTION_LOGS {
        integer id PK "Auto Increment"
        text document_id FK "Relasi ke DOCUMENTS"
        text stage "DOWNLOAD / EXTRACT / CHUNK / INDEX"
        text status "SUCCESS / FAILED / SKIPPED"
        text message "Rincian Log Eksekusi"
        text created_at "Timestamp Kejadian"
    }

    DOCUMENT_SUMMARIES {
        integer id PK "Auto Increment"
        text document_id FK "Relasi ke DOCUMENTS"
        text summary_type "document / query_focused"
        text query_text "Kueri spesifik (opsional)"
        text summary_text "Teks ringkasan esensial"
        text language "id / en / mixed"
        text algorithm "textrank_mmr / multilingual_embedding_mmr"
        text key_sentences_json "JSON Array butir kalimat & skor"
        text source_pages_json "JSON Array nomor halaman sumber"
        integer sentence_count "Jumlah kalimat terpilih"
        real processing_time_ms "Waktu komputasi ms"
        text created_at "Timestamp Pembuatan"
    }
```

#### Kamus Data (*Data Dictionary*)
1. **Tabel `documents`**: Menyimpan entitas induk dokumen akademik lengkap dengan metadata bibliografi, sumber asal, dan hash SHA-256 untuk memastikan tidak ada redundansi berkas fisik.
2. **Tabel `pages`**: Menyimpan representasi teks per halaman individual PDF. Berguna untuk pelacakan halaman asli dan pratinjau halaman visual.
3. **Tabel `chunks`**: Menyimpan unit data terkecil yang dijadikan baris dalam matriks TF-IDF. Setiap chunk memiliki rentang halaman awal (`page_start`) dan akhir (`page_end`) serta teks hasil pembersihan.
4. **Tabel `ingestion_logs`**: Menyimpan jejak audit (*audit trail*) otomatis proses pengunduhan, ekstraksi teks, dan penanganan eror sistem.
5. **Tabel `document_summaries`**: Menyimpan hasil komputasi ringkasan ekstraktif (TextRank + MMR) dan bukti relevan kueri lintas bahasa agar permintaan berulang dapat disajikan secara instan dari cache (< 5 ms) tanpa komputasi graf ulang.

---

### 3.3.4 Flowchart Algoritma Machine Learning

#### A. Pipeline Preprocessing Data & Pelatihan Model (*Training Phase*)
Flowchart berikut menggambarkan alur konversi dari berkas PDF mentah menjadi model ruang vektor terindeks:

```mermaid
flowchart TD
    Start([Mulai Ingestion Korpus]) --> ScanPDF[Pindai Berkas PDF dari Koleksi]
    ScanPDF --> CheckHash{Hitung SHA-256<br>Ada di Database?}
    CheckHash -- Ya --> SkipDoc[Lewati / Abaikan Dokumen Duplikat]
    CheckHash -- Tidak --> ExtractText[Ekstraksi Teks per Halaman via PyMuPDF]
    
    ExtractText --> Chunking[Segmentasi Teks Menjadi Chunks<br>Window 200-400 Kata + Overlap 50 Kata]
    Chunking --> LangDetect{Deteksi Bahasa Teks}
    
    LangDetect -- Bahasa Indonesia --> CaseFoldID[Case Folding & Normalisasi Karakter]
    CaseFoldID --> StopwordID[Hapus Stopwords Bahasa Indonesia - Sastrawi 123 Kata]
    StopwordID --> StemID[Stemming Kata Dasar - Algoritma Sastrawi]
    
    LangDetect -- Bahasa Inggris --> CaseFoldEN[Case Folding & Normalisasi Karakter]
    CaseFoldEN --> StopwordEN[Hapus Stopwords Bahasa Inggris - NLTK 198 Kata]
    StopwordEN --> StemEN[Stemming Kata Dasar - NLTK Snowball Stemmer]

    StemID --> SaveDB[Simpan Metadata & Chunks ke SQLite]
    StemEN --> SaveDB

    SaveDB --> MoreFiles{Ada PDF Lain?}
    MoreFiles -- Ya --> ScanPDF
    MoreFiles -- Tidak --> FitTFIDF[Fit TF-IDF Vectorizer<br>N-gram 1-2, Min-DF 2, Sublinear TF]
    
    FitTFIDF --> BuildMatrix[Bentuk Matriks VSM Sparse SciPy CSR<br>Dimensi: 56.881 x 1.969.538]
    BuildMatrix --> SaveArtifacts[Simpan Biner ke models/:<br>tfidf_vectorizer.pkl, tfidf_matrix.npz, chunk_ids.pkl]
    SaveArtifacts --> EndTrain([Selesai Pelatihan Indeks])
```

#### B. Pipeline Pemrosesan Kueri & Perankingan (*Retrieval, Aggregation & Ranking Phase with Tolerant Recovery*)
Flowchart berikut menunjukkan alur pencarian ketika pengguna memasukkan kueri, analisis toleransi typo, eksekusi exact-first, pemilihan model retrieval, hingga agregasi dokumen:

```mermaid
flowchart TD
    StartQ([Pengguna Memasukkan Kueri]) --> CheckEmpty{Kueri Kosong?}
    CheckEmpty -- Ya --> ReturnEmpty[Kembalikan Hasil Kosong]
    CheckEmpty -- Tidak --> ParseMode{Mode Toleransi?<br>Auto / Always / Off}
    
    ParseMode -- Always --> NormForce[Normalisasi Kueri Paksa: Typo, Singkatan, Ejaan]
    NormForce --> ChooseModel
    
    ParseMode -- Off --> ChooseModel[Pencarian Eksak Murni]
    
    ParseMode -- Auto (Default) --> ExecExact[Eksekusi Pencarian Eksak Pertama Kali]
    ExecExact --> CheckAdequate{Hasil Eksak Memadai?<br>Total >= 3 & Skor Cukup}
    CheckAdequate -- Ya --> KeepExact[Gunakan Hasil Eksak: Fallback Tidak Dipicu]
    KeepExact --> AggregateDocs
    
    CheckAdequate -- Tidak --> CheckModifiable{Kueri Memiliki Typo / Singkatan / Ejaan?}
    CheckModifiable -- Ya --> FallbackNorm[Picu Tolerant Fallback:<br>Normalisasi ke Kueri Baku]
    FallbackNorm --> ChooseModel
    CheckModifiable -- Tidak --> KeepExact
    
    ChooseModel -- Okapi BM25 (Utama) --> TokenBM25[Lookup Inverted Index BM25]
    TokenBM25 --> BM25Score[Kalkulasi Skor Okapi BM25: k1=1.5, b=0.75]
    
    ChooseModel -- TF-IDF VSM (Sekunder) --> VectorizeQ[Transformasi Kueri Vektor TF-IDF]
    VectorizeQ --> CosineSim[Kalkulasi Cosine Similarity Matriks CSR]
    
    BM25Score --> CandidatePool[Ambil Candidate Pool: candidate_k = 500]
    CosineSim --> CandidatePool
    
    CandidatePool --> FetchMeta[Ambil Metadata Kandidat dari Basis Data SQLite]
    FetchMeta --> ApplyFilters{Ada Filter Pengguna?<br>Jenis / Tahun / Bahasa}
    ApplyFilters -- Ya --> FilterCandidates[Saring Kandidat Sesuai Filter di Pool]
    ApplyFilters -- Tidak --> AggregateDocs[Modul Agregasi Dokumen: max+2nd]
    FilterCandidates --> AggregateDocs
    
    AggregateDocs --> GroupByDoc[Kelompokkan Chunk Berdasarkan document_id]
    GroupByDoc --> CalcDocScore[Hitung Skor Dokumen: max+2nd]
    CalcDocScore --> PickBest[Pilih Bukti Halaman & Snippet dari Best Chunk]
    PickBest --> SortDocs[Urutkan Dokumen Berdasarkan Skor Teragregasi]
    SortDocs --> TopKDocs[Ambil Top-K Dokumen Teratas - default: 10/20]
    
    TopKDocs --> AttachAudit[Lampirkan Tolerant Metadata & Audit Log Transformasi]
    AttachAudit --> ReturnJSON[Kirim Paket Respons JSON ke Frontend Next.js]
    ReturnJSON --> DisplayUI[Render Hasil Pencarian + Recovery Banner di Web]
    DisplayUI --> EndQ([Selesai])
```

---

### 3.3.5 Desain Antarmuka Sistem (*User Interface Design*)
Antarmuka pengguna didesain dengan prinsip kesederhanaan, keterbacaan tinggi (*high legibility*), dan responsif terhadap perangkat desktop maupun mobile. 

#### A. Wireframe / Mockup Tata Letak (*Layout Architecture*)
```text
+----------------------------------------------------------------------------------------------------+
|  [Logo Academic IR]       Beranda     Tentang     Dokumentasi API          [Status: 56,881 Chunks] |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|                            ACADEMIC INFORMATION RETRIEVAL SYSTEM                                   |
|               Pencarian Terpadu Bahan Kuliah, Jurnal Penelitian, dan Skripsi / Tesis               |
|                                                                                                    |
|    +--------------------------------------------------------+ +------------------+ +-----------+   |
|    |  [Ikon Cari]  menggunkan bert                          | | [Mode: Auto v]   | | [ CARI ]  |   |
|    +--------------------------------------------------------+ +------------------+ +-----------+   |
|    |  DROPDOWN SARAN REKOMENDASI CERDAS (POP-OVER):                                            |   |
|    |  [*] Mungkin maksud Anda: "menggunakan bert" (97% match) -> [ Gunakan Saran Ini ]        |   |
|    |  [Q] menggunakan bert          [Typo: menggunkan -> menggunakan]                         |   |
|    |  [Q] Natural Language Proc...  [Singkatan: NLP]                                           |   |
|    +-------------------------------------------------------------------------------------------+   |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
| PANEL FILTER (KIRI)                 | HASIL PENCARIAN (KANAN)                                      |
|                                     |                                                              |
| Mode Toleransi Kueri:               | +----------------------------------------------------------+ |
| (*) Otomatis (Fallback)             | | [SPARKLE] Menampilkan hasil untuk: "menggunakan bert"    | |
| ( ) Selalu Aktif                    | | Cari "menggunkan bert" sebagai gantinya (tanpa toleransi)| |
| ( ) Nonaktif (Eksak Saja)           | |                          [ Lihat Detail Audit & Log ]    | |
|                                     | +----------------------------------------------------------+ |
| Model Retrieval:                    | Ditemukan 15 hasil relevan (BM25: 0.08 detik)                |
| (*) Okapi BM25 (Utama)              |                                                              |
| ( ) TF-IDF VSM (Baseline A)         | +----------------------------------------------------------+ |
|                                     | | [RESEARCH] [CORE OA] [Sangat Relevan - 1.4820]            | |
| Kategori Korpus:                    | | Analisis Sentimen Ulasan Menggunakan Model BERT          | |
| [X] Semua Korpus                    | | Penulis: Tim Peneliti CS UI | Tahun: 2023               | |
| [ ] Bahan Kuliah (Material)         | | [Relevan di Hal. 4, 5, 8]  [26 Hal. Total]  [ID]         | |
| [ ] Jurnal Riset (Research)         | | Abstrak Dokumen Utuh:                                     | |
| [ ] Skripsi / Tesis (Thesis)        | | "Penelitian ini mengkaji penerapan model BERT untuk..."  | |
|                                     | | [ Baca Dokumen Lengkap ]  [ Ringkasan AI ]  [ Tautan ]  | |
| [ Reset Seluruh Filter ]            | +----------------------------------------------------------+ |
|                                     |                                                              |
+----------------------------------------------------------------------------------------------------+
|  Footer: Academic IR Project © 2026 — Kelompok [Nama] — Program Studi Ilmu Komputer                |
+----------------------------------------------------------------------------------------------------+
```

#### B. Fitur Unggulan Antarmuka
1. **Search Bar Cerdas dengan Live Typo Autocomplete**: Input teks pencarian dilengkapi dengan pendeteksi salah ketik real-time berkecepatan tinggi (*debounced 220 ms*). Ketika pengguna mengetik kueri dengan typo atau singkatan, dropdown interaktif langsung muncul menampilkan prompt *"Mungkin maksud Anda: [kueri saran]"* lengkap dengan persentase skor keyakinan dan navigasi keyboard (`↑`, `↓`, `Enter`, `Esc`).
2. **Selektor Mode Toleransi Langsung (*Quick Tolerant Mode Switcher*)**: Tersemat langsung di samping bilah pencarian dan panel filter. Memungkinkan pengguna beralih antara mode *Otomatis (Fallback)*, *Selalu Aktif*, dan *Nonaktif (Eksak Murni)* dalam satu kali klik untuk keperluan komparasi pengujian.
3. **Banner Pemulihan Kueri (*Tolerant Recovery Banner*)**: Memberikan transparansi jika kueri mengalami koreksi otomatis (*"Menampilkan hasil untuk: 'menggunakan'"*), lengkap dengan opsi satu klik untuk mencari kueri asli tanpa toleransi.
4. **Modal Dialog Audit Log & Explainability**: Menampilkan rincian teknis proses transformasi kueri: kueri asal $\rightarrow$ kueri efektif, status fallback, confidence score, dan pemetaan kata per kata sesuai prinsip keterjelasan (*explainability*).
5. **Badge Metadata & Relevansi Dokumen Utuh**: Setiap kartu hasil dilengkapi badge warna kategori korpus, skor relevansi kualitatif (*Sangat Relevan / Relevan / Cukup Relevan*), jumlah total halaman fisik, serta daftar nomor halaman yang membahas kueri (`Relevan di Hal. 1, 4, 10`).
6. **Penyajian Abstrak Dokumen Resmi**: Menampilkan teks abstrak dokumen utuh asli pada kartu hasil pencarian, menggantikan potongan teks acak yang terfragmentasi.
7. **In-App Full Document Reader (`DocumentReaderDialog`)**: Pengguna dapat membaca keseluruhan halaman fisik dokumen langsung di dalam aplikasi tanpa harus mengunduh file PDF besar atau meninggalkan halaman web. Mendukung navigasi halaman fisik (*Sebelumnya / Selanjutnya / Jump to Page*), *continuous scrolling*, dan penyalinan teks per halaman.
8. **Penyorotan Kata Kunci Otomatis (*Query-Term Highlighting*)**: Istilah kueri pencarian otomatis disorot dengan latar belakang kuning pada seluruh halaman teks dokumen yang sedang dibaca di dalam reader.
9. **Pintasan Halaman Relevan (*Quick-Jump Chips*)**: Bilah kontrol pembaca dokumen menyediakan tombol-tombol chip halaman relevan (`[Hal. 1] [Hal. 4] [Hal. 10]`) yang dapat diklik untuk melompat langsung ke halaman yang memuat bukti jawaban kueri.
10. **Akses Langsung ke Peringkasan AI (*Seamless AI Summarization Handoff*)**: Pengguna dapat beralih dalam satu klik dari pembaca dokumen ke modal peringkasan cerdas TextRank + MMR, atau sebaliknya.

#### C. Wireframe Modal Pembaca Dokumen Utuh (*In-App Full Document Reader Dialog*)
```text
+----------------------------------------------------------------------------------------------------+
| [Buku] Pembaca Dokumen Lengkap                                                               [ X ] |
| Judul: Analisis Perancangan Sistem Informasi Berorientasi Objek                                    |
| [BAHAN KULIAH]  [OCW UI]  [2023]  [26 Halaman Fisik]  [Bahasa: ID]                                 |
+----------------------------------------------------------------------------------------------------+
| Navigasi: [ < Sebelumnya ]  Hal. 4 dari 26  [ Selanjutnya > ]  | Lompat ke Hal: [ 4 ] [ Go ]       |
| Halaman Relevan Kueri: [Hal. 1] [*Hal. 4*] [Hal. 8] [Hal. 15]  | Mode: [Per Halaman | Semua Hal]   |
+----------------------------------------------------------------------------------------------------+
| +------------------------------------------------------------------------------------------------+ |
| | [KOTAK ABSTRAK RESMI DOKUMEN]                                                                  | |
| | Dokumen ini membahas tahapan analisis dan perancangan sistem berorientasi objek menggunakan... | |
| +------------------------------------------------------------------------------------------------+ |
|                                                                                                    |
| HALAMAN 4 (412 kata):                                                                              |
| "...Pada tahapan ini, [use case diagram] digunakan untuk memodelkan interaksi antara [aktor] dan   |
| [sistem informasi]. Setiap [use case] merepresentasikan fungsionalitas utama yang disediakan..."   |
|                                                                                                    |
| (Catatan: Kata kunci kueri di atas otomatis tersorot kuning / highlighted)                         |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
| [ Sparkles: Ringkas Dokumen Ini ]   [ Unduh / Buka Dokumen Asli ]                  [ Tutup Reader] |
+----------------------------------------------------------------------------------------------------+
```

---

## 3.4 Desain Pengujian dan Evaluasi

### 3.4.1 Desain Pengujian Perangkat Lunak (*Black-box Testing Plan*)
Pengujian fungsionalitas sistem dilakukan menggunakan metode pengujian kotak hitam (*Black-box Testing*) untuk memvalidasi bahwa setiap modul bekerja sesuai spesifikasi kebutuhan perangkat lunak tanpa memandang kode internal:

| ID Uji | Modul / Skenario Pengujian | Masukan (*Input*) | Tindakan Pengujian | Keluaran yang Diharapkan (*Expected Output*) | Kriteria Keberhasilan |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Pencarian Normal Kueri Tunggal | Kueri: `"algoritma"` | Pengguna mengetik kueri dan menekan tombol *Cari* | Sistem menampilkan daftar kartu hasil relevan yang memuat term "algoritma" dengan skor terurut menurun. | Lolos jika kartu hasil muncul dan skor terurut |
| **TC-02** | Pencarian Multi-Kata Dwibahasa | Kueri: `"machine learning sistem pakar"` | Pengguna mengirimkan kueri gabungan Bahasa Inggris dan Indonesia | Pipeline preprocessing memisahkan stopword kedua bahasa, melakukan stemming ganda, dan mengembalikan hasil akurat. | Lolos jika kueri dwibahasa diproses tanpa eror |
| **TC-03** | Pencarian Kueri Kosong / Spasi | Kueri: `"   "` (hanya spasi) | Pengguna menekan tombol cari tanpa memasukkan karakter valid | Sistem tidak mengirim request pencarian ke backend dan menampilkan pesan peringatan ramah bagi pengguna. | Lolos jika tidak terjadi crash atau blank page |
| **TC-04** | Penyaringan Segi (*Facet Filter*) | Centang filter: `document_type = 'MATERIAL'` | Pengguna mencentang kotak filter kategori bahan kuliah | Seluruh kartu hasil yang ditampilkan otomatis hanya memiliki kategori `MATERIAL`. Hasil riset & skripsi disembunyikan. | Lolos jika 100% kartu yang tampil bertipe MATERIAL |
| **TC-05** | Penyaringan Rentang Tahun | Filter slider: `Tahun >= 2022` | Pengguna menggeser pembatas tahun ke angka 2022 | Hanya dokumen yang diterbitkan pada tahun 2022 atau setelahnya yang ditampilkan di layar. | Lolos jika tidak ada dokumen bertahun < 2022 |
| **TC-06** | Pemeriksaan Integritas Halaman | Klik tautan dokumen sumber | Pengguna mengklik nomor halaman dan tautan berkas | Berkas PDF terbuka pada tab baru atau mengunduh berkas fisik lokal sesuai path yang tersimpan. | Lolos jika URL berkas valid dan dapat diakses |
| **TC-07** | Endpoint Health Check API | `GET /api/health` | Permintaan HTTP GET via browser atau Postman | Mengembalikan status HTTP 200 OK dengan payload JSON: `{"status": "ok", "index_loaded": true, "message": "Index loaded with 56881 chunks."}` | Lolos jika HTTP status 200 dan format JSON valid |
| **TC-08** | Penanganan Kueri Tanpa Relevansi | Kueri: `"xyzqwerty12345nonexistent"` | Pengguna mencari istilah sembarang yang tidak ada di korpus | Sistem menampilkan pesan informasi: *"Tidak ditemukan dokumen yang cocok dengan kueri Anda"* dengan skor 0. | Lolos jika UI menampilkan fallback state dengan rapi |
| **TC-09** | Pengalihan Model Retrieval | Param: `retrieval_mode = 'bm25'` | Pengguna memilih model BM25 pada panel sidebar | Backend memproses kueri menggunakan algoritma Okapi BM25 dan merender skor BM25 teragregasi. | Lolos jika hasil pencarian diperbarui sesuai model BM25 |
| **TC-10** | Agregasi Dokumen & Anti-Duplikasi | Kueri dengan dokumen tebal | Pengguna mencari topik yang memuat banyak chunk dalam satu dokumen | Sistem mengelompokkan chunk berdasarkan `document_id`. Setiap dokumen hanya muncul 1 kali dengan bukti halaman terbaik (`best_page_start`). | Lolos jika tidak ada dokumen dengan ID ganda di daftar hasil |
| **TC-11** | Endpoint Metadata Provenance Korpus | `GET /api/provenance` | Permintaan HTTP GET via browser atau API client | Mengembalikan payload JSON daftar sumber data resmi (OCW UI, arXiv, DOAJ) beserta jenis akses (`public/open_access`) dan lisensinya. | Lolos jika HTTP status 200 dan data provenance valid |
| **TC-12** | Rekomendasi Live Typo pada Search Bar | Ketik: `"menggunkan"` | Pengguna mengetik kueri salah ketik pada Search Bar | Dropdown saran otomatis muncul dengan teks "Mungkin maksud Anda: menggunakan" dan badge kategori Typo (confidence 97%). | Lolos jika dropdown saran muncul interaktif |
| **TC-13** | Mekanisme Fallback Otomatis Kueri Typo | Kueri: `"menggunkan bert"`, Mode: `auto` | Pengguna mencari kueri yang mengalami typo | Sistem mendeteksi hasil eksak minim, memicu fallback ke kueri baku "menggunakan BERT", mengembalikan 15 dokumen, dan merender Recovery Banner. | Lolos jika kueri typo dipulihkan dan dokumen relevan muncul |
| **TC-14** | Pemulihan Singkatan & Ejaan Baku | Kueri: `"NLP"`, `"analisa sentimen"` | Pengguna mengirimkan singkatan atau variasi ejaan | Sistem mengenali singkatan "NLP" -> "Natural Language Processing" dan ejaan "analisa" -> "analisis" tanpa kesalahan interpretasi. | Lolos jika kueri dipetakan ke bentuk baku |
| **TC-15** | Perlindungan Istilah Teknis (*Protected Terms*) | Kueri: `"pemrograman C++"`, `"TF-IDF"` | Pengguna mencari istilah pemrograman dengan simbol khusus | Tokenizer khusus melindungi karakter `++` dan `-`, mencegah korupsi menjadi "pemrograman C" atau "TF IDF". | Lolos jika istilah teknis terlindungi utuh |
| **TC-16** | Pembaca Dokumen Utuh (*In-App Reader*) | Klik tombol *"Baca Dokumen Lengkap"* pada kartu hasil | Pengguna mengklik tombol pembaca dokumen utuh | Modal `DocumentReaderDialog` terbuka, memuat seluruh halaman fisik dari database SQLite (`GET /api/documents/{id}/pages`), menampilkan total halaman dan teks halaman 1. | Lolos jika seluruh halaman termuat lengkap |
| **TC-17** | Navigasi & Pintasan Halaman Relevan | Klik chip `[Hal. 4]` atau tombol `[Selanjutnya]` | Pengguna berpindah halaman atau mengklik pintasan halaman relevan | Halaman aktif berpindah secara instan ke nomor halaman yang dituju dan menampilkan teks halaman tersebut secara mulus. | Lolos jika teks berganti sesuai nomor halaman terpilih |
| **TC-18** | Penyorotan Kata Kunci pada Reader | Buka dokumen dengan kueri `"algoritma"` | Pengguna membaca halaman dokumen yang memuat kata kueri | Seluruh kemunculan kata "algoritma" di teks halaman tersorot warna kuning cerah secara otomatis. | Lolos jika term kueri tersorot visual |
| **TC-19** | Peringkasan Teks Ekstraktif Dokumen | Klik tombol *"Ringkasan AI"* | Pengguna meminta ringkasan intisari dokumen | Modal `SummaryDialog` memuat ringkasan berbasis TextRank + MMR, menampilkan kalimat inti beserta atribusi nomor halaman fisik asli. | Lolos jika ringkasan muncul berdasar kalimat dokumen asli |
| **TC-20** | Ekstraksi Bukti Kueri Lintas Bahasa | Kueri ID pada paper EN | Pengguna membuka tab *"Relevansi Kueri"* | Sistem menyajikan kalimat-kalimat bukti berbahasa Inggris yang menjawab kueri bahasa Indonesia dengan skor similaritas dan nomor halaman. | Lolos jika bukti kalimat lintas bahasa relevan |
| **TC-21** | Akselerasi Cache Ringkasan Dokumen | Permintaan ringkasan kedua untuk dokumen yang sama | Pengguna membuka kembali ringkasan dokumen | Sistem mengambil ringkasan dari tabel `document_summaries` dengan latensi sub-5ms (**1,7–2,1 ms**) tanpa komputasi ulang TextRank. | Lolos jika latensi < 5 ms dan data identik |

---

### 3.4.2 Desain Evaluasi Model Machine Learning

#### A. Koleksi Kueri Uji Standar (*Benchmark Test Queries*)
Untuk menjamin validitas statistik dan representasi kebutuhan informasi riil, koleksi kueri uji diekspansi dari 10 kueri awal menjadi **33 kueri akademik terstruktur** yang mencakup 6 kategori kebutuhan pencarian (*information need taxonomy*) sesuai standar IREval ([evaluation/queries.csv](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/evaluation/queries.csv)):

| Kategori Kueri | Kode | Jumlah | Contoh Kueri Uji | Karakteristik Kebutuhan Informasi |
| :--- | :---: | :---: | :--- | :--- |
| **Known-item Search** | **A** | 5 | `Q01: analisis perancangan sistem informasi use case diagram`<br>`Q02: work breakdown structure manajemen proyek teknologi informasi` | Pencarian materi/dokumen spesifik dari silabus atau mata kuliah tertentu yang sudah diketahui keberadaannya. |
| **Topical Search** | **B** | 9 | `Q07: sistem operasi proses thread scheduling virtual memory`<br>`Q11: pembelajaran mesin supervised unsupervised neural network` | Pencarian konseptual berbasis topik bahasan umum di lingkungan ilmu komputer dan teknologi informasi. |
| **Methodological Search** | **C** | 5 | `Q15: TF-IDF vector space model cosine similarity temu kembali informasi`<br>`Q16: naive bayes support vector machine klasifikasi teks` | Pencarian metode, algoritma, atau kerangka kerja ilmiah spesifik untuk studi komparasi metodologi. |
| **Learning Material Search** | **D** | 5 | `Q20: materi kuliah sistem operasi proses manajemen`<br>`Q24: buku rancangan pengajaran basis data relasional SQL` | Pencarian spesifik berkas bahan ajar, slide presentasi, atau Buku Rancangan Pengajaran (BRP). |
| **Cross-lingual Search** | **E** | 5 | `Q25: data clustering`<br>`Q26: sentiment analysis`<br>`Q28: machine learning classification` | Pengujian kesenjangan leksikal lintas bahasa antara kueri Bahasa Indonesia dan literatur internasional berbahasa Inggris. |
| **Constrained Search** | **F** | 4 | `Q30: skripsi analisis sentimen media sosial 2023`<br>`Q32: jurnal penelitian deep learning image recognition 2024` | Pencarian dengan pembatas eksplisit berupa segi (*facet*) tipe dokumen (`THESIS`, `RESEARCH`) dan rentang tahun terbit. |
| **Total Benchmark** | | **33** | | **Representasi komprehensif seluruh ragam korpus akademik** |

#### B. Skema Penilaian Relevansi (*Relevance Judgments / Qrels*)
Derajat relevansi dokumen dinilai menggunakan skala bergradasi 4 tingkat (*4-point Graded Relevance Scale*) sesuai panduan formal penilai pada [evaluation/judging_guide.md](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/evaluation/judging_guide.md). Total terkumpul **942 penilaian relevansi (*judgments*)** pada berkas [evaluation/qrels.csv](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/evaluation/qrels.csv):
- **Nilai 3 (Highly Relevant)**: Dokumen atau silabus mata kuliah target membahas konsep kueri secara mendalam sebagai bahasan pokok utama.
- **Nilai 2 (Relevant)**: Dokumen memuat bahasan substantif mengenai konsep terkait, meskipun bukan satu-satunya fokus utama dokumen.
- **Nilai 1 (Partially Relevant)**: Dokumen menyebutkan atau mengutip konsep sebagai konteks pendukung sekunder.
- **Nilai 0 (Non-Relevant)**: Dokumen tidak memiliki kaitan konseptual bermakna dengan kueri (dianggap 0 implisit jika tidak tercatat di qrels).

#### C. Skenario Pengujian dan Metrik Kinerja yang Digunakan
Pengujian dieksekusi secara otomatis melalui skrip benchmark komprehensif [scripts/run_full_benchmark.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/run_full_benchmark.py) menggunakan metrik evaluasi baku temu kembali informasi:
1. **Precision@K (P@5, P@10)**: Proporsi dokumen relevan di antara top-$K$ dokumen yang dikembalikan sistem.
2. **Recall@10 (R@10)**: Proporsi dokumen relevan yang berhasil ditemukan di top-10 dari seluruh dokumen relevan yang ada di korpus ground truth.
3. **Mean Reciprocal Rank (MRR)**: Mengukur kualitas peringkat pertama ditemukannya dokumen relevan ($MRR = \frac{1}{|Q|}\sum_{i=1}^{|Q|}\frac{1}{\text{rank}_i}$). Metrik ini krusial untuk mengevaluasi apakah pengguna langsung menemukan jawaban pada klik pertama.
4. **Normalized Discounted Cumulative Gain (NDCG@10)**: Mengukur kualitas perankingan bergradasi dengan penalti logaritmik posisi peringkat.
5. **Mean Average Precision (MAP)**: Rata-rata presisi terhitung pada setiap titik pemanggilan dokumen relevan di seluruh kueri uji.
6. **Agregasi Dokumen (*Document-Level Aggregation*)**: Menerapkan strategi `max+2nd` pada modul [src/retrieval/aggregation.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/src/retrieval/aggregation.py) untuk menggabungkan skor potongan (*chunks*) ke tingkat dokumen utuh guna mengeliminasi bias dokumen panjang (*long-document dominance*).

#### D. Hasil Eksperimen Komparatif Dual-Baseline & Uji Signifikansi Statistik Formal

Sebagai implementasi pengujian empiris, sistem membandingkan dua arsitektur penelusuran leksikal: **Baseline A (TF-IDF Vector Space Model dengan Cosine Similarity)** melawan **Baseline B (Okapi BM25 dengan normalisasi panjang berkas $k_1=1.5, b=0.75$)**. Hasil benchmark agregat pada 33 kueri uji disajikan pada tabel berikut:

| Metrik Evaluasi | Baseline A: TF-IDF (VSM) | Baseline B: BM25 Okapi | Selisih Absolut ($\Delta$) | Peningkatan Relatif (%) | Wilcoxon Stat ($W$) | Nilai $p$ (dua sisi) | Interpretasi Statistik ($\alpha=0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Mean Average Precision (MAP)** | **0.0832** | **0.1235** | **+0.0403** | **+48.4%** | 75.0 | $p = 0.1592$ | Tidak signifikan secara statistik ($p > 0.05$) |
| **Mean Reciprocal Rank (MRR)** | **0.3990** | **0.4270** | **+0.0280** | **+7.0%** | 29.5 | $p = 0.4558$ | Tidak signifikan secara statistik ($p > 0.05$) |
| **Precision@5 (P@5)** | **0.2667** | **0.2848** | **+0.0181** | **+6.8%** | 7.0 | $p = 0.4631$ | Tidak signifikan secara statistik ($p > 0.05$) |
| **Precision@10 (P@10)** | **0.2182** | **0.2364** | **+0.0182** | **+8.3%** | 11.0 | $p = 0.3252$ | Tidak signifikan secara statistik ($p > 0.05$) |
| **Recall@10 (R@10)** | **0.1186** | **0.1506** | **+0.0320** | **+27.0%** | 33.0 | $p = 0.0764$ | Indikasi tren keunggulan ($p < 0.10$) |
| **NDCG@10** | **0.2490** | **0.2992** | **+0.0502** | **+20.2%** | 38.0 | $p = 0.0684$ | Indikasi tren keunggulan ($p < 0.10$) |

> **Analisis Inferensial dan Uji Signifikansi Statistik (Audit §1 & §3):**
> 1. **Uji Non-Parametrik Wilcoxon Signed-Rank Test:** Berdasarkan pengujian berpasangan pada 33 kueri uji ([scripts/statistical_significance.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/statistical_significance.py)), peningkatan metrik utama **NDCG@10 (+20.2%)** menghasilkan nilai statistik $W = 38.0$ dengan $p = 0.0684$. Selang kepercayaan bootstrap 95% untuk selisih NDCG@10 adalah $[+0.0057, +0.1036]$ dengan ukuran efek rank-biserial $r = -0.5033$ (*large effect size*).
> 2. **Koreksi Terhadap Klaim "Signifikan":** Karena nilai $p = 0.0684$ berada sedikit di atas ambang batas konvensional $\alpha = 0.05$, hipotesis nol belum dapat ditolak secara definitif pada tingkat kepercayaan 95%. Oleh karena itu, klaim laporan diperbaiki secara ilmiah: BM25 menunjukkan **keunggulan empiris yang konsisten dengan ukuran efek besar (*large effect size*)**, namun pembuktian signifikansi statistik formal membutuhkan perluasan jumlah kueri uji (misal $N \ge 50$) pada evaluasi lanjutan.
> 3. **Distribusi Kemenangan per Kueri:** Dari 33 kueri evaluasi, BM25 mengungguli TF-IDF pada **11 kueri**, TF-IDF mengungguli BM25 pada **6 kueri**, dan kedua model mencatat hasil imbang (*ties*) pada **16 kueri**.

---

#### E. Analisis Posisi Peringkat Dokumen Relevan Pertama (Distribusi Rank MRR)

Untuk memperbaiki kesalahan interpretasi matematis mengenai nilai MRR (Audit §4), sistem menganalisis distribusi posisi konkret dokumen relevan pertama yang ditemukan oleh BM25:

| Kategori Peringkat Dokumen Pertama | Jumlah Kueri | Persentase (%) | Implikasi Pengalaman Pengguna (*User Experience*) |
| :--- | :---: | :---: | :--- |
| **Peringkat 1 (*Rank 1*)** | **12 / 33** | **36.4%** | Pengguna langsung mendapatkan dokumen relevan pada hasil teratas. |
| **Peringkat 2 (*Rank 2*)** | **2 / 33** | **6.1%** | Dokumen relevan ditemukan pada kartu kedua. |
| **Peringkat 3 (*Rank 3*)** | **0 / 33** | **0.0%** | Tidak ada kueri dengan dokumen pertama di peringkat 3. |
| **Peringkat > 3 (*Rank > 3*)** | **7 / 33** | **21.2%** | Dokumen relevan ditemukan pada peringkat 4 hingga 20. |
| **Tidak Ditemukan (*Not Found in Top-20*)** | **12 / 33** | **36.4%** | Kueri mengalami kegagalan temu kembali (*miss*) pada batas pemanggilan $K=20$. |

> **Catatan Metodologis:** Nilai $MRR = 0.4270$ merupakan rata-rata harmonik reciprocal rank ($E[1/R]$), sehingga secara matematis $E[1/R] \ne 1/E[R]$ (ketidaksamaan Jensen). Menafsirkan $1 / 0.4270 = 2.34$ sebagai "peringkat rata-rata ke-2.34" adalah keliru secara statistik. Data distribusi empiris di atas membuktikan bahwa pada **42.5% kueri**, pengguna menemukan dokumen relevan pada posisi 1 atau 2, sementara pada 36.4% kueri sistem leksikal belum berhasil menemukan dokumen relevan di top-20.

---

#### F. Evaluasi Granular: Performa per Kategori Kueri dan per Korpus (Audit §9 & §10)

Hasil evaluasi granular yang dianalisis menggunakan [scripts/run_full_benchmark.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/run_full_benchmark.py) mengungkap performa sistem pada setiap dimensi:

##### 1. Performa BM25 Berdasarkan Kategori Kebutuhan Informasi (*Taxonomy Breakdown*)

| Kategori Kueri | Kode | Jumlah ($N$) | Precision@10 | NDCG@10 | MAP | Karakteristik Performa |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Known-item Search** | **A** | 5 | **0.4400** | **0.4753** | **0.1319** | Performa tertinggi; istilah spesifik silabus cocok tepat dengan judul materi. |
| **Topical Search** | **B** | 9 | **0.3111** | **0.3826** | **0.1520** | Sangat baik pada konsep umum ilmu komputer (OS, Jarkom, Algoritma). |
| **Learning Material** | **D** | 5 | **0.3200** | **0.3011** | **0.0521** | Presisi top-10 baik pada slide kuliah, namun recall menyeluruh terbatas. |
| **Methodological Search** | **C** | 5 | **0.2000** | **0.2577** | **0.1236** | Moderat; terdapat kesenjangan istilah antara varian algoritma. |
| **Cross-lingual Search** | **E** | 5 | **0.0400** | **0.2522** | **0.2341** | Presisi rendah pada top-10; dokumen yang cocok relevan di peringkat sangat atas. |
| **Constrained Search** | **F** | 4 | **0.0000** | **0.0000** | **0.0000** | Terendah; kueri dengan constraint tahun/tipe gagal diproses tanpa filter terstruktur. |

##### 2. Performa BM25 Berdasarkan Pilar Korpus Akademik

| Pilar Korpus | Jumlah Kueri Terkait ($N$) | Precision@10 | NDCG@10 | MAP | Analisis Kinerja Korpus |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **MATERIAL (Bahan Kuliah)** | 21 | **0.3190** | **0.3613** | **0.1171** | Terkuat; korpus slide dan BRP memiliki kepadatan kata kunci tinggi. |
| **RESEARCH (Artikel Jurnal)** | 10 | **0.1100** | **0.2288** | **0.1618** | Moderat; artikel riset panjang memiliki dispersi istilah yang luas. |
| **THESIS (Skripsi/Tesis)** | 2 | **0.0000** | **0.0000** | **0.0000** | Lemah; sampel kueri skripsi pada benchmark memiliki pembatas tahun yang ketat. |

> **Audit Kueri Cross-Lingual (Audit §11):** Seluruh 5 kueri kategori E (`Q25` s.d. `Q29`) ditulis dalam Bahasa Inggris (misal `"data clustering"`, `"sentiment analysis"`). Analisis dokumen target membuktikan bahwa dokumen yang dipanggil juga merupakan paper riset berbahasa Inggris dari arXiv dan CORE. Secara operasional, pencarian ini merupakan **retrieval monolingual Bahasa Inggris**, bukan temu kembali lintas bahasa sejati (*cross-lingual retrieval*). Klaim cross-lingual tidak dipertahankan untuk menghindari penyesatan metodologi.

---

#### G. Studi Ablasi Komponen (*Ablation Ladder Study*, Audit §12 & §26)

Untuk mengidentifikasi komponen mana yang memberikan kontribusi nyata terhadap performa sistem, dijalankan eksperimen tangga ablasi (*Ablation Ladder*) E0 hingga E5 pada kondisi lingkungan identik ([scripts/run_ablation.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/run_ablation.py)):

| ID Eksperimen | Konfigurasi Model | MAP | NDCG@10 | Precision@10 | MRR | Latensi Evaluasi | Kontribusi Komponen ($\Delta$ vs E3 NDCG@10) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **E0** | TF-IDF Baseline (VSM murni) | 0.0832 | 0.2490 | 0.2182 | 0.3990 | 38.6 s | Baseline pembanding (-0.0502) |
| **E3** | **BM25 + Chunk + Aggregation (`max+2nd`)** | **0.1235** | **0.2992** | **0.2364** | **0.4270** | **2.6 s** | **Konfigurasi Terbaik Saat Ini (Baseline B)** |
| **E4** | BM25 + Title Boost (pembobotan judul 1.5x) | 0.1213 | 0.2945 | 0.2273 | 0.4558 | 2.7 s | MRR naik (+0.0288), namun NDCG@10 turun (-0.0047) |
| **E5** | BM25 + Naive Query Expansion (kamus 64 sinonim) | 0.0908 | 0.2406 | 0.2152 | 0.3230 | 2.8 s | Performa merosot drastis akibat *Query Drift* (-0.0586) |

> **Kesimpulan Ablasi:**
> 1. Peningkatan terbesar berasal dari pergantian algoritma ke **Okapi BM25 dengan normalisasi panjang dokumen dan agregasi potongan** (E0 $\to$ E3, $\Delta\text{NDCG@10} = +0.0502$).
> 2. Penerapan Title Boost sederhana (E4) berhasil meningkatkan MRR dari 0.4270 ke 0.4558 karena dokumen dengan judul yang cocok langsung melonjak ke posisi puncak, namun menurunkan presisi keseluruhan karena judul seringkali terlalu umum.
> 3. Naive Query Expansion (E5) terbukti kontraproduktif tanpa mekanisme pembobotan term.

---

#### H. Penyetelan Hyperparameter Okapi BM25 (*Hyperparameter Tuning*, Audit §13)

Untuk mencegah kebocoran set pengujian (*test-set leakage*), 33 kueri dibagi secara disiplin menjadi:
- **Development Set (Dev Set):** 22 kueri (`Q01` s.d. `Q22`) khusus untuk *grid search* parameter.
- **Test Set (Evaluasi Akhir):** 11 kueri (`Q23` s.d. `Q33`) yang hanya dievaluasi satu kali pada akhir eksperimen.

Eksperimen *grid search* ([scripts/tune_bm25_params.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/tune_bm25_params.py)) menguji 20 kombinasi parameter ($k_1 \in \{0.5, 1.0, 1.5, 2.0\}$ dan $b \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$) pada Dev Set dengan target optimasi NDCG@10:

| Konfigurasi Parameter | NDCG@10 (Dev Set) | MAP (Dev Set) | Status Evaluasi |
| :--- | :---: | :---: | :--- |
| $k_1 = 0.50, b = 0.00$ | 0.3040 | 0.1073 | Tanpa normalisasi panjang dokumen |
| $k_1 = 1.00, b = 0.50$ | 0.3422 | 0.1177 | Parameter moderat |
| $k_1 = 1.50, b = 0.75$ | **0.3388** | **0.1125** | **Konfigurasi Default Robertson** |
| $k_1 = 2.00, b = 0.75$ | **0.3485** | **0.1231** | **Parameter Terbaik pada Dev Set** |

**Evaluasi Validasi Silang pada Test Set (Q23–Q33):**
Ketika konfigurasi terbaik dev set ($k_1=2.0, b=0.75$) diuji pada Test Set independen melawan konfigurasi default ($k_1=1.5, b=0.75$):
- **NDCG@10 pada Test Set:** Konfigurasi Terbaik = **0.2164** vs Default = **0.2164** ($\Delta = 0.0000$).
- **P@10 pada Test Set:** Konfigurasi Terbaik = **0.1182** vs Default = **0.1182** ($\Delta = 0.0000$).
- **MAP pada Test Set:** Konfigurasi Terbaik = **0.1257** vs Default = **0.1258** ($\Delta = -0.0001$).

> **Temuan Tuning:** Peningkatan performa pada Dev Set tidak tertransfer ke Test Set, membuktikan bahwa parameter default Robertson ($k_1=1.5, b=0.75$) bersifat sangat tangguh (*robust*) dan tidak mengalami *overfitting*. Penggunaan parameter default terbukti merupakan pilihan desain yang tepat dan dapat dipertanggungjawabkan secara ilmiah.

---

#### I. Eksperimen Query Expansion dan Analisis Fenomena *Query Drift* (Audit §24)

Untuk mengatasi permasalahan *vocabulary mismatch*, modul perluasan kueri dwibahasa diimplementasikan ([src/retrieval/query_expansion.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/src/retrieval/query_expansion.py)) dengan kamus 64 entri akademik dwibahasa ([data/synonym_dict_bilingual.json](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/data/synonym_dict_bilingual.json)). Modul memperluas 21 dari 33 kueri evaluasi.

Hasil evaluasi komparatif BM25 vs BM25 + Query Expansion:

| Metrik Evaluasi | BM25 Murni | BM25 + Query Expansion | Selisih ($\Delta$) | Arah Perubahan |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Average Precision (MAP)** | **0.1235** | **0.0911** | **-0.0324** | Menurun |
| **Mean Reciprocal Rank (MRR)** | **0.4270** | **0.3253** | **-0.1017** | Menurun |
| **Precision@5 (P@5)** | **0.2848** | **0.2364** | **-0.0484** | Menurun |
| **Precision@10 (P@10)** | **0.2364** | **0.2152** | **-0.0212** | Menurun |
| **NDCG@10** | **0.2992** | **0.2415** | **-0.0577** | Menurun |
| **Recall@10** | **0.1506** | **0.0970** | **-0.0536** | Menurun |

> **Analisis Kegagalan — Fenomena Query Drift:**
> Penurunan performa pada seluruh metrik merupakan fenomena klasik temu kembali informasi yang dikenal sebagai **Query Drift**. Ketika kueri seperti `"analisis sentimen"` diperluas secara leksikal menjadi `"analisis sentimen sentiment analysis opinion mining"`, kata-kata tambahan yang bersifat umum mendistorsi distribusi frekuensi term (TF-IDF/BM25). Dokumen yang kaya akan kata umum `"analysis"` atau `"opinion"` terangkat ke peringkat atas, menggeser dokumen spesifik topik. Eksperimen ini membuktikan bahwa penanganan *vocabulary mismatch* pada korpus akademik **tidak dapat diselesaikan melalui perluasan sinonim kamus leksikal tanpa pembobotan istilah**, melainkan memerlukan **Dense Semantic Retrieval** (representasi vektor berbasis Transformer) yang direncanakan untuk Tahap II.

---

#### J. Analisis Galat Komprehensif (*Failure Analysis*) & Batasan Sistem (Audit §2)

Secara transparan, skor absolut sistem pada Tahap I (P@10 = 0.2364, MAP = 0.1235) berada di bawah ambang batas kesempurnaan mesin pencari komersial. Hal ini disebabkan oleh tiga faktor arsitektural mendasar:
1. **Asumsi Konservatif Cranfield (Penalti Unjudged Documents):** Dari 4.498 dokumen, ground truth qrels memuat 942 penilaian spesifik. Ribuan dokumen berkualitas tinggi lainnya yang terpanggil oleh sistem leksikal namun tidak tercatat di qrels secara otomatis diberi nilai 0, menekan nilai presisi dan MAP secara artifisial (*conservative lower bound*).
2. **Heterogenitas Ekstrem Format Dokumen:** Korpus memadukan slide kuliah padat kata kunci (2–10 halaman), paper riset dwibahasa (5–15 halaman), dan naskah skripsi komprehensif (100–300 halaman). Meskipun agregasi potongan (`max+2nd`) menekan dominasi dokumen tebal, variasi kepadatan informasi tetap menjadi tantangan perankingan leksikal murni.
3. **Ketiadaan Pemahaman Semantik Leksikal:** Model VSM dan BM25 murni bergantung pada kecocokan kata persis (*exact term matching*). Kueri yang menggunakan frasa sinonim yang tidak tertulis sama persis di dokumen gagal dipanggil secara akurat.

---

#### K. Hasil Pengujian Latensi Sistem (*Latency Benchmark*)

Pengujian latensi dilakukan secara terstandarisasi *apple-to-apple* menggunakan skrip [scripts/benchmark_latency.py](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/benchmark_latency.py) pada seluruh 56.881 potongan korpus pada lingkungan prototipe lokal:

| Mesin Penelusuran (*Retriever*) | Waktu Pemuatan Awal (*Cold Start*) | Latensi Median (P50) | Persentil 95 (P95) | Persentil 99 (P99) | Rata-rata Latensi (*Mean*) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **TF-IDF (Baseline A)** | 4.321,52 ms | 751,84 ms | 1.563,19 ms | 1.866,06 ms | 826,13 ms |
| **BM25 Okapi (Baseline B)** | 9.079,52 ms | **83,71 ms** | **101,89 ms** | **119,92 ms** | **80,04 ms** |

> **Analisis Latensi dan Kelayakan Operasional Prototipe Lokal:**
> - BM25 Okapi menunjukkan latensi pencarian **sekitar 9x lebih cepat** daripada TF-IDF Cosine Similarity pada kondisi eksekusi normal (**83,71 ms vs 751,84 ms**). Kecepatan ini dicapai karena struktur indeks terbalik (*inverted index*) BM25 hanya mengakumulasi skor untuk dokumen kandidat yang memuat term kueri, menghindari perkalian matriks penuh.
> - Nilai P95 BM25 sebesar **101,89 ms** membuktikan kelayakan operasional prototipe lokal yang sangat responsif, berada jauh di bawah batas toleransi interaksi manusia (250 ms).

---

#### L. Evaluasi Tolerant Retrieval dan Ketahanan Kueri Typo/Variasi (Revisi Tahap II)

Sebagai implementasi revisi arsitektur Tahap II berdasarkan spesifikasi [README_Tolerant_Retrieval.md](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/README_Tolerant_Retrieval.md), sistem dievaluasi terhadap ketahanan kueri yang mengandung kesalahan pengetikan (*typos*), variasi ejaan akademik, dan singkatan istilah teknis. 

Evaluasi komparatif dijalankan dengan menguji perilaku sistem pada tiga mode operasional: **Mode Nonaktif (*Strict Lexical Exact*)**, **Mode Otomatis (*Adaptive Exact-First + Fallback*)**, dan **Mode Selalu Aktif (*Force Normalization*)**:

| Kategori Pengujian Kueri | Contoh Kueri Uji | Hasil Mode Nonaktif (`off`) | Hasil Mode Otomatis (`auto`) | Hasil Mode Selalu Aktif (`always`) | Aksi Tolerant Layer | Skor Keyakinan (*Confidence*) |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **Typo Kata Kerja / Konjungsi** | `"menggunkan BERT"` | 0 Dokumen (*Zero Hits*) | **15 Dokumen** (Dipulihkan) | **15 Dokumen** (Dipulihkan) | `menggunkan` $\rightarrow$ `menggunakan` | 0.9746 (97%) |
| **Variasi Ejaan Akademik** | `"sentimen analisa"` | 3 Dokumen (Minim) | **10 Dokumen** (Dipulihkan) | **10 Dokumen** (Dipulihkan) | `analisa` $\rightarrow$ `analisis` | 0.9800 (98%) |
| **Ekspansi Singkatan Akademik** | `"NLP"` | 2 Dokumen (Slide Singkat) | **10 Dokumen** (Ekspansi) | **10 Dokumen** (Ekspansi) | `NLP` $\rightarrow$ `Natural Language Processing` | 0.9900 (99%) |
| **Kueri Normal Tanpa Typo** | `"algoritma pemrograman"` | **20 Dokumen** (Eksak) | **20 Dokumen** (Eksak Memadai) | **20 Dokumen** (Baku) | *Fallback Tidak Dipicu* (0% False Positive) | 1.0000 (100%) |
| **Istilah Teknis Terlindungi** | `"pemrograman C++"`, `"TF-IDF"` | **10 Dokumen** (Eksak) | **10 Dokumen** (Terlindungi) | **10 Dokumen** (Terlindungi) | Simbol `++` dan `-` dilindungi dari korupsi | 1.0000 (100%) |

> **Temuan & Analisis Kinerja Tolerant Retrieval:**
> 1. **Eliminasi Fenomena Zero Hits pada Typo**: Pada kueri yang mengandung typo kritis (`"menggunkan BERT"`), model leksikal BM25 murni gagal menemukan dokumen karena ketiadaan token exact match di indeks inverted. Melalui *Fast Damerau-Levenshtein distance* ($d=1$), sistem memulihkan kueri menjadi `"menggunakan BERT"`, menghasilkan lompatan pemanggilan dari **0 menjadi 15 dokumen relevan** berpresisi tinggi.
> 2. **Keberhasilan Prinsip Exact-First Guard**: Pengujian pada kueri baku (`"algoritma pemrograman"`) membuktikan bahwa mekanisme *Exact-First Fallback Controller* berhasil menjaga presisi sistem. Karena hasil eksak awal memadai ($\ge 3$ dokumen dengan skor tinggi), transformasi fuzzy tidak dipaksakan, sehingga mengeliminasi risiko *false positive drift* yang kerap terjadi pada mesin fuzzy komersial.
> 3. **Latensi Tambahan Minimal (*Sub-Millisecond Overhead*)**: Waktu komputasi modul tolerant retrieval tercatat rata-rata hanya **1.8 ms** per kueri berkat pengindeksan kosa kata korpus berdasarkan panjang karakter dan bigram. Total latensi end-to-end tetap berada pada **~85 ms**, jauh di bawah standar respons interaktif manusia (250 ms).

---

# IV. ANALISIS, DESAIN, DAN IMPLEMENTASI TEXT SUMMARIZATION (EKSTRAKTIF & QUERY-FOCUSED)

### 4.1 Latar Belakang & Urgensi Text Summarization pada Dokumen Akademik
Dalam alur penemuan informasi ilmiah (*academic discovery workflow*), pengguna tidak hanya membutuhkan daftar dokumen yang relevan terhadap kueri pencarian, melainkan juga memerlukan pemahaman instan terhadap esensi isi dokumen tanpa harus mengunduh dan membaca puluhan hingga ratusan halaman PDF. Pada repositori dokumen akademik, pengguna dihadapkan pada tiga persoalan mendasar:
1. **Beban Kognitif Pembacaan (*Cognitive Overload*)**: Mahasiswa atau peneliti membutuhkan waktu rata-rata 10–25 menit untuk menyaring apakah suatu artikel jurnal (10–30 halaman) atau skripsi (50–150 halaman) relevan dengan topik riset yang sedang diteliti.
2. **Keterbatasan Abstrak Bawaan**: Banyak bahan kuliah (*lecture materials*) dan dokumen teknis tidak menyertakan bagian abstrak formal. Selain itu, abstrak konvensional kerap terlalu padat dan tidak menyoroti jawaban spesifik terhadap kueri unik pengguna.
3. **Risiko Halusinasi Model Generatif**: Model bahasa besar (*Large Language Models / LLM*) modern yang melakukan peringkasan abstraktif rentan terhadap distorsi fakta ilmiah (*hallucination*), perubahan terminologi matematis, dan ketidakmampuan membuktikan sitasi nomor halaman fisik asli.

Untuk menyelesaikan tantangan tersebut, sistem **Academic IR** mengimplementasikan modul **Text Summarization** berbasis pendekatan ekstraktif (*Extractive Summarization*) dan pencocokan semantik multibahasa (*Query-Focused Cross-Lingual Evidence Extraction*). Pendekatan ini menjamin **100% fakta bersumber dari kalimat dokumen asli (*zero hallucination*)**, menyertakan bukti nomor halaman fisik dokumen (*page-level traceability*), serta beroperasi secara deterministik dan cepat pada lingkungan CPU (*sub-second latency*).

---

### 4.2 Strategi Menangani Heterogenitas Bahasa Korpus
Korpus akademik pada sistem ini memiliki keanekaragaman bahasa yang nyata:
1. **Bahan Kuliah (*Course Materials*)**: Mayoritas berupa slide perkuliahan dwibahasa (*code-switching*) yang mencampur narasi Bahasa Indonesia dengan istilah teknis Bahasa Inggris (750 dokumen ID, 322 dokumen EN).
2. **Skripsi / Tesis (*Theses*)**: Ditulis dalam Bahasa Indonesia baku namun memuat kutipan, definisi formal, dan istilah asing (91 dokumen ID, 28 dokumen EN).
3. **Artikel Riset (*Research Papers*)**: Seluruhnya ditulis dalam Bahasa Inggris akademik internasional (168 dokumen EN).

**Prinsip Desain Utama:** Sistem **TIDAK melakukan penerjemahan paksa ke satu bahasa (*No Forced Machine Translation*)**. Penerjemahan otomatis seluruh korpus PDF ke satu bahasa berisiko merusak terminologi ilmiah khusus (`TF-IDF`, `BERT`, `C++`, `k-NN`), menimbulkan galat sintaksis, serta membebani komputasi secara ekstrem. Sebagai gantinya, arsitektur summarization mengadopsi prinsip:
- **Skenario A (Document Summary / Intisari Dokumen)**: Sistem mendeteksi bahasa teks dokumen, menjalankan pemrosesan awal (*preprocessing*) yang sadar bahasa (*language-aware*), dan menghasilkan ringkasan esensial dalam **bahasa asli dokumen tersebut** menggunakan algoritma **TextRank + MMR**.
- **Skenario B (Query-Focused Cross-Lingual / Relevansi Kueri)**: Jika kueri pengguna (misalnya Bahasa Indonesia: *"evaluasi performa temu kembali informasi lintas bahasa"*) mencari bukti pada paper berbahasa Inggris, sistem menggunakan representasi semantik multibahasa (*multilingual sentence representation*) untuk menjembatani kesenjangan leksikal dan mengekstrak kalimat-kalimat berbahasa Inggris yang paling menjawab kueri tersebut.

---

### 4.3 Landasan Algoritma & Formulasi Matematis

```
                  Dokumen PDF (Teks Halaman Asli)
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       Skenario A (Dokumen)           Skenario B (Kueri)
               │                               │
        Language Detection              Query Processing
        (id / en / mixed)              (Bilingual Embedding)
               │                               │
        Safe Sentence Split             Semantic Similarity
        (Proteksi Singkatan)           cos(q, s_i)
               │                               │
        TF-IDF Sentence Matrix                 │
               │                               │
        Cosine Graph & TextRank                │
        (PageRank Centrality)                  │
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
                   Maximal Marginal Relevance
                   (MMR Anti-Redundansi, λ=0.70)
                               │
                               ▼
                  Rekonstruksi Kronologis
                  + Atribusi Nomor Halaman
                               │
                               ▼
                  Cache SQLite & Respon API
```

#### 4.3.1 Deteksi Bahasa Adaptif (*Confidence-based Language Detection*)
Modul `src/summarization/lang_detect.py` mengevaluasi sampel teks pembuka dokumen (judul, abstrak, dan 3 halaman pertama hingga 6.000 karakter). Dengan menetapkan ambang batas probabilitas $P \ge 0.85$, sistem mengklasifikasikan dokumen ke dalam:
- `id` (Bahasa Indonesia): jika probabilitas bahasa Indonesia dominan.
- `en` (Bahasa Inggris): jika probabilitas bahasa Inggris dominan.
- `mixed` (Dwibahasa/Campuran): jika kedua bahasa terdeteksi dengan probabilitas berimbang ($0.20 \le P(id), P(en) \le 0.80$).

#### 4.3.2 Tokenisasi Kalimat Aman (*Safe Sentence Tokenization*)
Pemecahan kalimat standar berbasis tanda titik (`.`) sering merusak struktur kalimat ilmiah akibat singkatan akademis. Modul `src/summarization/preprocessing.py` menerapkan *regex masking*:
1. **Proteksi Singkatan Ilmiah**: Melindungi singkatan bahasa Inggris (`et al.`, `e.g.`, `i.e.`, `vs.`, `Fig.`, `Tab.`, `Vol.`, `No.`, `pp.`, `Prof.`, `Dr.`) dan singkatan bahasa Indonesia (`dkk.`, `hlm.`, `hal.`, `jil.`, `lamp.`, `sdr.`, `yth.`, `drs.`, `ir.`) serta angka desimal (`3.14`, `94.5%`).
2. **Pembersihan Sitasi & Derau**: Menghapus sitasi kurung siku (`[1]`, `[1-3]`), sitasi nama tahun (`(Smith et al., 2020)`), dan derau batas header/footer.
3. **Penyaringan Kualitas Kalimat**: Mengeliminasi baris rumus matematika murni, kode program, dan fragmen pendek ($< 6$ kata atau $< 25$ karakter) atau terlalu panjang ($> 95$ kata).
4. **Pelacakan Asal Halaman**: Setiap kandidat kalimat $S_i$ mempertahankan pasangan metadata `(text, page_number, order_idx)` langsung dari tabel basis data `pages`.

#### 4.3.3 Matriks TF-IDF dan Graf Sentralitas TextRank
Setiap kandidat kalimat direpresentasikan sebagai vektor frekuensi kata berbobot:
$$\vec{S_i} = \text{TF-IDF}(S_i)$$
dengan daftar stopword yang disesuaikan secara dinamis: stopword Sastrawi untuk `id`, NLTK untuk `en`, dan gabungan keduanya (*union*) untuk `mixed`.

Matriks keterkaitan semantik antar-kalimat (graf ketetanggaan $W$) dibentuk menggunakan *Cosine Similarity*:
$$W_{ij} = \begin{cases} \frac{\vec{S_i} \cdot \vec{S_j}}{\|\vec{S_i}\|_2 \|\vec{S_j}\|_2}, & \text{jika } i \ne j \text{ dan } W_{ij} \ge 0.05 \\ 0, & \text{jika } i = j \text{ atau } W_{ij} < 0.05 \end{cases}$$
Skor sentralitas TextRank diselesaikan melalui metode *Power Iteration PageRank* ($\alpha=0.85$, konvergen pada toleransi $\epsilon = 10^{-5}$):
$$\vec{v}^{(t+1)} = \frac{1 - d}{N}\mathbf{1} + d \cdot P^T \vec{v}^{(t)}$$
di mana $P$ adalah matriks probabilitas transisi baris ternormalisasi. Kalimat dengan skor tertinggi menunjukkan posisi sentral yang paling merangkum gagasan utama dokumen.

#### 4.3.4 Eliminasi Redundansi dengan Maximal Marginal Relevance (MMR)
TextRank murni kerap memilih kalimat-kalimat yang mengulang informasi yang sama (memiliki kata kunci topik dominan serupa). Modul `src/summarization/mmr.py` menerapkan seleksi serakah (*greedy selection*) berbasis MMR:
$$S_{next} = \arg\max_{S_i \in C \setminus S} \left[ \lambda \cdot \text{Score}(S_i) - (1 - \lambda) \cdot \max_{S_j \in S} \text{Sim}(S_i, S_j) \right]$$
Dengan menyetel $\lambda = 0.70$, sistem memprioritaskan kalimat yang penting namun memiliki kemiripan kosinus rendah terhadap kalimat yang sudah dipilih sebelumnya.

#### 4.3.5 Rekonstruksi Alur Kronologis (*Chronological Reordering*)
Setelah Top-$K$ kalimat (default: 4 kalimat) terpilih oleh MMR, kalimat-kalimat tersebut tidak disajikan berdasarkan urutan skor, melainkan diurutkan kembali berdasarkan posisi kemunculannya di dokumen fisik:
$$\text{Sort By: } (\text{page\_number}, \text{order\_idx})$$
Hal ini menjamin ringkasan dapat dibaca secara kohesif mengalir dari pengenalan masalah, metodologi, temuan, hingga kesimpulan.

#### 4.3.6 Ekstraksi Bukti Kueri Lintas Bahasa (*Query-Focused Cross-Lingual*)
Untuk Skenario B, modul `src/summarization/embeddings.py` memproyeksikan kueri pengguna dan seluruh kalimat kandidat ke dalam representasi semantik multibahasa bersama. Skor relevansi kalimat terhadap kueri dihitung melalui:
$$\text{Relevance}(Q, S_i) = \cos(\vec{Q}, \vec{S_i})$$
Kalimat-kalimat dengan relevansi tertinggi diseleksi menggunakan MMR berbasis kueri untuk menghasilkan cuplikan bukti ilmiah yang padat tanpa duplikasi konteks.

---

### 4.4 Arsitektur Modul Backend & Skema Basis Data Caching

#### Struktur Berkas Modular (`academic-ir/src/summarization/`)
```text
academic-ir/src/summarization/
├── __init__.py          # Ekspor publik: Schemas, Service, Factory
├── schemas.py           # Model Pydantic: SentenceItem, SummaryResponse, QuerySummaryRequest
├── lang_detect.py       # Deteksi bahasa robust (id, en, mixed)
├── preprocessing.py     # Tokenisasi aman, proteksi singkatan, pembersihan sitasi
├── textrank.py          # Solusi graf TextRank dan sentralitas PageRank
├── mmr.py               # Filter redundansi MMR dan pengurutan kronologis
├── embeddings.py        # Representasi semantik multibahasa kueri ↔ kalimat
├── storage.py           # Adapter persistensi cache SQLite
└── service.py           # Orkestrator alur kerja (facade pattern)
```

#### Skema Tabel SQLite Caching (`document_summaries`)
Untuk mencegah pemborosan komputasi graf berulang pada dokumen yang sama, dibuat tabel khusus `document_summaries` pada `academic_ir.db`:
```sql
CREATE TABLE IF NOT EXISTS document_summaries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id         TEXT NOT NULL,
    summary_type        TEXT NOT NULL,        -- 'document' atau 'query_focused'
    query_text          TEXT,                 -- NULL jika 'document'
    summary_text        TEXT NOT NULL,
    language            TEXT NOT NULL,        -- 'id', 'en', 'mixed'
    algorithm           TEXT NOT NULL,        -- 'textrank_mmr' atau 'multilingual_embedding_mmr'
    key_sentences_json  TEXT NOT NULL,        -- JSON array: [{text, page, score, order_idx}]
    source_pages_json   TEXT NOT NULL,        -- JSON array: [1, 3, 5]
    sentence_count      INTEGER NOT NULL,
    processing_time_ms  REAL NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE(document_id, summary_type, query_text)
);
CREATE INDEX IF NOT EXISTS idx_summaries_doc ON document_summaries(document_id, summary_type);
```

#### Spesifikasi Antarmuka REST API (`app/api.py`)
1. **`GET /api/documents/{document_id}/summary`**
   - Mengembalikan ringkasan esensial dokumen dalam bahasa asli dokumen.
   - Parameter: `max_sentences` (default: 4), `lambda_param` (default: 0.70), `force_refresh` (boolean).
   - Mengambil hasil dari cache SQLite jika tersedia (< 3 ms), atau mengomputasi *on-demand*.
2. **`POST /api/documents/{document_id}/query-summary`**
   - Mengembalikan kalimat bukti yang menjawab kueri pencarian tertentu.
   - Request Body: `{"query": "...", "max_sentences": 4, "lambda_param": 0.70}`.

---

### 4.5 Desain Antarmuka Pengguna Interaktif (Next.js 15)

Modul peringkasan diintegrasikan secara elegan pada antarmuka web modern:
1. **Tombol "Ringkasan" pada Result Card (`result-card.tsx`)**:
   - Ditempatkan berdampingan dengan tombol *"Buka Dokumen"* pada setiap kartu hasil pencarian.
   - Dilengkapi ikon berkilau (*Sparkles*) dan warna aksen primer yang mengundang interaksi.
2. **Modal Dialog Interaktif (`summary-dialog.tsx`)**:
   - **Tab 1: Intisari Dokumen**: Menampilkan 4 kalimat esensial dokumen dari TextRank + MMR, badge bahasa dokumen (misalnya: `🌐 Bahasa Indonesia` atau `🌐 Bahasa Inggris`), badge algoritma, dan alur ringkasan utuh (*narrative box*).
   - **Tab 2: Relevansi Kueri**: Menampilkan kalimat-kalimat bukti yang secara spesifik menjawab kata kunci kueri aktif yang sedang dicari pengguna, lengkap dengan persentase kemiripan semantik.
   - **Lencana Halaman Fisik (*Page Badge*)**: Setiap butir kalimat ringkasan dilengkapi lencana rujukan (misalnya: `Halaman 2`, `Halaman 8`), memungkinkan pengguna memverifikasi langsung letak informasi pada berkas PDF asli.
   - **Interaktivitas Cepat**: Dilengkapi tombol **Salin** (*Copy to Clipboard*) dengan indikator visual *"Tersalin"* berwarna hijau, tombol **Segarkan** (*Force Recompute*), serta lencana status cache instan (`⚡ Cache (1.8 ms)`).

---

### 4.6 Hasil Pengujian Empiris dan Tolok Ukur Kinerja (*Evaluation Benchmark*)

Evaluasi empiris dijalankan menggunakan skrip benchmark resmi [`scripts/evaluate_summarization.py`](file:///c:/Users/Monk/Downloads/TemuKembaliInformasi/academic-ir/scripts/evaluate_summarization.py) terhadap korpus akademik multi-disiplin:

#### 1. Uji Peringkasan Intisari Dokumen (Cold Run vs. Warm Cache Hit)
| ID Dokumen | Pilar & Bahasa Korpus | Judul Dokumen | Kalimat Terpilih | Halaman Rujukan Sumber | Latensi Cold (ms) | Latensi Cache (ms) | Skor Redundansi (Jaccard) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **MAT-000007** | Material (EN) | *Schwalbe 8th Ed - Chapter 01* (Buku 36 Halaman) | 4 | `[Hal. 7, 8, 9]` | 477,1 ms | **1,80 ms** | 15,7% |
| **RES-000001** | Riset (EN) | *Toward a Unified Retrieval Outcome Analysis...* | 4 | `[Hal. 1, 3, 5, 6]` | 29,5 ms | **1,72 ms** | 13,4% |
| **THS-000006** | Skripsi (ID) | *Economics Of Regulatory Compliance In Fisheries...* | 4 | `[Hal. 1, 2]` | 18,7 ms | **2,07 ms** | 6,5% |
| **MAT-000001** | Material (ID) | *BRP Manajemen Proyek TI* | 4 | `[Hal. 2, 5, 16]` | 20,6 ms | **2,13 ms** | 3,5% |

#### 2. Uji Ekstraksi Bukti Kueri Lintas Bahasa (*Cross-Lingual Evidence Extraction*)
- **Pengujian 1 (Kueri ID $\rightarrow$ Dokumen EN Paper)**:
  - **Kueri Pengguna**: `"evaluasi performa temu kembali informasi lintas bahasa"`
  - **Target Dokumen**: `RES-000001` (Artikel Jurnal Riset Bahasa Inggris)
  - **Waktu Eksekusi**: **37,4 ms** | **Status**: `success`
  - **Halaman Bukti Terpilih**: `[Hal. 1, 2, 6]`
  - **Kalimat yang Diekstrak**:
    1. *[Hal. 1, Skor: 0.346]*: *"Introduction Cross-Language Information Retrieval (CLIR) is a special case of Information Retrieval (IR)..."*
    2. *[Hal. 1, Skor: 0.236]*: *"It explores solutions to finding relevant documents in a collection of documents written in a different language..."*
    3. *[Hal. 2, Skor: 0.329]*: *"However, current CLIR evaluation focuses more on the average performance over multiple topics than individual queries..."*
- **Pengujian 2 (Kueri ID $\rightarrow$ Dokumen EN Bab Buku)**:
  - **Kueri Pengguna**: `"manajemen waktu biaya proyek"`
  - **Target Dokumen**: `MAT-000007` (Chapter 1 Project Management)
  - **Waktu Eksekusi**: **35,0 ms** | **Status**: `success`
  - **Halaman Bukti Terpilih**: `[Hal. 2, 9]`
  - **Kalimat yang Diekstrak**:
    1. *[Hal. 2, Skor: 0.202]*: *"1.1 INTRODUCTION Many people and organizations today have a new—or renewed—interest in project management..."*
    2. *[Hal. 2, Skor: 0.188]*: *"Until the 1980s, project management primarily focused on providing schedule and resource data to top management..."*
    3. *[Hal. 9, Skor: 0.326]*: *"Alternatively, you might have to reduce the scope of a project to meet time and cost goals."*

#### 3. Analisis Ketercapaian Metrik Kinerja Summarization:
1. **Kecepatan Akses Instan (*Sub-5ms Cache Latency*)**: Melalui skema persistensi SQLite, pembacaan ringkasan berulang tercatat hanya memakan waktu **1,7–2,1 milidetik**, melampaui target performa sistem (< 5 ms). Untuk komputasi dingin (*cold execution*) pada buku tebal 36 halaman, TextRank dan MMR selesai dalam **477 ms** di CPU tanpa akselerasi GPU.
2. **Eliminasi Redundansi Efektif**: Skor *pairwise Jaccard overlap* antar-kalimat berada pada rentang **3,5% – 15,7%**, membuktikan bahwa parameter MMR ($\lambda = 0.70$) berhasil menyingkirkan pengulangan klausa dan memilih kalimat dengan perspektif informasi yang beragam.
3. **Keterlacakan Faktual Sempurna (*100% Traceability*)**: Seluruh kalimat ringkasan terhubung langsung dengan nomor halaman fisik dokumen sumber asli, memberikan transparansi akademis yang dapat diverifikasi pembaca secara langsung.
4. **Jaminan Zero Regression**: Pengujian verifikasi regresi membuktikan bahwa mesin penelusuran utama (Okapi BM25, TF-IDF VSM, dan Tolerant Retrieval) tetap berfungsi 100% tanpa gangguan apa pun.

---

# V. KESIMPULAN DAN RENCANA PENGEMBANGAN TAHAP II

### 5.1 Kesimpulan
Berdasarkan hasil analisis, perancangan arsitektur, implementasi perangkat lunak, dan evaluasi empiris yang telah dilaksanakan pada Proyek Tahap I, dapat diambil kesimpulan sebagai berikut:
1. **Keberhasilan Integrasi Multi-Korpus Akademik**: Perangkat lunak **Academic IR** berhasil mengintegrasikan tiga pilar repositori akademik yang sebelumnya terisolasi (*Bahan Kuliah OCW UI, Artikel Jurnal Riset DOAJ/arXiv, dan Skripsi Institusi*) ke dalam satu indeks terpadu berskala representatif yang mencakup **1.364 dokumen**, **56.881 unit potongan teks (*chunks*)**, serta **50.218 halaman fisik asli**.
2. **Superioritas Empiris Model Probabilistik Okapi BM25**: Pengujian benchmark pada 33 kueri terstruktur membuktikan keunggulan Okapi BM25 ($k_1=1.5, b=0.75$) dibanding TF-IDF Vector Space Model konvensional pada literatur akademik, ditandai dengan peningkatan signifikan pada **MAP (+48.4%, 0.1235 vs 0.0832)**, peningkatan **NDCG@10 (+20.2%, 0.2992 vs 0.2490)**, serta latensi pemrosesan 9 kali lebih cepat (**P50: 83.71 ms vs 751.84 ms**). Modul agregasi dokumen `max+2nd` secara efektif melenyapkan bias dominasi dokumen tebal.
3. **Ketangguhan Penanganan Kueri Melalui Tolerant Retrieval**: Lapisan *Tolerant Retrieval* dengan prinsip *Exact-First Priority* berhasil menormalisasi variasi ejaan akademik, memetakan singkatan teknis, serta memulihkan kesalahan pengetikan (*typo*) secara adaptif tanpa mengorbankan performa kueri eksak, didukung oleh transparansi *audit log* dan antarmuka *live suggestion autocomplete*.
4. **Penyelesaian Dilema Penyajian Temu Kembali Informasi (*Full Document Delivery*)**: Sistem berhasil menjembatani paradoks antara *passage retrieval* (yang mutlak dibutuhkan untuk mencegah *term dilution* pada dokumen multi-halaman) dan kebutuhan pembacaan dokumen utuh oleh pengguna. Melalui kartu hasil yang menampilkan abstrak resmi dan peta halaman relevan, serta penyediaan modul **In-App Full Document Reader** yang terhubung langsung ke tabel `pages`, pengguna dapat membaca seluruh halaman fisik dokumen secara berkesinambungan dengan penyorotan kata kunci kueri otomatis.
5. **Peringkasan Teks Cerdas Bebas Halusinasi**: Modul *Text Summarization* berbasis graf sentralitas kalimat **TextRank** dan eliminasi redundansi **MMR ($\lambda=0.70$)** berhasil menghasilkan intisari dokumen yang 100% faktual berdasar kalimat dokumen asli, mendukung ekstraksi bukti lintas bahasa (kueri Indonesia $\rightarrow$ paper Inggris), serta menyajikan waktu respons instan (**1,7–2,1 ms**) berkat persistensi tabel *cache* SQLite.

### 5.2 Rencana Pengembangan Tahap Selanjutnya (Roadmap Tahap II)
Untuk menyempurnakan sistem pada pengembangan tahap selanjutnya, direncanakan beberapa peningkatan strategis:
1. **Penerapan Pencarian Hibrida (*Hybrid Sparse-Dense Retrieval*)**: Memadukan kekuatan penelusuran leksikal Okapi BM25 dengan penelusuran semantik padat (*Dense Retrieval*) berbasis model *embedding* multibahasa (seperti *BGE-M3* atau *ColBERT*) menggunakan algoritma penggabungan peringkat *Reciprocal Rank Fusion (RRF)* untuk mengatasi kesenjangan kosakata (*vocabulary mismatch*).
2. **Neural Re-ranking Lapisan Kedua (*Cross-Encoder Re-ranking*)**: Menambahkan modul pemeringkatan ulang (*re-ranker*) berbobot ringan (*FlashRank / MiniLM*) pada Top-50 kandidat dokumen hasil BM25 untuk memperhitungkan interaksi semantik mendalam antara kueri dan konteks dokumen.
3. **Evaluasi Pengalaman Pengguna Formal (*Formal User Usability Study*)**: Melakukan pengujian kegunaan berbasis skenario tugas (*task-based user study*) dengan kuesioner *System Usability Scale (SUS)* yang melibatkan mahasiswa dan dosen untuk mengukur peningkatan efisiensi penemuan literatur akademik secara kuantitatif di lingkungan nyata.

---

# DAFTAR PUSTAKA

1. **Manning, C. D., Raghavan, P., & Schütze, H.** (2008). *Introduction to Information Retrieval*. Cambridge University Press.
2. **Salton, G., & Buckley, C.** (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management*, 24(5), 513–523.
3. **Baeza-Yates, R., & Ribeiro-Neto, B.** (2011). *Modern Information Retrieval: The Concepts and Technology behind Search* (2nd ed.). Addison-Wesley.
4. **Robertson, S. E., & Jones, K. S.** (1976). Relevance weighting of search terms. *Journal of the American Society for Information Science*, 27(3), 129–146.
5. **Robertson, S. E., & Zaragoza, H.** (2009). The probabilistic relevance framework: BM25 and beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389.
6. **Callan, J. P.** (1994). Passage-level retrieval of unstructured, informative documents. In *Proceedings of the 17th Annual International ACM SIGIR Conference*, 189–198.
7. **Kaszkiel, M., & Zobel, J.** (1997). Passage retrieval revisited. In *Proceedings of the 20th Annual International ACM SIGIR Conference*, 178–185.
8. **Järvelin, K., & Kekäläinen, J.** (2002). Cumulated gain-based evaluation of retrieval techniques. *ACM Transactions on Information Systems (TOIS)*, 20(4), 422–446.
9. **Asian, J., Williams, H. E., & Tahaghoghi, S. M.** (2005). Stemming Indonesian: A confix-stripping approach. *ACM Transactions on Asian Language Information Processing (TALIP)*, 4(4), 407–426.
10. **Damerau, F. J.** (1964). A technique for computer detection and correction of spelling errors. *Communications of the ACM*, 7(3), 171–176.
11. **Levenshtein, V. I.** (1966). Binary codes capable of correcting deletions, insertions, and reversals. *Soviet Physics Doklady*, 10(8), 707–710.
12. **Mihalcea, R., & Tarau, P.** (2004). TextRank: Bringing order into texts. In *Proceedings of the 2004 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 404–411.
13. **Carbonell, J., & Goldstein, J.** (1998). The use of MMR, diversity-based reranking for reordering documents and producing summaries. In *Proceedings of the 21st Annual International ACM SIGIR Conference*, 335–336.
14. **Erkan, G., & Radev, D. R.** (2004). LexRank: Graph-based lexical centrality as salience in text summarization. *Journal of Artificial Intelligence Research*, 22, 457–479.
15. **Reimers, N., & Gurevych, I.** (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 3982–3992.
16. **Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... & Duchesnay, É.** (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.
17. **Tiangolo, S.** (2023). *FastAPI: Modern, Fast (High-Performance), Web Framework for Building APIs with Python 3.8+*. Dokumen daring: `https://fastapi.tiangolo.com`.
18. **Next.js Team (Vercel)**. (2024). *Next.js 15 Documentation: The React Framework for the Web*. Dokumen daring: `https://nextjs.org/docs`.
19. **OpenCourseWare Universitas Indonesia**. (2026). *OCW UI — Free and Open Educational Resources*. `https://ocw.ui.ac.id`.

