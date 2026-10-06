# Audit Kesalahan dan Kelemahan Sistem Temu Kembali Informasi Akademik

## 1. Tujuan Dokumen

Dokumen ini menjabarkan kesalahan, kelemahan, dan masalah metodologis
pada sistem **Temu Kembali Informasi (Information Retrieval/IR) Akademik
Multi-Korpus** yang telah dikembangkan.

Dokumen ini disusun berdasarkan hasil audit/review terhadap sistem yang
menggunakan:

-   TF-IDF sebagai baseline.
-   Okapi BM25 sebagai baseline pembanding.
-   Document-level aggregation.
-   33 benchmark queries.
-   Qrels/relevance judgments.
-   Evaluasi P@5, P@10, Recall@10, MAP, MRR, dan NDCG.
-   Benchmark latency.
-   Multi-corpus yang mencakup Material, Research, dan Thesis.
-   Preprocessing, chunking, language detection, serta n-gram.
-   Fitur Academic Search dan Proposal Similarity.

Fokus utama dokumen ini adalah **mengidentifikasi apa yang salah atau
belum kuat pada sistem dan eksperimennya**, sehingga dapat digunakan
sebagai dasar perbaikan laporan, eksperimen, dan sistem.

------------------------------------------------------------------------

# 2. Ringkasan Masalah

Berdasarkan hasil audit, masalah terbesar sistem saat ini **bukan
kekurangan teknologi**, tetapi validitas eksperimen dan ketepatan klaim
yang dibuat berdasarkan hasil eksperimen.

Sistem sudah memiliki banyak komponen, tetapi beberapa kesimpulan belum
didukung oleh eksperimen yang cukup.

## Prioritas masalah

  -----------------------------------------------------------------------
  Prioritas               Masalah                 Severity
  ----------------------- ----------------------- -----------------------
  1                       Klaim "signifikan"      🔴 Critical
                          tanpa statistical       
                          significance test       

  2                       Interpretasi MRR        🔴 Critical
                          sebagai rata-rata rank  

  3                       P@10 hanya 0.2364       🔴 Critical

  4                       MAP hanya 0.1235        🔴 Critical

  5                       Qrels/relevance         🔴 Critical
                          judgment perlu diaudit  

  6                       Belum ada validasi      🔴 Critical
                          bahwa qrels tidak bias  
                          terhadap model          

  7                       Jumlah 33 query masih   🟠 High
                          terbatas untuk klaim    
                          umum                    

  8                       Penyebab peningkatan    🟠 High
                          BM25 terlalu cepat      
                          dikaitkan dengan        
                          document-length         
                          normalization           

  9                       Belum ada BM25          🟠 High
                          tuning/ablation         

  10                      Semantic/hybrid         🟠 High
                          retrieval belum diuji   
                          meskipun disebut        
                          sebagai solusi          

  11                      Istilah "berbasis       🟠 High
                          Machine Learning"       
                          kurang tepat untuk      
                          TF-IDF + BM25           

  12                      Benchmark latency belum 🟠 High
                          cukup untuk klaim       
                          production-ready        

  13                      Evaluasi belum dibedah  🟠 High
                          berdasarkan corpus dan  
                          jenis query             

  14                      Klaim cross-lingual     🟠 High
                          masih terlalu kuat      

  15                      Literature 2021--2026   🟡 Medium
                          belum terintegrasi      
                          secara kuat             
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 3. Masalah Kritis pada Evaluasi

## 3.1 Klaim "Signifikan" Tidak Didukung Statistical Significance Test

Sistem melaporkan:

``` text
MAP
TF-IDF = 0.0832
BM25   = 0.1235

NDCG
TF-IDF = 0.2490
BM25   = 0.2992
```

Perbedaan tersebut memang menunjukkan peningkatan numerik BM25
dibandingkan TF-IDF.

Namun, **peningkatan numerik tidak sama dengan statistical
significance**.

Klaim seperti:

> "BM25 mengungguli TF-IDF secara signifikan"

tidak dapat digunakan jika belum dilakukan pengujian statistik.

### Kesalahan

Sistem membedakan peningkatan relatif dengan statistical significance.

Contoh:

``` text
Relative improvement = +48.4%
```

berbeda dengan:

