# Tolerant Retrieval --- Feature Specification

## 1. Overview

**Tolerant Retrieval** adalah lapisan tambahan pada sistem Information
Retrieval (IR) untuk menangani query yang memiliki typo, variasi
spelling, singkatan, istilah teknis, variasi morfologis, dan perbedaan
istilah Indonesia--Inggris.

Fitur ini **tidak menggantikan BM25**. Tolerant Retrieval berfungsi
sebagai query normalization/recovery layer sebelum lexical retrieval.

``` text
User Query
    ↓
Query Analysis
    ↓
Tolerant Retrieval Layer
    ├── Exact Term
    ├── Typo Correction
    ├── Fuzzy Matching
    ├── Abbreviation Handling
    ├── Spelling Variation
    ├── Technical-Term Normalization
    ├── Morphological Variation
    └── Cross-Lingual Tolerance
    ↓
Expanded / Normalized Query
    ↓
BM25 / Dense / Hybrid Retrieval
    ↓
Document Aggregation
    ↓
Final Ranking
```

------------------------------------------------------------------------

## 2. Tujuan

Tolerant Retrieval harus:

1.  Meningkatkan recall pada query yang mengandung typo.
2.  Menangani variasi penulisan istilah.
3.  Menangani singkatan akademik/teknis.
4.  Menangani variasi format istilah teknis.
5.  Menangani variasi morfologis sederhana.
6.  Membantu query Indonesia--Inggris.
7.  Mempertahankan precision dengan memprioritaskan exact match.
8.  Tidak menggantikan retrieval engine utama.
9.  Tidak melakukan fuzzy matching secara agresif pada semua query.
10. Menyimpan informasi transformasi query untuk debugging dan
    explainability.

------------------------------------------------------------------------

## 3. Prinsip Utama

### 3.1 BM25 Tetap Menjadi Retrieval Engine Utama

``` text
Query
 ↓
Normalize / Recover
 ↓
BM25
```

Tolerant Retrieval bukan pengganti BM25.

### 3.2 Exact Match Harus Diprioritaskan

Gunakan strategi:

``` text
1. Exact retrieval
2. Evaluasi kualitas hasil
3. Jika hasil memadai → gunakan retrieval normal
4. Jika hasil kurang memadai → aktifkan Tolerant Retrieval
5. Generate candidate terms
6. Validate candidates
7. Generate normalized/expanded query
8. BM25 retrieval
9. Final ranking
```

Tujuannya mencegah fuzzy retrieval menghasilkan terlalu banyak false
positive.

------------------------------------------------------------------------

# 4. Komponen Fitur

  -------------------------------------------------------------------------------
  Komponen                Contoh                          Tujuan
  ----------------------- ------------------------------- -----------------------
  Typo tolerance          `sentimen analisi` →            Menangani typo
                          `sentimen analisis`             

  Fuzzy matching          istilah dengan kemiripan string Menangani variasi kecil

  Spelling variation      `optimization` ↔ `optimisation` Variasi ejaan

  Abbreviation            `NLP` ↔                         Ekspansi singkatan
                          `Natural Language Processing`   

  Technical normalization `TF IDF` ↔ `TF-IDF`             Normalisasi istilah
                                                          teknis

  Morphological variation `cluster` ↔ `clustering`        Variasi bentuk kata

  Cross-lingual tolerance `analisis sentimen` ↔           Variasi
                          `sentiment analysis`            Indonesia--Inggris
  -------------------------------------------------------------------------------

------------------------------------------------------------------------

# 5. Typo Tolerance

Contoh:

``` text
Input:
sentimen analisi

Candidate:
sentimen analisis
```

Contoh:

``` text
Input:
analisis sentimen menggunkan BERT

Correction:
analisis sentimen menggunakan BERT
```

Simpan:

``` text
original_query
corrected_query
correction
confidence
```

Contoh:

``` json
{
  "original": "analisis sentimen menggunkan BERT",
  "corrected": "analisis sentimen menggunakan BERT",
  "changes": [
    {
      "from": "menggunkan",
      "to": "menggunakan",
      "confidence": 0.96
    }
  ]
}
```

