#!/usr/bin/env python3
"""
Academic IR System — Comprehensive Ground Truth (Qrels) Builder
===============================================================
Constructs graded relevance judgements (0-3) for all 33 evaluation queries (Q01-Q33)
based on evaluation/judging_guide.md and SQLite corpus content.

Scale:
  3 = Highly Relevant (primary target, comprehensive coverage)
  2 = Relevant (substantial coverage / related subtopic)
  1 = Marginally Relevant (mentions concepts, supporting context)

Output:
  evaluation/qrels.csv
"""

import sys
import csv
import sqlite3
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build_qrels():
    db_path = PROJECT_ROOT / "database" / "academic_ir.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    docs = c.execute("""
        SELECT document_id, document_type, title, abstract, course, 
               year, language, source, keywords
        FROM documents
    """).fetchall()

    print(f"Loaded {len(docs)} documents from database.")

    # Dictionary: query_id -> {document_id: relevance}
    qrels = {}

    def add_rel(qid, doc_id, score):
        if qid not in qrels:
            qrels[qid] = {}
        # Keep maximum score if duplicate
        qrels[qid][doc_id] = max(qrels[qid].get(doc_id, 0), score)

    for doc in docs:
        did = doc["document_id"]
        dtype = (doc["document_type"] or "").upper()
        title = (doc["title"] or "").lower()
        abstract = (doc["abstract"] or "").lower()
        course = (doc["course"] or "").lower()
        year = doc["year"] or 0
        text = f"{title} {abstract} {course}"

        # ── Q01: analisis perancangan sistem informasi use case diagram (A) ──
        if "analisis dan perancangan sistem informasi" in course or "perancangan sistem informasi" in course:
            if "use case" in text or "uml" in text or "diagram" in text:
                add_rel("Q01", did, 3)
            else:
                add_rel("Q01", did, 2)
        elif "sistem informasi" in text and ("use case" in text or "perancangan" in text):
            add_rel("Q01", did, 1)

        # ── Q02: work breakdown structure manajemen proyek teknologi informasi (A) ──
        if "manajemen proyek ti" in course or "manajemen proyek" in course:
            if "wbs" in text or "work breakdown" in text or "struktur" in text:
                add_rel("Q02", did, 3)
            else:
                add_rel("Q02", did, 2)
        elif "manajemen proyek" in text and "wbs" in text:
            add_rel("Q02", did, 2)

        # ── Q03: critical path method network diagram activity durasi (A) ──
        if "manajemen proyek ti" in course or "manajemen proyek" in course:
            if "cpm" in text or "critical path" in text or "network" in text or "penjadwalan" in text or "durasi" in text:
                add_rel("Q03", did, 3)
            else:
                add_rel("Q03", did, 2)

        # ── Q04: data mining business intelligence clustering classification (A) ──
        if "data mining and business intelligence" in course or "data mining" in course:
            add_rel("Q04", did, 3)
        elif "data mining" in text and ("clustering" in text or "klasifikasi" in text or "classification" in text):
            add_rel("Q04", did, 2)

        # ── Q05: aljabar linier matriks transformasi linier (A) ──
        if "aljabar" in course or "matematika" in course:
            add_rel("Q05", did, 3)
        elif "aljabar" in text or "matriks" in text:
            add_rel("Q05", did, 2)

        # ── Q06: pemrograman fungsional higher order function recursi (B) ──
        if "pemrograman fungsional" in course:
            add_rel("Q06", did, 3)
        elif "fungsional" in text or "recursion" in text or "rekursi" in text:
            add_rel("Q06", did, 2)

        # ── Q07: sistem operasi proses thread scheduling virtual memory (B) ──
        if "sistem operasi" in course:
            add_rel("Q07", did, 3)
        elif "sistem operasi" in text or "operating system" in text:
            add_rel("Q07", did, 2)

        # ── Q08: human computer interaction evaluasi usability antarmuka pengguna (B) ──
        if "sistem interaksi (human computer interaction)" in course or "hci" in course:
            add_rel("Q08", did, 3)
        elif "human computer interaction" in text or "usability" in text or "antarmuka pengguna" in text:
            add_rel("Q08", did, 2)

        # ── Q09: metodologi penelitian rumusan masalah tinjauan pustaka (B) ──
        if "metodologi penelitian" in course:
            add_rel("Q09", did, 3)
        elif "metodologi penelitian" in text or "tinjauan pustaka" in text:
            add_rel("Q09", did, 2)

        # ── Q10: arsitektur komputer instruction set pipeline cache memory (B) ──
        if "arsitektur komputer" in course:
            add_rel("Q10", did, 3)
        elif "arsitektur komputer" in text or "pipeline" in text or "cache" in text:
            add_rel("Q10", did, 2)

        # ── Q11: pembelajaran mesin supervised unsupervised neural network (B) ──
        if any(k in text for k in ["machine learning", "pembelajaran mesin", "neural network", "supervised", "unsupervised"]):
            if "machine learning" in title or "pembelajaran mesin" in title or "neural network" in title:
                add_rel("Q11", did, 3)
            else:
                add_rel("Q11", did, 2)

        # ── Q12: pengolahan citra digital segmentasi deteksi tepi (B) ──
        if any(k in text for k in ["citra", "image", "vision", "segmentasi", "deteksi tepi", "grafika", "visual", "kognisi"]):
            if "vision" in title or "image" in title or "citra" in title:
                add_rel("Q12", did, 3)
            elif "vision" in text or "image" in text or "citra" in text or "kognisi" in text:
                add_rel("Q12", did, 2)

        # ── Q13: analisis sentimen opini publik media sosial (B) ──
        if any(k in text for k in ["sentimen", "sentiment", "opini publik", "media sosial", "twitter"]):
            if "sentimen" in title or "sentiment" in title:
                add_rel("Q13", did, 3)
            else:
                add_rel("Q13", did, 2)

        # ── Q14: jaringan komputer TCP IP routing switching (B) ──
        if any(k in text for k in ["jaringan komputer", "computer network", "tcp", "routing", "switching"]):
            if "jaringan" in title or "network" in title:
                add_rel("Q14", did, 3)
            else:
                add_rel("Q14", did, 2)

        # ── Q15: TF-IDF vector space model cosine similarity temu kembali informasi (C) ──
        if any(k in text for k in ["temu kembali informasi", "information retrieval", "tf-idf", "tfidf", "vector space", "cosine similarity"]):
            if "temu kembali" in title or "retrieval" in title or "tf-idf" in title:
                add_rel("Q15", did, 3)
            else:
                add_rel("Q15", did, 2)

        # ── Q16: naive bayes support vector machine klasifikasi teks (C) ──
        if ("naive bayes" in text or "support vector machine" in text or "svm" in text) and ("klasifikasi" in text or "classification" in text):
            if "naive bayes" in title or "svm" in title or "support vector" in title:
                add_rel("Q16", did, 3)
            else:
                add_rel("Q16", did, 2)

        # ── Q17: K-means hierarchical clustering silhouette index (C) ──
        if "k-means" in text or "kmeans" in text or "hierarchical clustering" in text or "silhouette" in text:
            if "k-means" in title or "clustering" in title:
                add_rel("Q17", did, 3)
            else:
                add_rel("Q17", did, 2)

        # ── Q18: backpropagation gradient descent optimasi deep learning (C) ──
        if ("backpropagation" in text or "gradient descent" in text or "deep learning" in text) and "neural" in text:
            if "deep learning" in title or "backpropagation" in title:
                add_rel("Q18", did, 3)
            else:
                add_rel("Q18", did, 2)

        # ── Q19: random forest decision tree ensemble method akurasi (C) ──
        if "random forest" in text or "decision tree" in text or "ensemble" in text:
            if "random forest" in title or "decision tree" in title:
                add_rel("Q19", did, 3)
            else:
                add_rel("Q19", did, 2)

        # ── Q20: materi kuliah sistem operasi proses manajemen (D) ──
        if dtype == "MATERIAL" and "sistem operasi" in course:
            add_rel("Q20", did, 3)
        elif "sistem operasi" in course:
            add_rel("Q20", did, 2)

        # ── Q21: bahan ajar pemrograman web HTML CSS JavaScript (D) ──
        if dtype == "MATERIAL" and ("web" in text or "pemrograman" in course or "html" in text or "javascript" in text):
            add_rel("Q21", did, 3)
        elif "web" in text or "javascript" in text:
            add_rel("Q21", did, 2)

        # ── Q22: slide kuliah struktur data linked list tree graph (D) ──
        if dtype == "MATERIAL" and ("algoritma" in course or "pemrograman" in course or "struktur data" in text):
            add_rel("Q22", did, 3)
        elif "struktur data" in text or "linked list" in text or "algoritma" in text:
            add_rel("Q22", did, 2)

        # ── Q23: silabus mata kuliah kalkulus integral diferensial (D) ──
        if dtype == "MATERIAL" and ("kalkulus" in text or "matematika" in text or "fisika" in course):
            add_rel("Q23", did, 3)
        elif "integral" in text or "kalkulus" in text:
            add_rel("Q23", did, 2)

        # ── Q24: buku rancangan pengajaran basis data relasional SQL (D) ──
        if dtype == "MATERIAL" and ("basis data" in text or "database" in text or "sql" in text or "sistem informasi" in course):
            add_rel("Q24", did, 3)
        elif "basis data" in text or "database" in text or "sql" in text:
            add_rel("Q24", did, 2)

        # ── Q25: data clustering (E - Cross-lingual) ──
        if "clustering" in text or "cluster" in text or "pengelompokan" in text:
            if "clustering" in title or "cluster" in title:
                add_rel("Q25", did, 3)
            else:
                add_rel("Q25", did, 2)

        # ── Q26: sentiment analysis (E - Cross-lingual) ──
        if "sentiment" in text or "sentimen" in text:
            if "sentiment" in title or "sentimen" in title:
                add_rel("Q26", did, 3)
            else:
                add_rel("Q26", did, 2)

        # ── Q27: information retrieval ranking (E - Cross-lingual) ──
        if "information retrieval" in text or "temu kembali informasi" in text or ("retrieval" in text and "ranking" in text):
            if "retrieval" in title or "temu kembali" in title:
                add_rel("Q27", did, 3)
            else:
                add_rel("Q27", did, 2)

        # ── Q28: machine learning classification (E - Cross-lingual) ──
        if ("machine learning" in text or "pembelajaran mesin" in text) and ("classification" in text or "klasifikasi" in text):
            if "classification" in title or "klasifikasi" in title or "machine learning" in title:
                add_rel("Q28", did, 3)
            else:
                add_rel("Q28", did, 2)

        # ── Q29: natural language processing text mining (E - Cross-lingual) ──
        if "nlp" in text or "natural language" in text or "text mining" in text or "pemrosesan bahasa alami" in text:
            if "nlp" in title or "text mining" in title or "natural language" in title:
                add_rel("Q29", did, 3)
            else:
                add_rel("Q29", did, 2)

        # ── Q30: skripsi analisis sentimen media sosial 2023 (F - Constrained) ──
        if dtype == "THESIS":
            if ("sentimen" in text or "sentiment" in text):
                if year == 2023:
                    add_rel("Q30", did, 3)
                else:
                    add_rel("Q30", did, 2)
            elif ("temu kembali" in text or "teks" in text or "retrieval" in text) and year in [2022, 2023]:
                add_rel("Q30", did, 2)
        elif ("sentimen" in text or "sentiment" in text) and year == 2023:
            add_rel("Q30", did, 2)

        # ── Q31: tesis machine learning prediksi penyakit (F - Constrained) ──
        if dtype == "THESIS" and ("machine learning" in text or "klasifikasi" in text or "prediksi" in text or "penyakit" in text or "medis" in text):
            if ("prediksi" in text or "penyakit" in text or "klasifikasi" in text) and ("machine learning" in text or "learning" in text):
                add_rel("Q31", did, 3)
            else:
                add_rel("Q31", did, 2)

        # ── Q32: jurnal penelitian deep learning image recognition 2024 (F - Constrained) ──
        if dtype == "RESEARCH" and ("deep learning" in text or "citra" in text or "image" in text or "cnn" in text):
            if year == 2024:
                add_rel("Q32", did, 3)
            elif year in [2023, 2022]:
                add_rel("Q32", did, 2)
            else:
                add_rel("Q32", did, 1)

        # ── Q33: materi kuliah kedokteran bioengineering (F - Constrained) ──
        if dtype == "MATERIAL" and any(k in course for k in ["bioengineering", "biologi", "kedokteran", "kesehatan", "farmasi", "gizi"]):
            add_rel("Q33", did, 3)
        elif any(k in text for k in ["bioengineering", "biologi sel", "biomedis"]):
            add_rel("Q33", did, 2)

    # Write to evaluation/qrels.csv
    out_path = PROJECT_ROOT / "evaluation" / "qrels.csv"
    total_judgements = 0
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["query_id", "document_id", "relevance"])
        writer.writeheader()
        for qid in sorted(qrels.keys()):
            for did, rel in sorted(qrels[qid].items()):
                writer.writerow({"query_id": qid, "document_id": did, "relevance": rel})
                total_judgements += 1

    print(f"\nSuccessfully wrote {total_judgements} judgments across {len(qrels)} queries to {out_path}.")
    for qid in sorted(qrels.keys()):
        counts = {}
        for rel in qrels[qid].values():
            counts[rel] = counts.get(rel, 0) + 1
        print(f"  {qid}: {len(qrels[qid])} judgements (score 3: {counts.get(3, 0)}, score 2: {counts.get(2, 0)}, score 1: {counts.get(1, 0)})")

if __name__ == "__main__":
    build_qrels()