``` text
Statistically significant
p < 0.05
```

### Perbaikan

Gunakan skor per-query:

``` text
Q01: TF-IDF vs BM25
Q02: TF-IDF vs BM25
...
Q33: TF-IDF vs BM25
```

Kemudian gunakan salah satu metode paired statistical test, misalnya:

-   Wilcoxon signed-rank test.
-   Randomization test.
-   Paired bootstrap.

Idealnya laporan juga menyertakan:

``` text
Effect size
95% confidence interval
p-value
```

### Aturan klaim

Jika belum ada statistical significance test:

> **Jangan menggunakan kata "signifikan".**

Gunakan:

> "BM25 memperoleh nilai evaluasi yang lebih tinggi daripada TF-IDF."

------------------------------------------------------------------------

# 4. Interpretasi MRR Tidak Tepat

Nilai MRR yang diperoleh:

``` text
BM25 = 0.4270
TF-IDF = 0.3990
```

Kesalahan terjadi ketika MRR sebesar `0.4270` diinterpretasikan sebagai:

> "rata-rata dokumen relevan pertama berada pada peringkat ke-2."

Interpretasi tersebut tidak tepat.

Rumus MRR:

``` math
MRR = (1/Q) * Σ(1/rank_q)
```

Sehingga:

``` text
MRR = 0.427
```

tidak berarti:

``` text
average rank = 1 / 0.427
              = 2.34
```

karena secara umum:

``` text
E[1/R] != 1/E[R]
```

### Perbaikan

Gunakan interpretasi:

> Nilai MRR sebesar 0.4270 menunjukkan bahwa BM25 secara umum
> menempatkan dokumen relevan pertama pada posisi yang lebih tinggi
> dibandingkan TF-IDF yang memperoleh MRR sebesar 0.3990.

Jika ingin menjelaskan posisi dokumen relevan pertama, tampilkan
distribusi:

``` text
Rank 1 : xx%
Rank 2 : xx%
Rank 3 : xx%
Rank >3: xx%
```

------------------------------------------------------------------------

# 5. Absolute Retrieval Performance Masih Rendah

Hasil BM25:

``` text
P@5   = 0.2848
P@10  = 0.2364
R@10  = 0.1506
MAP   = 0.1235
NDCG  = 0.2992
```

Temuan ini penting karena menunjukkan bahwa BM25 memang lebih baik dari
TF-IDF, tetapi **efektivitas absolut sistem masih terbatas**.

## P@10

Dengan:

``` text
P@10 = 0.2364
```

secara sederhana hasil tersebut menunjukkan bahwa rata-rata sekitar 2--3
dari 10 hasil teratas dianggap relevan berdasarkan qrels.

Karena itu, sistem belum tepat jika disebut:

-   highly accurate;
-   highly relevant;
-   sangat akurat.

### Kesimpulan yang lebih tepat

> Hasil evaluasi menunjukkan bahwa BM25 memperbaiki baseline TF-IDF,
> tetapi absolute retrieval effectiveness masih terbatas.

Temuan ini justru dapat menjadi dasar penelitian tahap berikutnya.

------------------------------------------------------------------------

# 6. Acceptance Threshold Tidak Tercapai

Threshold yang ditetapkan sebelumnya:

``` text
P@10  >= 0.70
MAP   >= 0.65
NDCG@10 >= 0.75
```

Sedangkan hasil aktual:

``` text
P@10    = 0.2364
MAP     = 0.1235
NDCG@10 = 0.2992
```

Perbandingan:

  Metric      Target     BM25 Status
  --------- -------- -------- -------------------
  P@10          0.70   0.2364 ❌ Tidak tercapai
  MAP           0.65   0.1235 ❌ Tidak tercapai
  NDCG@10       0.75   0.2992 ❌ Tidak tercapai

### Kesalahan yang harus dihindari

Jangan menghapus threshold hanya agar sistem terlihat berhasil.

### Interpretasi yang benar

> Sistem belum memenuhi acceptance threshold yang telah ditetapkan.
> Failure analysis kemudian digunakan sebagai dasar pengembangan tahap
> berikutnya.

Kegagalan memenuhi threshold harus dianggap sebagai **hasil
eksperimen**, bukan sesuatu yang disembunyikan.