------------------------------------------------------------------------

# 6. Fuzzy Term Matching

Fuzzy matching digunakan untuk mencari kandidat istilah yang memiliki
kemiripan string tinggi.

Gunakan guard:

-   similarity threshold;
-   maximum candidate count;
-   vocabulary validation;
-   technical-term protection;
-   confidence score.

Contoh konfigurasi awal:

``` text
fuzzy_enabled = true
fuzzy_threshold = 0.85
max_fuzzy_candidates = 3
```

Nilai tersebut adalah **starting point**, bukan nilai optimal. Parameter
harus dapat dituning melalui eksperimen.

------------------------------------------------------------------------

# 7. Spelling Variation

Tangani variasi ejaan yang memiliki hubungan terminologis.

Contoh:

``` text
optimization
optimisation
```

Normalisasi harus hati-hati agar istilah yang berbeda tidak disamakan
secara salah.

------------------------------------------------------------------------

# 8. Abbreviation Handling

Contoh:

``` text
NLP
```

dapat memiliki candidate:

``` text
Natural Language Processing
```

Representasi internal:

``` json
{
  "term": "NLP",
  "expansions": [
    "Natural Language Processing"
  ]
}
```

Ekspansi hanya dilakukan jika confidence memadai.

------------------------------------------------------------------------

# 9. Technical-Term Normalization

Istilah teknis harus dilindungi.

Contoh:

``` text
TF IDF
TF-IDF
TFIDF

CNN BiLSTM
CNN-BiLSTM
CNN Bi-LSTM
```

Technical terms yang berpotensi membutuhkan perlakuan khusus:

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

Jangan menggunakan preprocessing agresif yang menghilangkan karakter
penting dari istilah tersebut.

------------------------------------------------------------------------

# 10. Morphological Variation

Contoh:

``` text
cluster
clustering
```

Gunakan candidate generation dan validation. Jangan menganggap semua
variasi morfologis selalu identik.

------------------------------------------------------------------------

# 11. Cross-Lingual Tolerance

Contoh:

``` text
analisis sentimen
        ↕
sentiment analysis
```

atau:

``` text
pengelompokan data
        ↕
data clustering
```

Perlu dibedakan antara **cross-lingual expansion** dan **cross-lingual
retrieval evaluation**.

Melakukan expansion lintas bahasa saja belum cukup untuk menyatakan
bahwa sistem telah membuktikan performa cross-lingual retrieval.

------------------------------------------------------------------------

# 12. Query Processing Pipeline

``` text
                    User Query
                         │
                         ▼
                  Query Analysis
                         │
                         ▼
                 Exact Retrieval
                         │
              ┌──────────┴──────────┐
              │                     │
       Results Adequate?        Results Poor?
              │                     │
             YES                    ▼
              │             Tolerant Retrieval
              │                     │
              │          ┌──────────┼───────────┐
              │          │          │           │
              │        Typo       Fuzzy    Abbreviation
              │          │          │           │
              │          ├──────────┼───────────┤
              │          │          │           │
              │       Spelling   Technical   Cross-Lingual
              │       Variation    Terms       Terms
              │          │          │           │
              │          └──────────┼───────────┘
              │                     │
              │                     ▼
              │             Candidate Validation
              │                     │
              └─────────────────────┤
                                    ▼
                              BM25 Retrieval
                                    │
                                    ▼
                           Document Aggregation
                                    │
                                    ▼
                              Final Ranking
```

------------------------------------------------------------------------

# 13. Query Transformation Example

Input:

``` text
analisis sentimen menggunkan BERT
```

Tolerant layer mendeteksi:

``` text
menggunkan
    ↓
menggunakan
```

Normalized query:

``` text
analisis sentimen menggunakan BERT
```

Possible expansion:

``` text
analisis sentimen menggunakan BERT
sentiment analysis BERT
```

Original query harus tetap disimpan.

``` json
{
  "original_query": "analisis sentimen menggunkan BERT",
  "normalized_query": "analisis sentimen menggunakan BERT",
  "expanded_terms": [
    "sentiment analysis"
  ],
  "corrections": [
    {
      "source": "menggunkan",
      "target": "menggunakan",
      "confidence": 0.96
    }
  ]
}
```

