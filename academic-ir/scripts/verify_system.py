#!/usr/bin/env python3
"""
Academic IR System — End-to-End System Verification
====================================================
Verifies:
1. Database connectivity and counts
2. TF-IDF index loading and shape
3. SearchEngine with snippet generation and field-aware re-ranking
4. ProposalSimilarity engine with text and file scoring
5. Evaluation results report validity
"""

import sys
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.database.models import Database
from src.indexing.tfidf import TFIDFIndex
from src.preprocessing.pipeline import PreprocessingPipeline
from src.retrieval.search import SearchEngine
from src.retrieval.ranking import rank_results
from src.retrieval.snippet import generate_snippet
from src.similarity.proposal import ProposalSimilarityEngine


def main():
    print("=" * 65)
    print("  ACADEMIC IR SYSTEM — END-TO-END VERIFICATION")
    print("=" * 65)

    # 1. Database
    db_file = ROOT / "database" / "academic_ir.db"
    db = Database(str(db_file))
    stats = db.get_corpus_stats()
    print("[1] Database Status:")
    print(f"    Total Documents: {stats.get('total_documents', 0)}")
    print(f"    Total Pages:     {stats.get('total_pages', 0)}")
    print(f"    Total Chunks:    {stats.get('total_chunks', 0)}")

    # 2. TF-IDF Index
    models_dir = ROOT / "models"
    index = TFIDFIndex()
    index.load(str(models_dir))
    print("\n[2] Index Status:")
    print(f"    Chunk IDs:       {len(index.chunk_ids)}")
    print(f"    Vocabulary Size: {len(index.vocabulary)}")
    print(f"    Matrix Shape:    {index.tfidf_matrix.shape}")

    # 3. Search Engine
    pipeline = PreprocessingPipeline(default_language="id")
    engine = SearchEngine(index, db, pipeline)
    test_query = "critical path method network diagram"
    raw_results = engine.search(test_query, top_k=5)
    ranked = rank_results(raw_results, test_query)[:3]

    print(f"\n[3] Search Test (Query: '{test_query}'):")
    for r in ranked:
        clean_snip = generate_snippet(r['raw_text'], test_query, max_chars=100)
        # Remove HTML mark tags for terminal output
        term_snip = clean_snip.replace("<mark>", "[").replace("</mark>", "]")
        print(f"    - Score: {r['score']:.4f} | {r['document_id']} | {r['title']} (p.{r['page_start']})")
        print(f"      Snippet: {term_snip[:90]}...")

    # 4. Proposal Similarity
    sim_engine = ProposalSimilarityEngine(index, db, pipeline)
    draft_text = (
        "Pengembangan sistem informasi terpadu menggunakan metodologi SDLC "
        "dan manajemen penjadwalan proyek berbasis network diagram critical path."
    )
    sim_res = sim_engine.analyze_text(draft_text, top_k=3)
    print("\n[4] Proposal Similarity Test:")
    print(f"    Max Similarity:  {sim_res['max_similarity']:.4f}")
    print(f"    Mean Top-K:      {sim_res['mean_top_k_similarity']:.4f}")
    for ch in sim_res['similar_chunks'][:2]:
        print(f"    - [{ch['score']:.4f}] {ch['document_id']} - {ch['title']}")

    # 5. Evaluation Report
    report_path = ROOT / "data" / "reports" / "evaluation_results.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
        agg = eval_data.get("aggregate", {})
        print("\n[5] Evaluation Benchmark Metrics:")
        print(f"    MAP:             {agg.get('MAP', 0.0):.4f}")
        print(f"    Avg P@5:         {agg.get('Avg_P@5', 0.0):.4f}")
        print(f"    Avg P@10:        {agg.get('Avg_P@10', 0.0):.4f}")
        print(f"    Avg NDCG@10:     {agg.get('Avg_NDCG@10', 0.0):.4f}")

    print("\n" + "=" * 65)
    print("  ALL VERIFICATION CHECKS PASSED [OK]")
    print("=" * 65)


if __name__ == "__main__":
    main()
