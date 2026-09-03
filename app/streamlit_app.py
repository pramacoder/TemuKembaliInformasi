import streamlit as st
import os
import sys
import sqlite3

# Add src to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "src"))

from retrieval.search import SearchEngine
from retrieval.ranking import get_metadata

st.set_page_config(
    page_title="Penelusur Arsip Akademik",
    page_icon="📚",
    layout="wide"
)

# --- CSS for styling ---
st.markdown("""
<style>
    .stTextInput > div > div > input {
        font-size: 1.2rem;
        padding: 10px;
    }
    .result-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #0052cc;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .dark-mode .result-card {
        background-color: #1e1e1e;
        border-left: 5px solid #4d90fe;
    }
    .result-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 5px;
        color: #0052cc;
    }
    .dark-mode .result-title {
        color: #4d90fe;
    }
    .result-meta {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 10px;
    }
    .sim-score {
        background-color: #e9ecef;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .dark-mode .sim-score {
        background-color: #333;
        color: #ddd;
    }
    .link-btn {
        display: inline-block;
        padding: 5px 15px;
        background-color: #0052cc;
        color: white !important;
        text-decoration: none;
        border-radius: 5px;
        font-size: 0.9rem;
        margin-top: 10px;
    }
    .link-btn:hover {
        background-color: #003d99;
    }
</style>
""", unsafe_allow_html=True)

# --- Detect theme for basic styling ---
# Streamlit handles dark mode relatively well, but we can use JS or rely on native classes if needed.
# For simplicity, we stick to standard styling.

@st.cache_resource
def load_engine():
    return SearchEngine(models_dir=os.path.join(project_root, "models"))

@st.cache_data
def get_courses():
    db_path = os.path.join(project_root, "database", "archive.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT course FROM documents ORDER BY course")
    courses = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return courses

# Main UI
st.title("📚 Penelusur Arsip Akademik")
st.markdown("Cari dokumen, modul, dan materi kuliah dari arsip Universitas Indonesia.")

# Load backend
with st.spinner("Memuat model mesin pencari..."):
    engine = load_engine()
    courses = get_courses()
    db_path = os.path.join(project_root, "database", "archive.db")

# Search UI
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Masukkan kata kunci pencarian...", placeholder="Contoh: manajemen risiko proyek")
with col2:
    selected_course = st.selectbox("Filter Mata Kuliah (Opsional)", ["Semua Mata Kuliah"] + courses)

top_k = st.slider("Jumlah hasil", min_value=5, max_value=50, value=10)

if query:
    with st.spinner("Mencari dokumen yang relevan..."):
        # 1. Search
        raw_results = engine.search(query, top_k=50) # Get more to allow filtering
        
        # 2. Enrich with metadata
        enriched_results = get_metadata(db_path, raw_results)
        
        # 3. Filter by course if needed
        if selected_course != "Semua Mata Kuliah":
            enriched_results = [r for r in enriched_results if r['course'] == selected_course]
            
        # 4. Limit to top_k
        final_results = enriched_results[:top_k]
        
    # Display results
    if not final_results:
        st.warning("Tidak ditemukan dokumen yang relevan dengan kata kunci tersebut.")
    else:
        st.success(f"Ditemukan {len(final_results)} dokumen yang relevan.")
        
        for doc in final_results:
            st.markdown(f"""
            <div class="result-card">
                <div class="result-title">{doc['title']}</div>
                <div class="result-meta">
                    <span class="sim-score">Sim: {doc['similarity']:.3f}</span> &nbsp;•&nbsp; 
                    <strong>Mata Kuliah:</strong> {doc['course']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Use columns for buttons/links
            c1, c2 = st.columns([1, 4])
            with c1:
                # PDF link (Streamlit can serve local files if they are in static folder, 
                # but we can just show the path for now or provide a download button)
                
                # We can create a download button since the file is local
                file_path = os.path.join(project_root, doc['file_path']) if doc.get('file_path') else ""
                if os.path.exists(file_path):
                    with open(file_path, "rb") as pdf_file:
                        st.download_button(
                            label="📥 Unduh PDF",
                            data=pdf_file,
                            file_name=doc['filename'],
                            mime="application/pdf",
                            key=f"dl_{doc['id']}"
                        )
                else:
                    st.button("❌ PDF Tidak Tersedia", disabled=True, key=f"na_{doc['id']}")
                    
            with c2:
                if doc.get('source_url'):
                    st.markdown(f"[Buka Sumber Asli (OCW)]({doc['source_url']})")
                    
            st.markdown("<hr style='margin: 10px 0; border: none;'>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Sistem Temu Kembali Informasi (IR) • TF-IDF + Vector Space Model</div>", unsafe_allow_html=True)