------------------------------------------------------------------------

# 14. Ranking Strategy

Prioritas:

``` text
Exact Match
    >
Normalized Match
    >
High-confidence Tolerant Match
    >
Low-confidence Tolerant Match
```

Conceptual score dapat berupa:

``` text
final_score =
    bm25_score
    + exact_match_bonus
    + normalized_match_bonus
    + tolerant_match_bonus
```

Bobot tersebut **bukan nilai final** dan harus divalidasi melalui
eksperimen.

------------------------------------------------------------------------

# 15. Confidence Scoring

Setiap transformasi sebaiknya memiliki confidence:

``` text
Typo correction    : 0.96
Fuzzy candidate    : 0.89
Abbreviation       : 0.99
Cross-lingual      : 0.91
```

Confidence digunakan untuk:

1.  Memfilter candidate.
2.  Mencegah expansion berlebihan.
3.  Membantu ranking.
4.  Debugging.
5.  Explainability.

------------------------------------------------------------------------

# 16. False Positive Protection

Gunakan:

``` text
minimum similarity threshold
maximum candidates
domain vocabulary
technical term protection
candidate confidence
exact-match priority
```

Jika confidence rendah:

``` text
DO NOT EXPAND
```

Sistem lebih baik mempertahankan query asli daripada melakukan expansion
yang salah.

------------------------------------------------------------------------

# 17. Fallback Logic

Tolerant Retrieval sebaiknya hanya menjadi fallback.

``` text
Query
 ↓
Normal BM25
 ↓
Check result quality
```

Jika:

``` text
Plausible results = YES
```

gunakan normal BM25.

Jika:

``` text
Plausible results = NO
```

aktifkan Tolerant Retrieval.

Indikator awal dapat berupa:

``` text
no results
very low retrieval score
too few candidates
high query OOV ratio
```

Threshold harus configurable dan diuji secara eksperimen.

------------------------------------------------------------------------

# 18. Logging

Simpan:

``` text
original_query
normalized_query
expanded_query
detected_language
corrections
fuzzy_candidates
abbreviation_expansions
cross_lingual_expansions
confidence
retrieval_mode
```

Contoh:

``` json
{
  "original_query": "sentimen analisi menggunkan BERT",
  "normalized_query": "sentimen analisis menggunakan BERT",
  "retrieval_mode": "tolerant",
  "corrections": [
    {
      "from": "analisi",
      "to": "analisis",
      "confidence": 0.97
    }
  ]
}
```

------------------------------------------------------------------------

# 19. Explainability

UI dapat menampilkan:

``` text
Did you mean:
analisis sentimen menggunakan BERT
```

atau:

``` text
Query normalized from:
sentimen analisi

to:
sentimen analisis
```

Untuk expansion:

``` text
Expanded terms:
sentiment analysis
opinion mining
```

Jangan mengartikan BM25 score sebagai persentase relevansi.

------------------------------------------------------------------------

# 20. Arsitektur Modul

Pisahkan Tolerant Retrieval dari retrieval engine.

Contoh:

``` text
retrieval/
├── query/
│   ├── analyzer
│   ├── normalizer
│   ├── typo_corrector
│   ├── fuzzy_matcher
│   ├── abbreviation_handler
│   ├── technical_term_normalizer
│   ├── morphology_handler
│   └── cross_lingual_expander
│
├── tolerant/
│   ├── candidate_generator
│   ├── candidate_validator
│   ├── confidence_scorer
│   └── fallback_controller
│
├── ranking/
│   ├── bm25
│   ├── aggregation
│   └── final_ranker
│
└── evaluation/
    ├── metrics
    ├── qrels
    └── tolerant_evaluation
```

Nama folder boleh disesuaikan dengan project existing.

**Jangan membuat ulang BM25 jika implementation BM25 sudah tersedia.**

------------------------------------------------------------------------

# 21. Konfigurasi

Semua parameter penting harus configurable.