------------------------------------------------------------------------

# 7. Qrels Berpotensi Menjadi Sumber Masalah

Sistem memiliki:

``` text
33 queries
942 relevance judgments
```

Rata-rata:

``` text
942 / 33 ≈ 28.5 judgment/query
```

Jumlah tersebut sendiri bukan masalah.

Masalah utamanya adalah:

> **Bagaimana dokumen yang masuk ke dalam 942 relevance judgments
> tersebut dipilih?**

## Risiko bias

Misalnya prosesnya:

``` text
TF-IDF Top-30
+
BM25 Top-30
      ↓
   Combine
      ↓
 Deduplicate
      ↓
 Human Judgment
      ↓
     Qrels
```

Pendekatan tersebut relatif lebih defensible.

Namun jika prosesnya:

``` text
BM25 Top-30
      ↓
 Human Judgment
      ↓
     Qrels
```

maka evaluasi berpotensi bias terhadap BM25.

Lebih bermasalah lagi apabila qrels dibuat berdasarkan output sistem
yang sedang dievaluasi.

## Perbaikan

Gunakan pooling:

``` text
TF-IDF Top-50
+
BM25 Top-50
+
Random Sample
+
Retrieval Method Lain (jika tersedia)
        ↓
    Deduplicate
        ↓
 Human Relevance Judgment
        ↓
       Qrels
```

------------------------------------------------------------------------

# 8. "Tidak Ada di Qrels = Tidak Relevan" Harus Ditangani Hati-Hati

Sistem menggunakan pendekatan bahwa dokumen yang tidak tercatat di qrels
mendapatkan nilai:

``` text
0 = non-relevant
```

Masalahnya:

``` text
Not judged
```

tidak selalu sama dengan:

``` text
Non-relevant
```

Contoh:

``` text
Total dokumen = 1000
Dokumen yang dinilai = 30
```

970 dokumen lainnya belum tentu tidak relevan.

Mereka hanya:

> **belum dinilai.**

Hal ini dapat memengaruhi:

-   Recall.
-   MAP.
-   NDCG.
-   Interpretasi absolute retrieval effectiveness.

### Perbaikan

Metodologi evaluasi harus menjelaskan:

1.  Bagaimana kandidat qrels dipilih.
2.  Berapa dokumen yang dipool.
3.  Apakah semua kandidat dinilai.
4.  Bagaimana unjudged documents diperlakukan.
5.  Apakah penilaian relevance dilakukan secara manual.
6.  Apakah ada lebih dari satu assessor.
7.  Apakah terdapat agreement antar-assessor jika penilaian dilakukan
    oleh beberapa orang.

------------------------------------------------------------------------

# 9. Jumlah Query 33 Masih Terbatas

33 query sudah jauh lebih baik daripada benchmark 10 query.

Namun, jumlah tersebut masih relatif kecil untuk membuat klaim umum
seperti:

> Sistem cocok untuk unified academic search secara umum.

Masalah lain adalah distribusi query tidak sepenuhnya seimbang.

Contoh kategori:

``` text
Topical         = 9
Known-item      = 5
Methodological  = 5
Material        = 5
Cross-lingual   = 5
Constrained     = 4
```

### Perbaikan

Evaluasi harus dibagi menjadi:

``` text
Overall
Per query category
Per corpus
```

Minimal:

``` text
P@10 per category
NDCG@10 per category
MAP per category
```

Contoh tabel:

  Query Type         BM25 NDCG@10
  ---------------- --------------
  Known-item                    ?
  Topical                       ?
  Methodological                ?
  Material                      ?
  Cross-lingual                 ?
  Constrained                   ?

Tujuannya adalah mengetahui **di mana sistem berhasil dan di mana sistem
gagal**.

------------------------------------------------------------------------

# 10. Evaluasi Per Corpus Belum Cukup

Sistem bersifat multi-corpus:

``` text
MATERIAL
RESEARCH
THESIS
```

Tetapi hasil utama masih cenderung ditampilkan sebagai satu nilai:

``` text
Overall NDCG = 0.2992
```

Hal ini dapat menyembunyikan masalah pada corpus tertentu.

### Perbaikan

Tampilkan hasil:

``` text
Material
Research
Thesis
```

