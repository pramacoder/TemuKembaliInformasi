"""
Academic IR System — Interactive Web Application
=================================================
Modern Streamlit interface supporting:
1. Academic Search with field-aware chunk retrieval & snippet highlights
2. Proposal Similarity & Originality Checker
3. Corpus Analytics & Collection Health
4. IR Evaluation Benchmark Viewer
"""

import sys
import os
import json
import time
from pathlib import Path
import streamlit as st

# Setup sys.path for academic-ir imports
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.indexing.tfidf import TFIDFIndex
from src.preprocessing.pipeline import PreprocessingPipeline
from src.retrieval.search import SearchEngine
from src.retrieval.ranking import rank_results
from src.retrieval.snippet import generate_snippet
from src.similarity.proposal import ProposalSimilarityEngine
from src.extraction.pdf import extract_pdf

# ─── Page Configuration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="Academic IR — Temu Kembali Informasi",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Premium Design ───────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0 0 0.5rem 0;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.05rem;
        margin: 0;
    }

    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
    }

    .result-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .result-card:hover {
        border-left-color: #1d4ed8;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
    }
    .result-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.4rem;
    }
    .result-meta {
        font-size: 0.875rem;
        color: #64748b;
        margin-bottom: 0.75rem;
    }
    .result-snippet {
        background-color: #f8fafc;
        border: 1px solid #f1f5f9;
        border-radius: 8px;
        padding: 0.85rem;
        font-size: 0.925rem;
        color: #334155;
        line-height: 1.6;
    }
    .result-snippet mark {
        background-color: #fef08a;
        color: #854d0e;
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
        font-weight: 600;
    }
    
    .badge-material {
        background-color: #dbeafe;
        color: #1d4ed8;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-research {
        background-color: #dcfce7;
        color: #15803d;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-thesis {
        background-color: #fef3c7;
        color: #b45309;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-score {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# ─── Resource Caching ─────────────────────────────────────────────────────────

@st.cache_resource
def get_database():
    db_path = PROJECT_ROOT / "database" / "academic_ir.db"
    db = Database(str(db_path))
    db.initialize()
    return db


@st.cache_resource
def get_index():
    models_dir = PROJECT_ROOT / "models"
    if (models_dir / "tfidf_vectorizer.pkl").exists():
        index = TFIDFIndex()
        index.load(str(models_dir))
        return index
    return None


@st.cache_resource
def get_pipeline():
    return PreprocessingPipeline(default_language="id")


# ─── Sidebar Controls ─────────────────────────────────────────────────────────

db = get_database()
tfidf_index = get_index()
pipeline = get_pipeline()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Universitas_Indonesia_logo.svg/1200px-Universitas_Indonesia_logo.svg.png", width=70)
    st.title("Academic IR")
    st.caption("Information Retrieval & Similarity System")
    st.divider()

    st.subheader("⚙️ Parameter Pencarian")
    corpus_filter = st.selectbox(
        "Tipe Korpus:",
        ["Semua Korpus", "Materi Kuliah (MATERIAL)", "Penelitian (RESEARCH)", "Skripsi/Tesis (THESIS)"],
    )
    
    # Map to DB document_type
    doc_type_map = {
        "Semua Korpus": None,
        "Materi Kuliah (MATERIAL)": "MATERIAL",
        "Penelitian (RESEARCH)": "RESEARCH",
        "Skripsi/Tesis (THESIS)": "THESIS",
    }
    selected_doc_type = doc_type_map[corpus_filter]

    lang_filter = st.selectbox(
        "Bahasa:",
        ["Semua Bahasa", "Indonesia (id)", "English (en)"]
    )
    lang_map = {
        "Semua Bahasa": None,
        "Indonesia (id)": "id",
        "English (en)": "en"
    }
    selected_lang = lang_map[lang_filter]

    top_k = st.slider("Jumlah Hasil (Top-K):", min_value=3, max_value=30, value=10, step=1)
    
    rerank_toggle = st.checkbox("Gunakan Field-Aware Re-ranking", value=True,
                                help="Menggabungkan skor kemiripan teks (60%) dengan bobot judul (20%) dan metadata (20%)")

    st.divider()
    st.markdown("### 📊 Status Sistem")
    if tfidf_index:
        st.success(f"✓ Indeks Aktif ({len(tfidf_index.chunk_ids):,} chunks)")
    else:
        st.warning("⚠️ Indeks belum dibangun. Jalankan `scripts/build_index.py`.")


# ─── Main Tabs Navigation ────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Pencarian Dokumen",
    "📑 Uji Kemiripan Proposal",
    "📈 Statistik Korpus",
    "🧪 Evaluasi Retrieval",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: PENCARIAN DOKUMEN (ACADEMIC SEARCH)
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Pencarian Dokumen Akademik</h1>
        <p>Temukan materi perkuliahan, artikel penelitian, dan skripsi dengan pencarian berbasis representasi VSM (TF-IDF) & Cosine Similarity tingkat chunk.</p>
    </div>
    """, unsafe_allow_html=True)

    search_query = st.text_input(
        "Masukkan kata kunci atau pertanyaan akademik:",
        placeholder="contoh: work breakdown structure dalam manajemen proyek perangkat lunak...",
        key="search_input"
    )

    col_btn, col_sample = st.columns([1, 4])
    with col_btn:
        search_clicked = st.button("Cari Dokumen", type="primary", use_container_width=True)
    with col_sample:
        sample_choice = st.selectbox(
            "Coba query contoh:",
            [
                "-- Pilih Query Contoh --",
                "analisis perancangan sistem informasi use case",
                "critical path method network diagram activity durasi",
                "data mining business intelligence clustering classification",
                "aljabar linier matriks transformasi linier eigenvalue",
                "sistem operasi proses thread scheduling virtual memory",
                "metodologi penelitian kuantitatif kualitatif rumusan masalah",
            ],
            key="sample_query"
        )

    active_query = search_query
    if sample_choice != "-- Pilih Query Contoh --" and not search_query:
        active_query = sample_choice

    if active_query:
        if not tfidf_index:
            st.error("Indeks TF-IDF belum ditemukan. Silakan jalankan `python scripts/build_index.py` terlebih dahulu.")
        else:
            with st.spinner("Mencari dokumen relevan di seluruh korpus..."):
                start_time = time.time()
                search_engine = SearchEngine(tfidf_index, db, pipeline)

                raw_results = search_engine.search(
                    query=active_query,
                    top_k=top_k * 2 if rerank_toggle else top_k,
                    document_type=selected_doc_type,
                    language=selected_lang,
                )

                if rerank_toggle:
                    results = rank_results(raw_results, active_query)[:top_k]
                else:
                    results = raw_results[:top_k]

                search_time = time.time() - start_time

            st.markdown(f"**Menemukan {len(results)} hasil relevan** dalam `{search_time:.3f}` detik untuk *\"{active_query}\"*")
            st.write("")

            if not results:
                st.info("Tidak ada dokumen yang cocok dengan kriteria pencarian dan filter Anda.")
            else:
                for idx, res in enumerate(results, 1):
                    doc_type = res.get("document_type", "MATERIAL")
                    badge_class = f"badge-{doc_type.lower()}"
                    score_pct = res.get("score", 0.0) * 100
                    course = res.get("course") or res.get("institution") or "Umum"
                    authors = res.get("authors") or "—"
                    page_info = f"Hal. {res.get('page_start')}" if res.get('page_start') else ""

                    # Generate highlighted snippet
                    snippet_html = generate_snippet(res.get("raw_text", ""), active_query, max_chars=260)

                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <span class="{badge_class}">{doc_type}</span>
                                <span style="margin-left: 0.5rem; font-size: 0.8rem; color: #64748b;">ID: {res.get('document_id')} | {page_info}</span>
                                <div class="result-title" style="margin-top: 0.5rem;">{idx}. {res.get('title', 'Tanpa Judul')}</div>
                            </div>
                            <span class="badge-score">{score_pct:.1f}% Match</span>
                        </div>
                        <div class="result-meta">
                            📚 <b>Mata Kuliah:</b> {course} &nbsp;•&nbsp; ✍️ <b>Penulis:</b> {authors}
                        </div>
                        <div class="result-snippet">
                            {snippet_html}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"Lihat detail chunk lengkap & metadata ({res.get('chunk_id')})"):
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            st.write(f"**Chunk ID:** `{res.get('chunk_id')}`")
                            st.write(f"**Halaman:** {res.get('page_start')} s/d {res.get('page_end')}")
                            st.write(f"**Bahasa:** `{res.get('language')}`")
                        with c2:
                            st.write(f"**Sumber Asli:** [{res.get('source')} Link]({res.get('source_url', '#')})")
                            st.write(f"**Path File Lokal:** `{res.get('local_path', '')}`")
                        
                        st.markdown("**Teks Utuh Chunk:**")
                        st.text_area("Chunk Text", res.get("raw_text", ""), height=150, key=f"area_{res.get('chunk_id')}", disabled=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: UJI KEMIRIPAN PROPOSAL (PROPOSAL SIMILARITY)
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("""
    <div class="main-header">
        <h1>📑 Uji Kemiripan & Orisinalitas Proposal</h1>
        <p>Bandingkan draf proposal penelitian atau tugas akhir dengan korpus referensi akademik untuk mendeteksi topik serumpun, referensi relevan, dan potensi redundansi.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input1, col_input2 = st.columns([1, 1])

    with col_input1:
        st.subheader("1. Unggah Berkas Proposal")
        uploaded_file = st.file_uploader("Pilih file PDF proposal:", type=["pdf"])
        
    with col_input2:
        st.subheader("2. Atau Tempelkan Teks Proposal")
        pasted_text = st.text_area("Tempelkan draf bab pengantar / metodologi proposal:", height=180,
                                   placeholder="Tuliskan latar belakang masalah, tujuan penelitian, atau metodologi yang diusulkan di sini...")

    analyze_btn = st.button("Analisis Kemiripan Proposal", type="primary", use_container_width=True)

    if analyze_btn:
        proposal_content = ""
        proposal_source_name = ""

        if uploaded_file is not None:
            with st.spinner("Mengekstraksi teks dari berkas PDF proposal..."):
                # Save temp file
                temp_path = PROJECT_ROOT / "data" / "temp_proposal.pdf"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                extract_res = extract_pdf(str(temp_path))
                proposal_content = extract_res.full_text
                proposal_source_name = uploaded_file.name
                temp_path.unlink(missing_ok=True)
        elif pasted_text.strip():
            proposal_content = pasted_text.strip()
            proposal_source_name = "Teks Input Pengguna"

        if not proposal_content or len(proposal_content.split()) < 20:
            st.warning("Mohon sediakan teks proposal yang memadai (minimal 20 kata).")
        elif not tfidf_index:
            st.error("Indeks TF-IDF belum dibangun. Silakan jalankan `python scripts/build_index.py`.")
        else:
            with st.spinner("Memproses vektor proposal dan menghitung matriks cosine similarity..."):
                start_p_time = time.time()
                sim_engine = ProposalSimilarityEngine(tfidf_index, db, pipeline)
                sim_result = sim_engine.analyze_text(proposal_content, top_k=top_k)
                p_elapsed = time.time() - start_p_time

            # Display Analysis Summary Cards
            st.markdown("### 📊 Ringkasan Analisis Orisinalitas")
            sc1, sc2, sc3, sc4 = st.columns(4)

            max_sim = sim_result.get("max_similarity", 0.0) * 100
            mean_sim = sim_result.get("mean_top_k_similarity", 0.0) * 100
            orig_score = max(0.0, 100.0 - max_sim)

            with sc1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Indeks Orisinalitas</div>
                    <div class="metric-value" style="color: {'#16a34a' if orig_score > 60 else '#dc2626'};">{orig_score:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with sc2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Kemiripan Puncak</div>
                    <div class="metric-value" style="color: {'#dc2626' if max_sim > 40 else '#2563eb'};">{max_sim:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with sc3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Rata-rata Top-K</div>
                    <div class="metric-value">{mean_sim:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with sc4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Waktu Komputasi</div>
                    <div class="metric-value">{p_elapsed:.2f}s</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("")
            st.markdown("### 📚 Dokumen & Bab Rujukan Paling Serupa")

            similar_docs = sim_result.get("similar_chunks", [])
            for s_idx, s_doc in enumerate(similar_docs, 1):
                s_score = s_doc.get("score", 0.0) * 100
                doc_t = s_doc.get("document_type", "MATERIAL")
                
                st.markdown(f"""
                <div class="result-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <span class="badge-{doc_t.lower()}">{doc_t}</span>
                            <span style="font-size: 0.85rem; color: #64748b; margin-left: 0.5rem;">{s_doc.get('document_id')} (Hal. {s_doc.get('page_start', 1)})</span>
                            <div class="result-title" style="margin-top: 0.4rem;">{s_idx}. {s_doc.get('title', 'Dokumen')}</div>
                        </div>
                        <span class="badge-score">{s_score:.1f}% Kemiripan</span>
                    </div>
                    <div class="result-meta">
                        Mata Kuliah / Institusi: <b>{s_doc.get('course') or s_doc.get('institution')}</b>
                    </div>
                    <div class="result-snippet">
                        {s_doc.get('raw_text', '')[:300]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: STATISTIK KORPUS (CORPUS ANALYTICS)
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("""
    <div class="main-header">
        <h1>📈 Statistik & Kesehatan Korpus Data</h1>
        <p>Pemantauan distribusi data dari OpenCourseWare UI, CORE API, DOAJ, dan Repositori Institusi.</p>
    </div>
    """, unsafe_allow_html=True)

    stats = db.get_corpus_stats()
    
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Dokumen</div>
            <div class="metric-value">{stats.get('total_documents', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    with mc2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Halaman PDF</div>
            <div class="metric-value">{stats.get('total_pages', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    with mc3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Unit Chunk</div>
            <div class="metric-value">{stats.get('total_chunks', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    with mc4:
        vocab_len = len(tfidf_index.vocabulary) if tfidf_index else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Kosakata Fitur TF-IDF</div>
            <div class="metric-value">{vocab_len:,}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.divider()

    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.subheader("Distribusi Berdasarkan Tipe Dokumen")
        by_type = stats.get("by_type", {})
        if by_type:
            st.bar_chart(by_type)
        else:
            st.info("Belum ada data dokumen.")

    with c_col2:
        st.subheader("Distribusi Berdasarkan Bahasa")
        by_lang = stats.get("by_language", {})
        if by_lang:
            st.bar_chart(by_lang)
        else:
            st.info("Belum ada data bahasa.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: EVALUASI RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.markdown("""
    <div class="main-header">
        <h1>🧪 Evaluasi Kinerja Information Retrieval</h1>
        <p>Pengukuran efektivitas temu kembali informasi menggunakan metrik standar akademik: Precision@K, MAP, dan NDCG@10.</p>
    </div>
    """, unsafe_allow_html=True)

    eval_report_file = PROJECT_ROOT / "data" / "reports" / "evaluation_results.json"
    if eval_report_file.exists():
        with open(eval_report_file, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

        agg = eval_data.get("aggregate", {})
        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            st.metric("MAP (Mean Average Precision)", f"{agg.get('MAP', 0.0):.4f}")
        with ec2:
            st.metric("Rata-rata P@5", f"{agg.get('Avg_P@5', 0.0):.4f}")
        with ec3:
            st.metric("Rata-rata P@10", f"{agg.get('Avg_P@10', 0.0):.4f}")
        with ec4:
            st.metric("Rata-rata NDCG@10", f"{agg.get('Avg_NDCG@10', 0.0):.4f}")

        st.divider()
        st.subheader("Rincian Hasil Evaluasi per Query Benchmark")
        
        per_query = eval_data.get("per_query", {})
        table_rows = []
        for q_id, q_m in per_query.items():
            table_rows.append({
                "Query ID": q_id,
                "P@5": q_m.get("P@5", 0.0),
                "P@10": q_m.get("P@10", 0.0),
                "R@10": q_m.get("R@10", 0.0),
                "NDCG@10": q_m.get("NDCG@10", 0.0),
                "Average Precision (AP)": q_m.get("AP", 0.0),
            })
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("Laporan evaluasi belum digenerate. Klik tombol di bawah atau jalankan `python scripts/run_evaluation.py`.")
        if st.button("Jalankan Evaluasi Benchmark Sekarang"):
            st.info("Jalankan `python scripts/run_evaluation.py` dari CLI untuk menghasilkan evaluasi.")