``` yaml
tolerant_retrieval:
  enabled: true
  fallback_only: true

  typo:
    enabled: true
    min_confidence: 0.90

  fuzzy:
    enabled: true
    similarity_threshold: 0.85
    max_candidates: 3

  abbreviation:
    enabled: true
    min_confidence: 0.90

  spelling_variation:
    enabled: true

  technical_terms:
    enabled: true
    protect_terms: true

  morphology:
    enabled: true

  cross_lingual:
    enabled: true
    min_confidence: 0.90

  ranking:
    exact_match_priority: true
```

Nilai di atas merupakan konfigurasi awal dan harus divalidasi.

------------------------------------------------------------------------

# 22. Experimental Design

Tolerant Retrieval harus menjadi eksperimen terpisah.

``` text
E3 = BM25

E4 = BM25 + Tolerant Retrieval

E5 = BM25 + Query Expansion

E6 = BM25 + Tolerant Retrieval + Query Expansion
```

Jika project memiliki nomor eksperimen berbeda, sesuaikan ID tanpa
mengubah urutan logis.

------------------------------------------------------------------------

# 23. Evaluation Metrics

Gunakan:

``` text
P@5
P@10
Recall@10
MAP
NDCG@10
MRR
Latency
```

Bandingkan:

``` text
BM25
vs
BM25 + Tolerant Retrieval
```

Laporkan:

``` text
ΔP@10
ΔMAP
ΔNDCG@10
ΔMRR
ΔRecall@10
ΔLatency
```

Jika memungkinkan, gunakan paired statistical test pada per-query
scores.

Tanpa statistical test, jangan menyebut peningkatan sebagai:

> "signifikan secara statistik."

Gunakan:

> "menunjukkan peningkatan numerik."

------------------------------------------------------------------------

# 24. Query Categories

Buat subset:

``` text
Normal Query
Typo Query
Technical Query
Abbreviation Query
Spelling Variation Query
Morphological Variation Query
Cross-Lingual Query
```

Tabel evaluasi:

  Query Type             P@10   MAP   NDCG@10   MRR   Latency
  -------------------- ------ ----- --------- ----- ---------
  Normal                                            
  Typo                                              
  Technical                                         
  Abbreviation                                      
  Spelling Variation                                
  Morphological                                     
  Cross-Lingual                                     

Tujuan:

> Mengetahui apakah Tolerant Retrieval membantu query bermasalah tanpa
> merusak query normal.

------------------------------------------------------------------------

# 25. Research Question

Research question yang dapat digunakan:

> **Apakah Tolerant Retrieval meningkatkan recall pada query yang
> mengandung kesalahan penulisan, variasi istilah, dan variasi bahasa
> tanpa menurunkan precision secara signifikan?**

Jawaban harus didasarkan pada hasil eksperimen.

------------------------------------------------------------------------

# 26. Precision vs Recall

Tolerant Retrieval terutama diharapkan meningkatkan:

``` text
Recall ↑
```

tetapi harus dipantau terhadap:

``` text
Precision ↓
```

Target yang diharapkan:

``` text
Recall meningkat
+
Precision tidak turun secara tidak terkendali
```

Jika recall meningkat tetapi precision turun drastis, konfigurasi belum
dapat dianggap berhasil.

------------------------------------------------------------------------

# 27. Latency Evaluation

Ukur:

``` text
BM25
vs
BM25 + Tolerant Retrieval
```

Gunakan:

``` text
P50
P95
P99
```

Pisahkan:

``` text
Query preprocessing
Typo correction
Fuzzy matching
Expansion
BM25 retrieval
Aggregation
Total latency
```

Jangan menyimpulkan production readiness hanya berdasarkan benchmark
lokal.

------------------------------------------------------------------------

# 28. Ablation Experiment

Uji komponen secara terpisah:

``` text
T0 = BM25

T1 = BM25 + Typo Correction

T2 = BM25 + Fuzzy Matching

T3 = BM25 + Abbreviation

T4 = BM25 + Technical Normalization

T5 = BM25 + Cross-Lingual Expansion

T6 = BM25 + All Tolerant Components
```

Bandingkan:

``` text
MAP
NDCG@10
P@10
MRR
Latency
```

Tujuannya mengetahui komponen mana yang benar-benar berkontribusi.

------------------------------------------------------------------------

# 29. Regression Testing

Penambahan fitur tidak boleh merusak baseline.

Minimal test:

``` text
Normal:
machine learning

Exact:
sentiment analysis

Typo:
sentimen analisi

Technical:
CNN-BiLSTM

Abbreviation:
NLP

Cross-lingual:
analisis sentimen
```

Pastikan query normal tidak mengalami penurunan ranking yang tidak
diinginkan.

------------------------------------------------------------------------

# 30. Edge Cases

Tangani:

``` text
Empty query
Very short query
Single-character query
Numbers
Technical symbols
Mixed language
Unknown abbreviation
Unknown technical term
Very high typo rate
Multiple typos
Long query
Query with punctuation
```

Technical terms seperti:

``` text
C++
C#
.NET
R²
TF-IDF
BERT-base
```

tidak boleh rusak akibat normalization.

------------------------------------------------------------------------

# 31. Robustness

Cegah:

-   candidate explosion;
-   query expansion explosion;
-   unlimited fuzzy candidates;
-   recursive expansion;
-   repeated normalization;
-   infinite correction loop.

Contoh masalah yang harus dicegah:

``` text
term A
 ↓
term B
 ↓
term C
 ↓
term A
```

Gunakan:

``` text
max expansion depth
max candidates
visited terms
```

------------------------------------------------------------------------

# 32. Statistik Penggunaan

Log statistik:

``` text
total queries
queries using exact retrieval
queries using tolerant retrieval
queries corrected
queries expanded
queries with no correction
queries with low confidence
queries with multiple corrections
```

Contoh format:

``` text
Total queries             : 1000
Exact retrieval            : 720
Tolerant fallback          : 280
Typo correction            : 160
Fuzzy matching             : 85
Abbreviation expansion     : 42
Cross-lingual expansion    : 63
Low-confidence candidates  : 21
```

Angka di atas hanya contoh format, bukan hasil aktual.

------------------------------------------------------------------------

# 33. Hal yang Tidak Boleh Dilakukan

Implementasi tidak boleh:

1.  Menggantikan BM25.
2.  Melakukan fuzzy matching ke seluruh vocabulary tanpa threshold.
3.  Menghasilkan candidate tidak terbatas.
4.  Menghapus technical terms.
5.  Menganggap semua abbreviation memiliki satu arti.
6.  Menganggap semua morphological variants identik.
7.  Mengklaim cross-lingual retrieval hanya karena melakukan expansion.
8.  Mengubah original query secara permanen.
9.  Menggunakan test set untuk memilih threshold tanpa kontrol
    metodologis.
10. Mengklaim statistical significance tanpa statistical test.
11. Mengaktifkan semua expansion tanpa evaluasi.
12. Menurunkan precision secara signifikan tanpa dianalisis.
13. Membuat ulang BM25 jika implementation existing sudah tersedia.
14. Merusak pipeline retrieval yang sudah berjalan.

------------------------------------------------------------------------

# 34. Acceptance Criteria

### Implementasi

-   [ ] Tolerant Retrieval module dibuat.
-   [ ] BM25 tetap menjadi retrieval engine.
-   [ ] Exact-first strategy diterapkan.
-   [ ] Fallback controller diterapkan.
-   [ ] Typo correction tersedia.
-   [ ] Fuzzy matching memiliki threshold.
-   [ ] Candidate count dibatasi.
-   [ ] Abbreviation handling tersedia.
-   [ ] Technical terms dilindungi.
-   [ ] Spelling variation ditangani.
-   [ ] Morphological variation ditangani secara hati-hati.
-   [ ] Cross-lingual tolerance dapat dikontrol.
-   [ ] Confidence scoring tersedia.
-   [ ] Candidate validation tersedia.
-   [ ] Original query selalu dipertahankan.
-   [ ] Query transformation dapat dilog.
-   [ ] False-positive protection tersedia.
-   [ ] Latency tambahan dapat diukur.
-   [ ] Error handling tersedia.