Contoh:

  Corpus          MAP     P@10   NDCG@10
  ---------- -------- -------- ---------
  Material          ?        ?         ?
  Research          ?        ?         ?
  Thesis            ?        ?         ?
  Overall      0.1235   0.2364    0.2992

Hal ini penting karena karakteristik dokumen berbeda.

Contoh:

-   Material cenderung memiliki terminologi pendidikan.
-   Research banyak menggunakan scientific English.
-   Thesis dapat berukuran lebih panjang.
-   Thesis mungkin memiliki metadata yang lebih kaya.

Jika BM25 baik pada Research tetapi buruk pada Thesis, masalah dapat
mengarah ke:

> document aggregation atau chunking pada dokumen Thesis.

------------------------------------------------------------------------

# 11. Klaim Cross-Lingual Terlalu Kuat

Contoh query:

``` text
sentiment analysis
```

tidak dapat digunakan sebagai bukti cross-lingual apabila dokumen juga
menggunakan bahasa Inggris.

Jika:

``` text
Query:
sentiment analysis

Document:
sentiment analysis
```

maka itu adalah:

> **monolingual retrieval**

bukan cross-lingual retrieval.

## Cross-lingual yang lebih valid

Contoh:

``` text
Query:
analisis sentimen

Relevant document:
sentiment analysis
```

atau:

``` text
Query:
pengelompokan data

Relevant document:
data clustering
```

### Perbaikan

Audit kembali query yang dikategorikan sebagai cross-lingual.

Jika query dan dokumen menggunakan bahasa yang sama:

> jangan menyebut eksperimen tersebut sebagai cross-lingual retrieval.

------------------------------------------------------------------------

# 12. Penyebab Peningkatan BM25 Tidak Bisa Langsung Disimpulkan

Laporan menyatakan bahwa peningkatan BM25 membuktikan pentingnya:

-   document length normalization;
-   term frequency saturation.

Kesimpulan tersebut terlalu kuat.

Sistem hanya membandingkan:

``` text
TF-IDF
vs
BM25
```

BM25 memiliki beberapa mekanisme yang berbeda dari TF-IDF.

Karena itu, dari eksperimen tersebut saja tidak dapat diketahui komponen
mana yang menyebabkan peningkatan.

## Perbaikan dengan ablation

Contoh:

``` text
TF-IDF
TF-IDF + normalization
BM25 tanpa length normalization
BM25 full
```

Atau lakukan parameter study:

### Parameter b

``` text
b = 0
b = 0.25
b = 0.50
b = 0.75
b = 1.00
```

### Parameter k1

``` text
k1 = 0.5
k1 = 1.0
k1 = 1.5
k1 = 2.0
```

Baru setelah eksperimen tersebut dilakukan, pembahasan mengenai
kontribusi parameter dapat dibuat dengan lebih kuat.

------------------------------------------------------------------------

# 13. Parameter BM25 Belum Dibuktikan Optimal

Parameter yang digunakan:

``` text
k1 = 1.5
b  = 0.75
```

Nilai tersebut merupakan nilai yang umum digunakan.

Namun:

> **common default != optimal untuk corpus tertentu.**

Parameter seharusnya dituning menggunakan development set, bukan test
set.

Contoh:

``` text
33 queries

Train/Development:
Q01–Q22

Test:
Q23–Q33
```

Jika jumlah query memungkinkan, cross-validation dapat dipertimbangkan.

### Masalah jika tuning dilakukan pada test set

Jika parameter BM25 dipilih berdasarkan hasil test set, maka test set
tidak lagi menjadi evaluasi yang independen.

Hal ini menyebabkan:

> **test-set leakage / overfitting terhadap benchmark.**

------------------------------------------------------------------------

# 14. Masalah pada Preprocessing dan Language Detection

Flow saat ini berpotensi:

``` text
PDF
 ↓
Chunking
 ↓
Language Detection
 ↓
Preprocessing
```

Hal ini dapat menjadi masalah pada dokumen bilingual.

Contoh satu chunk:

``` text
70% English
30% Indonesian
```

Language detector dapat salah menentukan bahasa utama.

### Perbaikan yang disarankan

Pertimbangkan:

``` text
Document/Page Language Detection
```

atau gunakan:

``` text
Chunk Language Confidence
```

