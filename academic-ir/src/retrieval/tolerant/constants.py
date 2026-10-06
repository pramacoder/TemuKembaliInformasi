"""
Tolerant Retrieval — Constants & Dictionaries
=============================================
Defines dictionaries, abbreviations, protected terms, and default configurations
in accordance with README_Tolerant_Retrieval.md.
"""

from typing import Dict, List, Set

# Section 21: Configuration defaults
DEFAULT_CONFIG = {
    "enabled": True,
    "fallback_only": True,  # Exact-first: only trigger if exact match is inadequate
    "typo": {
        "enabled": True,
        "min_confidence": 0.82,
        "max_edit_distance": 2,
    },
    "fuzzy": {
        "enabled": True,
        "similarity_threshold": 0.82,
        "max_candidates": 3,
    },
    "abbreviation": {
        "enabled": True,
        "min_confidence": 0.95,
        "expand": True,
    },
    "spelling_variation": {
        "enabled": True,
        "min_confidence": 0.90,
    },
    "technical_terms": {
        "enabled": True,
        "protect_terms": True,
    },
    "morphology": {
        "enabled": True,
        "min_confidence": 0.85,
    },
    "cross_lingual": {
        "enabled": True,
        "min_confidence": 0.90,
    },
    "fallback": {
        "min_adequate_results": 3,
        "min_top_score_bm25": 1.0,
        "min_top_score_tfidf": 0.10,
    },
    "ranking": {
        "exact_match_priority": True,
    },
}

# Section 9 & 30: Protected Technical Terms (Never modify, split, or fuzzy-replace)
PROTECTED_TERMS: Set[str] = {
    "c++",
    "c#",
    ".net",
    "r²",
    "r2",
    "tf-idf",
    "tfidf",
    "bert-base",
    "roberta",
    "gpt-4",
    "gpt-3.5",
    "llama-2",
    "llama-3",
    "cnn-bilstm",
    "tcp/ip",
    "wi-fi",
    "ipv4",
    "ipv6",
    "k-means",
    "k-nearest",
    "node.js",
    "next.js",
    "vue.js",
    "react.js",
    "o(n log n)",
    "o(n)",
    "o(1)",
    "o(n^2)",
}

# Section 8: Academic and Computer Science Abbreviations
# Mappings from acronym (lowercase) to canonical term and display info
ABBREVIATIONS: Dict[str, Dict[str, any]] = {
    "nlp": {
        "canonical": "natural language processing",
        "indonesian": "pemrosesan bahasa alami",
        "confidence": 0.99,
    },
    "ir": {
        "canonical": "information retrieval",
        "indonesian": "temu kembali informasi",
        "confidence": 0.95,
    },
    "ml": {
        "canonical": "machine learning",
        "indonesian": "pembelajaran mesin",
        "confidence": 0.98,
    },
    "ai": {
        "canonical": "artificial intelligence",
        "indonesian": "kecerdasan buatan",
        "confidence": 0.98,
    },
    "cv": {
        "canonical": "computer vision",
        "indonesian": "pengolahan citra komputer",
        "confidence": 0.95,
    },
    "svm": {
        "canonical": "support vector machine",
        "indonesian": "mesin vektor pendukung",
        "confidence": 0.99,
    },
    "cnn": {
        "canonical": "convolutional neural network",
        "indonesian": "jaringan saraf konvolusional",
        "confidence": 0.99,
    },
    "rnn": {
        "canonical": "recurrent neural network",
        "indonesian": "jaringan saraf berulang",
        "confidence": 0.99,
    },
    "lstm": {
        "canonical": "long short-term memory",
        "indonesian": "long short-term memory",
        "confidence": 0.99,
    },
    "bilstm": {
        "canonical": "bidirectional long short-term memory",
        "indonesian": "bilstm",
        "confidence": 0.99,
    },
    "ann": {
        "canonical": "artificial neural network",
        "indonesian": "jaringan saraf tiruan",
        "confidence": 0.98,
    },
    "dnn": {
        "canonical": "deep neural network",
        "indonesian": "jaringan saraf dalam",
        "confidence": 0.98,
    },
    "knn": {
        "canonical": "k-nearest neighbors",
        "indonesian": "k-nearest neighbors",
        "confidence": 0.98,
    },
    "pca": {
        "canonical": "principal component analysis",
        "indonesian": "analisis komponen utama",
        "confidence": 0.98,
    },
    "lda": {
        "canonical": "linear discriminant analysis",
        "indonesian": "linear discriminant analysis",
        "confidence": 0.95,
    },
    "ner": {
        "canonical": "named entity recognition",
        "indonesian": "pengenalan entitas bernama",
        "confidence": 0.98,
    },
    "vsm": {
        "canonical": "vector space model",
        "indonesian": "model ruang vektor",
        "confidence": 0.98,
    },
    "brp": {
        "canonical": "buku rancangan pengajaran",
        "indonesian": "buku rancangan pengajaran",
        "confidence": 0.99,
    },
    "ocw": {
        "canonical": "opencourseware",
        "indonesian": "bahan ajar terbuka",
        "confidence": 0.99,
    },
    "so": {
        "canonical": "sistem operasi",
        "indonesian": "sistem operasi",
        "confidence": 0.96,
    },
    "jarkom": {
        "canonical": "jaringan komputer",
        "indonesian": "jaringan komputer",
        "confidence": 0.99,
    },
    "imk": {
        "canonical": "interaksi manusia dan komputer",
        "indonesian": "interaksi manusia dan komputer",
        "confidence": 0.99,
    },
    "hci": {
        "canonical": "human-computer interaction",
        "indonesian": "interaksi manusia komputer",
        "confidence": 0.98,
    },
    "apsi": {
        "canonical": "analisis dan perancangan sistem informasi",
        "indonesian": "analisis dan perancangan sistem informasi",
        "confidence": 0.99,
    },
    "manpro": {
        "canonical": "manajemen proyek teknologi informasi",
        "indonesian": "manajemen proyek",
        "confidence": 0.99,
    },
    "wbs": {
        "canonical": "work breakdown structure",
        "indonesian": "work breakdown structure",
        "confidence": 0.99,
    },
    "cpm": {
        "canonical": "critical path method",
        "indonesian": "metode jalur kritis",
        "confidence": 0.99,
    },
    "dbms": {
        "canonical": "database management system",
        "indonesian": "sistem manajemen basis data",
        "confidence": 0.99,
    },
    "rdbms": {
        "canonical": "relational database management system",
        "indonesian": "sistem basis data relasional",
        "confidence": 0.99,
    },
    "sql": {
        "canonical": "structured query language",
        "indonesian": "basis data sql",
        "confidence": 0.98,
    },
    "sdlc": {
        "canonical": "software development life cycle",
        "indonesian": "siklus hidup pengembangan perangkat lunak",
        "confidence": 0.99,
    },
    "uml": {
        "canonical": "unified modeling language",
        "indonesian": "diagram uml",
        "confidence": 0.99,
    },
    "oop": {
        "canonical": "object-oriented programming",
        "indonesian": "pemrograman berorientasi objek",
        "confidence": 0.99,
    },
    "iot": {
        "canonical": "internet of things",
        "indonesian": "internet of things",
        "confidence": 0.99,
    },
    "llm": {
        "canonical": "large language model",
        "indonesian": "model bahasa besar",
        "confidence": 0.98,
    },
    "bert": {
        "canonical": "bidirectional encoder representations from transformers",
        "indonesian": "model bert",
        "confidence": 0.98,
    },
    "gan": {
        "canonical": "generative adversarial network",
        "indonesian": "generative adversarial network",
        "confidence": 0.98,
    },
    "er": {
        "canonical": "entity relationship",
        "indonesian": "hubungan entitas",
        "confidence": 0.92,
    },
    "erd": {
        "canonical": "entity relationship diagram",
        "indonesian": "diagram entitas relasi",
        "confidence": 0.99,
    },
}