### Eksperimen

-   [ ] BM25 baseline tersedia.
-   [ ] BM25 + Tolerant Retrieval diuji.
-   [ ] P@5 dibandingkan.
-   [ ] P@10 dibandingkan.
-   [ ] Recall@10 dibandingkan.
-   [ ] MAP dibandingkan.
-   [ ] NDCG@10 dibandingkan.
-   [ ] MRR dibandingkan.
-   [ ] Latency dibandingkan.
-   [ ] Evaluasi berdasarkan tipe query dilakukan.
-   [ ] Ablation experiment dilakukan.
-   [ ] Regression testing dilakukan.
-   [ ] Statistical test dilakukan jika ingin membuat klaim statistical
    significance.

------------------------------------------------------------------------

# 35. Definition of Done

Fitur dianggap selesai jika:

``` text
[ ] Tolerant Retrieval module berjalan
[ ] Exact retrieval tetap menjadi prioritas
[ ] Fallback mechanism berjalan
[ ] Typo correction berjalan
[ ] Fuzzy matching berjalan
[ ] Spelling variation berjalan
[ ] Abbreviation handling berjalan
[ ] Technical-term protection berjalan
[ ] Morphological variation berjalan
[ ] Cross-lingual tolerance berjalan
[ ] Confidence scoring berjalan
[ ] Candidate validation berjalan
[ ] Logging tersedia
[ ] Unit tests tersedia
[ ] Regression tests tersedia
[ ] Benchmark tersedia
[ ] Evaluation tersedia
[ ] Ablation tersedia
[ ] Dokumentasi konfigurasi tersedia
```

------------------------------------------------------------------------

# 36. Expected Final Pipeline

``` text
                         USER QUERY
                              │
                              ▼
                       QUERY ANALYSIS
                              │
                              ▼
                      EXACT RETRIEVAL
                              │
                    ┌─────────┴─────────┐
                    │                   │
                 ADEQUATE             POOR
                    │                   │
                    │                   ▼
                    │          TOLERANT RETRIEVAL
                    │                   │
                    │        ┌──────────┼──────────┐
                    │        │          │          │
                    │      TYPO       FUZZY    ABBREVIATION
                    │        │          │          │
                    │        ├──────────┼──────────┤
                    │        │          │          │
                    │    SPELLING   TECHNICAL  CROSS-LINGUAL
                    │    VARIATION    TERM
                    │        │          │
                    │        └──────────┼──────────┘
                    │                   │
                    │                   ▼
                    │           CANDIDATE VALIDATION
                    │                   │
                    │                   ▼
                    │            CONFIDENCE SCORING
                    │                   │
                    └───────────────────┤
                                        ▼
                                  BM25 RETRIEVAL
                                        │
                                        ▼
                              DOCUMENT AGGREGATION
                                        │
                                        ▼
                                  FINAL RANKING
                                        │
                                        ▼
                                     RESULTS
```

------------------------------------------------------------------------

# 37. Kesimpulan

Tolerant Retrieval cocok ditambahkan ke sistem academic IR karena corpus
akademik memiliki variasi typo, spelling, technical terms, abbreviation,
morphology, dan bahasa.

Namun fitur harus diterapkan sebagai **controlled retrieval
enhancement**, bukan fuzzy search tanpa batas.

Prinsip utama:

> **Exact retrieval first, tolerant retrieval as fallback, BM25 tetap
> sebagai retrieval engine, dan setiap peningkatan harus dibuktikan
> melalui eksperimen.**

Eksperimen utama:

``` text
BM25
   ↓
BM25 + Tolerant Retrieval
```

Evaluasi:

``` text
P@5
P@10
Recall@10
MAP
NDCG@10
MRR
Latency
```

dan analisis:

``` text
Normal Query
Typo Query
Technical Query
Abbreviation Query
Spelling Variation
Morphological Variation
Cross-Lingual Query
```

Dengan desain tersebut, Tolerant Retrieval menjadi bukan hanya fitur
tambahan, tetapi komponen yang dapat dievaluasi secara ilmiah.