dan simpan:

``` text
language
language_confidence
```

Hal ini membuat proses preprocessing lebih dapat dipertanggungjawabkan.

------------------------------------------------------------------------

# 15. Preprocessing Terlalu Agresif Dapat Merusak Istilah Akademik

Jika preprocessing menghapus karakter non-alfanumerik secara agresif,
istilah teknis dapat rusak.

Contoh:

``` text
C++
C#
.NET
BERT-base
RoBERTa
TF-IDF
LSTM
CNN-BiLSTM
R²
O(n log n)
```

Istilah tersebut sangat penting pada corpus Informatika.

### Risiko

Contoh:

``` text
C++
```

dapat berubah menjadi:

``` text
C
```

Hal ini dapat mengubah makna.

### Perbaikan

Gunakan preprocessing yang bersifat:

> **domain-aware**

Pertimbangkan mekanisme:

``` text
technical_term_protection
```

untuk mempertahankan istilah penting.

------------------------------------------------------------------------

# 16. Ukuran Corpus dan Vocabulary Perlu Dijelaskan

Sistem memiliki:

``` text
1.364 documents
57.202 chunks
1.969.538 terms
```

Rata-rata:

``` text
57.202 / 1.364 ≈ 41.9
```

atau sekitar:

> **42 chunks per document.**

Angka tersebut masih masuk akal, tetapi vocabulary sebesar sekitar 1.969
juta perlu dijelaskan.

Laporan perlu menjawab:

-   Apakah vocabulary dihitung setelah preprocessing?
-   Apakah vocabulary mencakup bigram?
-   Apakah vocabulary berasal dari chunk?
-   Apakah `min_df=2` digunakan?
-   Apakah rare terms dihapus?
-   Berapa jumlah unigram?
-   Berapa jumlah bigram?

Vocabulary yang sangat besar dapat menjadi indikasi:

> **vocabulary sparsity**

dan berpotensi memengaruhi performa retrieval.

------------------------------------------------------------------------

# 17. Proposal Similarity Adalah Task yang Berbeda

Sistem memiliki dua mode:

``` text
Academic Search
Proposal Similarity
```

Keduanya sebaiknya tidak diperlakukan sebagai task yang sama.

## Academic Search

``` text
query → documents
```

Metrik yang sesuai:

``` text
P@K
MAP
NDCG
MRR
```

## Proposal Similarity

``` text
document/query document → similar documents
```

Evaluasi dapat menggunakan:

``` text
Precision@K
Recall@K
Similarity threshold
Pair classification
Duplicate detection
Near-duplicate detection
```

### Masalah

Jika proposal similarity terlalu dicampur dengan eksperimen IR utama,
kontribusi utama sistem menjadi tidak jelas.

### Rekomendasi

Jadikan:

> **Proposal Similarity sebagai secondary module**

sementara kontribusi utama tetap:

> **Academic Information Retrieval.**

------------------------------------------------------------------------

# 18. Istilah "Berbasis Machine Learning" Kurang Tepat

Jika sistem utama menggunakan:

``` text
TF-IDF
+
BM25
```

maka penggunaan judul:

> "Sistem Temu Kembali Informasi Akademik Multi-Korpus Berbasis Machine
> Learning"

kurang presisi.

TF-IDF dan BM25 merupakan pendekatan **lexical information retrieval**,
bukan bukti bahwa keseluruhan sistem adalah machine-learning-based IR.

### Alternatif judul

#### Opsi 1

> **Pengembangan Sistem Temu Kembali Informasi Akademik Multi-Korpus
> Berbasis TF-IDF dan Okapi BM25 dengan Document-Level Aggregation**

#### Opsi 2

> **Pengembangan Sistem Temu Kembali Informasi Akademik Multi-Korpus
> Berbasis Lexical Retrieval**

Judul tersebut lebih sesuai dengan teknologi yang benar-benar digunakan.

------------------------------------------------------------------------

# 19. Klaim Production-Ready Belum Didukung Benchmark

Sistem melakukan latency benchmark:

``` text
TF-IDF P50 = 766.92 ms
BM25   P50 = 85.95 ms
```

Hasil ini menarik, tetapi belum cukup untuk menyatakan:

> "sistem production-ready."