# Section 7: Common Spelling Variations (Indonesian & English academic variations)
# Non-standard / alternative spelling -> Standard canonical term
SPELLING_VARIATIONS: Dict[str, str] = {
    # Indonesian non-standard vs standard KBBI
    "analisa": "analisis",
    "analisi": "analisis",
    "metoda": "metode",
    "praktek": "praktik",
    "sistim": "sistem",
    "katagori": "kategori",
    "teoria": "teori",
    "kualitet": "kualitas",
    "jadual": "jadwal",
    "hirarki": "hierarki",
    "otentikasi": "autentikasi",
    "aktiviti": "aktivitas",
    "efektifitas": "efektivitas",
    "kreatifitas": "kreativitas",
    "rekayasaa": "rekayasa",
    "algoritm": "algoritma",
    "algoritme": "algoritma",
    "strukturdata": "struktur data",
    "basisdata": "basis data",
    "databasis": "basis data",
    "teksmining": "text mining",
    "mesinlearning": "machine learning",
    "deeplearning": "deep learning",
    "datamining": "data mining",
    
    # English UK vs US spelling
    "optimisation": "optimization",
    "optimising": "optimizing",
    "modelling": "modeling",
    "behaviour": "behavior",
    "normalisation": "normalization",
    "summarisation": "summarization",
    "categorisation": "categorization",
    "vectorisation": "vectorization",
    "generalisation": "generalization",
    "prioritisation": "prioritization",
}

# Section 9: Compound technical term canonicalization
TECHNICAL_PHRASES: Dict[str, str] = {
    "tf idf": "tf-idf",
    "tf/idf": "tf-idf",
    "tfidf": "tf-idf",
    "cnn bilstm": "cnn-bilstm",
    "cnn-bi-lstm": "cnn-bilstm",
    "k means": "k-means",
    "kmeans": "k-means",
    "k-nn": "knn",
    "decision trees": "decision tree",
    "support vector machines": "support vector machine",
    "neural networks": "neural network",
    "deep neural networks": "deep neural network",
    "recurrent neural networks": "recurrent neural network",
    "convolutional neural networks": "convolutional neural network",
    "usecase": "use case",
    "use case diagram": "use case diagram",
    "activity diagram": "activity diagram",
    "class diagram": "class diagram",
    "sequence diagram": "sequence diagram",
}

# Section 10: Morphological variation pairs (stem <-> inflections)
MORPHOLOGICAL_VARIANTS: Dict[str, str] = {
    "clustering": "cluster",
    "cluster": "clustering",
    "classification": "classify",
    "mengklasifikasikan": "klasifikasi",
    "terklasifikasi": "klasifikasi",
    "pengklasifikasian": "klasifikasi",
    "memprediksi": "prediksi",
    "prediksi": "prediksi",
    "perancangan": "rancang",
    "merancang": "rancang",
    "pengelompokan": "kelompok",
    "mengelompokkan": "kelompok",
    "pengujian": "uji",
    "menguji": "uji",
    "teruji": "uji",
    "pengolahan": "olah",
    "mengolah": "olah",
    "penerapan": "terap",
    "menerapkan": "terap",
}