Benchmark lokal tidak sama dengan production benchmark.

Belum terdapat pengujian terhadap:

-   concurrent users;
-   network latency;
-   API overhead;
-   database contention;
-   cold start;
-   memory under load;
-   containerized deployment;
-   horizontal scaling.

### Perbaikan klaim

Gunakan:

> **"membuktikan kelayakan operasional pada lingkungan pengujian
> lokal/prototipe."**

Jangan menggunakan:

> "production-ready"

jika pengujian production belum dilakukan.

------------------------------------------------------------------------

# 20. Benchmark Latency Harus Apple-to-Apple

Perbandingan:

``` text
TF-IDF P50 = 766.92 ms
BM25   P50 = 85.95 ms
```

harus dipastikan dilakukan dengan kondisi yang sama.

Minimal:

``` text
same machine
same queries
same warm-up
same candidate K
same preprocessing
same metadata filtering
same aggregation
```

Selain itu, latency sebaiknya dipecah menjadi:

``` text
Query preprocessing
        ↓
Retrieval
        ↓
Document aggregation
        ↓
Database lookup
        ↓
Serialization
        ↓
Total API latency
```

Karena latency yang dirasakan pengguna adalah:

``` text
T_total
```

bukan hanya waktu retrieval engine.

------------------------------------------------------------------------

# 21. Belum Terbukti Bahwa Metadata-Aware Ranking Meningkatkan Performa

Laporan menyebut:

``` text
title weighting
metadata weighting
metadata-aware ranking
```

Namun hasil utama yang dilaporkan masih:

``` text
TF-IDF
vs
BM25
```

Dengan demikian, belum ada bukti eksperimen bahwa metadata benar-benar
meningkatkan ranking.

### Eksperimen yang diperlukan

Bandingkan:

``` text
BM25
BM25 + title
BM25 + metadata
BM25 + title + metadata
```

Kemudian ukur:

``` text
ΔNDCG
ΔMAP
ΔP@10
```

Barulah dapat dibuat klaim bahwa metadata-aware ranking memberikan
peningkatan.

------------------------------------------------------------------------

# 22. Tampilan Score pada UI Dapat Menyesatkan Pengguna

UI menampilkan contoh:

``` text
Score: 0.842
```

Masalahnya, pengguna dapat menganggap:

``` text
0.842 = 84.2% relevan
```

Padahal BM25 score tidak memiliki interpretasi seperti itu.

### Perbaikan UI

Daripada hanya menampilkan:

``` text
Score: 0.842
```

lebih baik tampilkan:

``` text
Relevance
Matched Terms
Best Matching Page
Why this result?
Document Type
Year
```

------------------------------------------------------------------------

# 23. Explainability Lebih Bernilai Daripada Angka Score

Karena retrieval utama bersifat lexical, sistem dapat menyediakan:

``` text
Why this result?
```

Contoh:

``` text
Why this result?

Matched terms:
- machine learning
- sentiment analysis
- classification

Best match:
Page 14

Document type:
Research

Year:
2025
```

Fitur ini dapat memberikan explainability yang lebih bermakna daripada:

``` text
Score: 0.734
```

------------------------------------------------------------------------

# 24. Error Analysis Menunjukkan Masalah Vocabulary Mismatch

Error analysis menunjukkan adanya:

``` text
Vocabulary mismatch
Cross-lingual vocabulary gap
```

Masalah ini penting karena BM25 pada dasarnya masih merupakan lexical
retrieval.

Jika query menggunakan istilah yang berbeda dari istilah di dokumen,
BM25 dapat gagal meskipun maknanya sama.

Contoh:

``` text
Query:
analisis sentimen

Document:
sentiment analysis
```

Lexical matching biasa tidak selalu mampu menganggap kedua istilah
tersebut sama secara semantik.

------------------------------------------------------------------------

# 25. Urutan Pengembangan Berikutnya

Jangan langsung menambahkan model paling kompleks.

Urutan eksperimen yang lebih tepat:

``` text
TF-IDF
   ↓
BM25
   ↓
Document-Level Aggregation
   ↓
Query Expansion
   ↓
Multilingual Dense Retrieval
   ↓
Hybrid IR
   ↓
Optional Reranker
```

Pendekatan ini membuat hubungan:

``` text
Problem
   ↓
Method
   ↓
Experiment
   ↓
Evaluation
   ↓
Conclusion
```

menjadi jelas.

------------------------------------------------------------------------

# 26. Arsitektur Eksperimen yang Direkomendasikan

Gunakan **ablation ladder**:

``` text
E0
TF-IDF
   ↓
E1
TF-IDF + Chunk
   ↓
E2
TF-IDF + Chunk + Aggregation
   ↓
E3
BM25 + Chunk + Aggregation
   ↓
E4
BM25 + Query Expansion
   ↓
E5
Dense Retrieval
   ↓
E6
Hybrid BM25 + Dense
```

Buat tabel eksperimen:

  Experiment     MAP   NDCG@10   P@10   Latency
  ------------ ----- --------- ------ ---------
  E0                                  
  E1                                  
  E2                                  
  E3                                  
  E4                                  
  E5                                  
  E6                                  

Dengan desain tersebut, setiap peningkatan dapat ditelusuri berdasarkan
perubahan metode.

------------------------------------------------------------------------

# 27. Masalah Utama yang Harus Diperbaiki Terlebih Dahulu

## 🔴 Prioritas 1 --- Audit Evaluasi

Perbaiki:

-   qrels;
-   pooling;
-   relevance judgment;
-   statistical significance;
-   per-query evaluation;
-   per-category evaluation;
-   per-corpus evaluation.

## 🔴 Prioritas 2 --- Perbaiki Klaim

Hapus atau ubah klaim:

> "signifikan"

jika belum ada statistical test.

Hapus:

> "average rank 2"

dari interpretasi MRR.

Hapus:

> "production-ready"

jika hanya berdasarkan latency lokal.

Pertimbangkan mengganti:

> "berbasis Machine Learning"

jika sistem hanya menggunakan TF-IDF dan BM25.

## 🔴 Prioritas 3 --- Cari Penyebab MAP/P@10 Rendah

Lakukan error analysis yang lebih mendalam untuk mengetahui:

-   vocabulary mismatch;
-   cross-lingual mismatch;
-   long-document problem;
-   chunking problem;
-   metadata problem;
-   query formulation problem;
-   qrels problem.

## 🟠 Prioritas 4 --- Query Expansion

Karena error analysis menunjukkan vocabulary mismatch, lakukan
eksperimen:

``` text
BM25
vs
BM25 + Query Expansion
```

Contoh:

``` text
Query:
analisis sentimen

Expansion:
analisis sentimen
sentiment analysis
opinion mining
sentiment classification
```

## 🟠 Prioritas 5 --- BM25 Tuning

Jangan langsung menganggap:

``` text
k1 = 1.5
b = 0.75
```

optimal.

## 🟠 Prioritas 6 --- Semantic Retrieval

Setelah baseline lexical cukup terukur, uji multilingual dense
retrieval.

## 🟡 Prioritas 7 --- Hybrid Retrieval

Jika dense retrieval memberikan keuntungan, bandingkan:

``` text
BM25
vs
Dense
vs
BM25 + Dense
```

## 🟡 Prioritas 8 --- User Study

User study dilakukan setelah ranking cukup stabil.

------------------------------------------------------------------------

# 28. OASE dan Dataset Eksternal

Jika sistem ditujukan untuk kebutuhan OASE tetapi dataset aktual tidak
tersedia dan menggunakan dataset eksternal, hal tersebut harus
dinyatakan secara eksplisit.

Gunakan framing:

> **Dataset eksternal digunakan sebagai proxy/benchmark corpus, bukan
> sebagai representasi langsung dari isi OASE Universitas Udayana.**

Struktur penjelasan:

``` text
OASE
 │
 │ motivating use case
 ↓
Academic IR Requirements
 │
 ↓
Public Benchmark Corpus
 │
 ├── UI OCW
 ├── Research Repositories
 └── Thesis Repositories
```

Dengan demikian, penggunaan dataset eksternal tidak terlihat sebagai
ketidaksesuaian, melainkan sebagai keputusan metodologis yang
dijelaskan.

------------------------------------------------------------------------

# 29. Kesimpulan Audit

Sistem **tidak perlu dibongkar dari awal**.

Fondasi yang sudah dibuat cukup baik, terutama:

-   Dual baseline TF-IDF vs BM25.
-   Document-level aggregation.
-   33 benchmark queries.
-   Graded relevance.
-   Error analysis.
-   Latency P50/P95/P99.
-   Multi-corpus.

Namun, kelemahan terbesar berada pada:

1.  Validitas qrels.
2.  Statistical significance.
3.  Interpretasi metrik.
4.  Rendahnya absolute retrieval effectiveness.
5.  Evaluasi yang belum cukup granular.
6.  Klaim cross-lingual yang terlalu kuat.
7.  Klaim production-ready yang terlalu dini.
8.  Belum adanya ablation yang membuktikan penyebab peningkatan BM25.
9.  Belum adanya tuning BM25.
10. Belum adanya pengujian semantic/hybrid retrieval.

------------------------------------------------------------------------

# 30. Penilaian Kondisi Sistem Saat Ini

  Aspek                    Penilaian
  ---------------------- -----------
  Arsitektur                    8/10
  Engineering                   8/10
  Konsep IR                     8/10
  Evaluasi                      6/10
  Validitas eksperimen        5.5/10
  User-centered IR              5/10
  Potensi penelitian        **9/10**

Penilaian tersebut menunjukkan bahwa sistem memiliki **potensi
penelitian yang tinggi**, tetapi validitas eksperimen masih perlu
diperkuat.

------------------------------------------------------------------------

# 31. Kesalahan Utama dalam Satu Kalimat

Jika seluruh masalah sistem diringkas menjadi satu pernyataan:

> **Sistem sudah memiliki arsitektur dan komponen IR yang cukup matang,
> tetapi beberapa klaim performa belum didukung oleh validasi eksperimen
> yang memadai, sementara absolute retrieval performance masih rendah
> sehingga penyebab kegagalan perlu dianalisis sebelum sistem dibuat
> lebih kompleks.**

------------------------------------------------------------------------

# 32. Kondisi yang Harus Dicapai Sebelum Sistem Dianggap Kuat

Sistem sebaiknya belum dianggap final sebelum minimal:

-   [ ] Qrels diaudit.
-   [ ] Proses pooling dijelaskan.
-   [ ] Unjudged document handling dijelaskan.
-   [ ] Statistical significance test dilakukan.
-   [ ] MRR diinterpretasikan dengan benar.
-   [ ] P@10, MAP, dan NDCG dilaporkan secara jujur.
-   [ ] Evaluasi per-query dilakukan.
-   [ ] Evaluasi per-category dilakukan.
-   [ ] Evaluasi per-corpus dilakukan.
-   [ ] Klaim cross-lingual diverifikasi.
-   [ ] BM25 tuning dilakukan pada development set.
-   [ ] Ablation experiment dilakukan.
-   [ ] Metadata-aware ranking diuji secara terpisah.
-   [ ] Latency benchmark dibuat apple-to-apple.
-   [ ] Klaim production-ready diperbaiki.
-   [ ] Error analysis vocabulary mismatch diperkuat.
-   [ ] Query expansion diuji.
-   [ ] Semantic retrieval diuji jika diperlukan.
-   [ ] Hybrid retrieval hanya ditambahkan setelah dense retrieval
    terbukti bermanfaat.

------------------------------------------------------------------------

# 33. Prinsip Utama Perbaikan

Prinsip yang harus digunakan dalam pengembangan selanjutnya adalah:

> **Jangan menambahkan kompleksitas sebelum memahami kegagalan
> baseline.**

Urutan yang disarankan:

``` text
Audit
  ↓
Validasi
  ↓
Error Analysis
  ↓
Ablation
  ↓
Improvement
  ↓
Statistical Test
  ↓
Conclusion
```

Bukan:

``` text
Baseline gagal
  ↓
Tambahkan model yang lebih kompleks
  ↓
Klaim sistem lebih baik
```

Dengan pendekatan pertama, setiap perubahan sistem memiliki alasan
ilmiah dan dapat dipertanggungjawabkan.

------------------------------------------------------------------------

## Referensi Audit

Dokumen ini merupakan penjabaran ulang dari hasil audit/review yang
diberikan, tanpa menambahkan klaim eksperimen baru yang tidak terdapat
pada materi audit tersebut.
