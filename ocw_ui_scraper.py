#!/usr/bin/env python3
"""
=============================================================================
OCW UI Scraper — Dataset Builder untuk CBR/NLP  (PDF-ONLY mode)
=============================================================================
Pipeline:
  Kategori Fasilkom (categoryid=12)
    │
    ▼
  Daftar Mata Kuliah
    │
    ▼
  course/view.php?id=X  ─── discovery saja (tidak disimpan)
    │
    ▼
  Semua link di halaman course
    │
    ├── Mengarah ke PDF?  YA  → download → extract text (PyMuPDF)
    │                    TIDAK → SKIP (forum, tugas, HTML, video, dll.)
    ▼
  dataset_ocw_ui/<Nama_Matkul>/<nama_file>.pdf
  metadata.json  +  documents.jsonl

Hanya file PDF yang didownload. HTML, forum, tugas, dan link lain DIABAIKAN.

Lisensi sumber: Creative Commons BY-NC-SA (OCW UI)
Atribusi: Universitas Indonesia, Fakultas Ilmu Komputer
=============================================================================
Kebutuhan pip:
    pip install requests beautifulsoup4 lxml pymupdf tqdm
=============================================================================
"""

import os
import re
import json
import time
import random
import hashlib
import logging
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

# ─── Coba import PyMuPDF ────────────────────────────────────────────────────
try:
    import pymupdf as fitz  # PyMuPDF 1.24+ (menggantikan import fitz yang deprecated)
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz  # fallback untuk versi lama
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False
        logging.warning("PyMuPDF tidak tersedia. PDF tidak akan di-extract teksnya. "
                        "Install dengan: pip install pymupdf")

# ─── Coba import tqdm ───────────────────────────────────────────────────────
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    tqdm = lambda x, **kwargs: x  # fallback tanpa progress bar

# =============================================================================
# KONFIGURASI
# =============================================================================

BASE_URL        = "https://ocw.ui.ac.id/"
CATEGORY_URL    = BASE_URL + "course/index.php?categoryid=12"

# Target output directory (relatif ke lokasi script ini)
OUTPUT_DIR      = Path(__file__).parent / "dataset_ocw_ui"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Delay antar request (detik)
DELAY_MIN = 1.5
DELAY_MAX = 3.5

# Timeout request (detik)
REQUEST_TIMEOUT = 45

# Ukuran maksimum file yang didownload (bytes) — 100 MB
MAX_FILE_SIZE = 100 * 1024 * 1024

# Atribusi lisensi
LICENSE_INFO = {
    "license": "CC BY-NC-SA 4.0",
    "license_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "attribution": "Universitas Indonesia — OpenCourseWare (OCW UI)",
    "source_site": "https://ocw.ui.ac.id/",
}

# Format nama file JSONL output
DOCUMENTS_JSONL = "documents.jsonl"
METADATA_JSON   = "metadata.json"

# =============================================================================
# SETUP LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(Path(__file__).parent / "scraper.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================================
# HELPERS
# =============================================================================

def make_session() -> requests.Session:
    """Buat requests.Session dengan header default."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def polite_sleep():
    """Jeda acak antar request agar sopan ke server."""
    delay = random.uniform(DELAY_MIN, DELAY_MAX)
    time.sleep(delay)


def safe_filename(name: str, max_len: int = 80) -> str:
    """
    Ubah string menjadi nama file/folder yang aman.
    Ganti karakter tidak valid dengan underscore.
    """
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r'\s+', "_", name.strip())
    name = re.sub(r'_+', "_", name)
    return name[:max_len].strip("_") or "unnamed"


def url_to_id(url: str) -> str:
    """Buat ID unik pendek dari URL (8 karakter pertama MD5)."""
    return hashlib.md5(url.encode()).hexdigest()[:8]


def classify_url(url: str) -> str:
    """
    Klasifikasikan tipe resource berdasarkan URL.
    Return: 'pdf' | 'pluginfile' | 'resource' | 'folder' | 'video' | 'course' | 'other'
    """
    u = url.lower()
    if ".pdf" in u:
        return "pdf"
    if "pluginfile.php" in u:
        return "pluginfile"
    if "/mod/resource/view.php" in u:
        return "resource"
    if "/mod/folder/view.php" in u:
        return "folder"
    if "youtube.com" in u or "youtu.be" in u:
        return "video"
    if "/course/view.php" in u:
        return "course"
    return "other"


def get_file_ext_from_content_type(content_type: str) -> str:
    """Tebak ekstensi file dari Content-Type."""
    ct = content_type.lower()
    if "pdf" in ct:
        return ".pdf"
    if "powerpoint" in ct or "presentation" in ct:
        return ".pptx"
    if "word" in ct or "msword" in ct:
        return ".docx"
    if "excel" in ct or "spreadsheet" in ct:
        return ".xlsx"
    if "zip" in ct:
        return ".zip"
    if "html" in ct:
        return ".html"
    return ".bin"


# =============================================================================
# STEP 1: AMBIL DAFTAR COURSE DARI HALAMAN KATEGORI
# =============================================================================

def get_course_list(session: requests.Session, category_url: str) -> list:
    """
    Scrape halaman kategori Fasilkom dan kembalikan list course.
    Return: [{"id": "95", "name": "Manajemen Proyek TI", "url": "https://..."}]
    """
    logger.info(f"Mengambil daftar course dari: {category_url}")
    resp = session.get(category_url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    polite_sleep()

    soup = BeautifulSoup(resp.text, "html.parser")
    courses = {}

    # Selector utama: div.coursename > a
    for a in soup.select("div.coursename a[href*='/course/view.php']"):
        href = a.get("href", "")
        full_url = urljoin(BASE_URL, href)
        name = a.get_text(" ", strip=True)
        m = re.search(r"id=(\d+)", href)
        if m and name:
            course_id = m.group(1)
            if full_url not in courses:
                courses[full_url] = {
                    "id": course_id,
                    "name": name,
                    "url": full_url,
                }

    # Fallback: selector yang lebih luas
    if not courses:
        for a in soup.select("a[href*='/course/view.php?id=']"):
            href = a.get("href", "")
            full_url = urljoin(BASE_URL, href)
            name = a.get_text(" ", strip=True)
            m = re.search(r"id=(\d+)", href)
            if m and name and len(name) > 3:
                course_id = m.group(1)
                if full_url not in courses:
                    courses[full_url] = {
                        "id": course_id,
                        "name": name,
                        "url": full_url,
                    }

    result = list(courses.values())
    logger.info(f"Ditemukan {len(result)} course.")
    for c in result:
        logger.info(f"  [{c['id']}] {c['name']}")
    return result


# =============================================================================
# STEP 2: SCRAPE HALAMAN COURSE — EKSTRAK TOPIK + RESOURCE
# =============================================================================

def get_course_content(session: requests.Session, course: dict) -> dict:
    """
    Buka halaman course/view.php?id=X dan ekstrak topik + resource.
    """
    url = course["url"]
    logger.info(f"Scraping course: {course['name']} ({url})")

    resp = session.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    polite_sleep()

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── Deskripsi course ────────────────────────────────────────────────────
    desc = ""
    for sel in ["div.summary p", "div.course-description", "#region-main .generalbox"]:
        el = soup.select_one(sel)
        if el:
            desc = el.get_text(" ", strip=True)
            break

    # ── Nama course dari halaman ────────────────────────────────────────────
    course_name_from_page = course["name"]
    h1 = soup.select_one("h1")
    if h1:
        course_name_from_page = h1.get_text(" ", strip=True) or course["name"]

    sections = []

    # ── Iterasi section/topik ───────────────────────────────────────────────
    section_els = soup.select("li.section, div.section.main, ul.topics > li")
    if not section_els:
        section_els = soup.select("div.course-content ul li.section")
    if not section_els:
        section_els = soup.select("[id^='section-']")

    for sec_idx, sec_el in enumerate(section_els):
        title_el = sec_el.select_one(
            "h3.sectionname, h3.section-title, .content .sectionname, "
            "span.sectionname, div.section-title, h3"
        )
        sec_title = title_el.get_text(" ", strip=True) if title_el else f"Bagian {sec_idx}"

        resources = []
        seen_urls = set()

        for a in sec_el.select("a[href]"):
            href = a.get("href", "")
            if not href or href.startswith("#"):
                continue

            full_url = urljoin(BASE_URL, href)
            if "ocw.ui.ac.id" not in full_url:
                continue
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            skip_patterns = [
                "/course/index.php", "/login/", "/user/", "/grade/",
                "/calendar/", "/message/", "/report/", "info.php",
                "theme/image.php", "javascript.php", "yui_combo.php",
            ]
            if any(p in full_url for p in skip_patterns):
                continue

            title    = a.get_text(" ", strip=True) or a.get("title", "") or "Resource"
            url_type = classify_url(full_url)

            if url_type == "course" and full_url == url:
                continue

            resources.append({
                "title": title,
                "url":   full_url,
                "type":  url_type,
            })

        if sec_title or resources:
            sections.append({
                "section_index": sec_idx,
                "section_title": sec_title,
                "resources":     resources,
            })

    # Jika tidak ada sections terstruktur, fallback ambil semua resource
    if not sections:
        logger.warning(f"  Tidak ada section terstruktur. Fallback ke semua resource.")
        resources = []
        seen_urls = set()
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if not href or href.startswith("#"):
                continue
            full_url = urljoin(BASE_URL, href)
            if "ocw.ui.ac.id" not in full_url or full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            url_type = classify_url(full_url)
            if url_type in ("pdf", "pluginfile", "resource"):
                title = a.get_text(" ", strip=True) or "Resource"
                resources.append({"title": title, "url": full_url, "type": url_type})

        if resources:
            sections = [{"section_index": 0, "section_title": "Materi Kuliah", "resources": resources}]

    total_res = sum(len(s["resources"]) for s in sections)
    logger.info(f"  → {len(sections)} section, {total_res} resource.")

    return {
        "course_id":   course["id"],
        "course_name": course_name_from_page,
        "course_url":  url,
        "description": desc,
        "sections":    sections,
    }


# =============================================================================
# STEP 3: RESOLVE REDIRECT MOD/RESOURCE → PLUGINFILE
# =============================================================================

def resolve_resource_url(session: requests.Session, resource: dict) -> dict:
    """
    Untuk link mod/resource/view.php, ikuti redirect untuk temukan file asli.
    Setelah resolve, set resolved_type = 'skip' jika bukan PDF.
    """
    url      = resource["url"]
    url_type = resource["type"]

    # Link yang jelas bukan PDF langsung ditandai skip
    if url_type not in ("pdf", "pluginfile", "resource", "folder"):
        resource["resolved_url"]  = url
        resource["resolved_type"] = "skip"
        return resource

    # Link PDF eksplisit tidak perlu HEAD request
    if url_type == "pdf":
        resource["resolved_url"]  = url
        resource["resolved_type"] = "pdf"
        return resource

    # pluginfile / mod/resource / folder → cek via HEAD
    try:
        resp = session.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        final_url    = resp.url
        content_type = resp.headers.get("Content-Type", "")

        if "pdf" in content_type or final_url.lower().endswith(".pdf"):
            resolved_type = "pdf"
        elif "pdf" in classify_url(final_url):
            resolved_type = "pdf"
        else:
            # Bukan PDF → skip
            resolved_type = "skip"

        resource["resolved_url"]  = final_url
        resource["resolved_type"] = resolved_type

    except Exception as e:
        logger.debug(f"Resolve failed untuk {url}: {e}")
        resource["resolved_url"]  = url
        resource["resolved_type"] = "skip"  # aman: skip jika tidak bisa diverifikasi

    polite_sleep()
    return resource


# =============================================================================
# STEP 4: DOWNLOAD FILE
# =============================================================================

def download_file(
    session: requests.Session,
    url: str,
    output_path: Path,
    max_size: int = MAX_FILE_SIZE,
) -> tuple:
    """
    Download file dari URL ke output_path.
    Return: (success: bool, bytes_downloaded: int, content_type: str)
    """
    try:
        with session.get(url, stream=True, timeout=REQUEST_TIMEOUT, allow_redirects=True) as resp:
            resp.raise_for_status()

            content_type   = resp.headers.get("Content-Type", "")
            content_length = int(resp.headers.get("Content-Length", 0))

            if content_length > max_size:
                logger.warning(f"File terlalu besar ({content_length} bytes), skip: {url}")
                return False, 0, content_type

            output_path.parent.mkdir(parents=True, exist_ok=True)

            total = 0
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
                        if total > max_size:
                            logger.warning(f"File melebihi batas saat download, stop: {url}")
                            return False, total, content_type

            return True, total, content_type

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error {e.response.status_code} untuk {url}")
        return False, 0, ""
    except Exception as e:
        logger.error(f"Download gagal untuk {url}: {e}")
        return False, 0, ""


# =============================================================================
# STEP 5: EKSTRAK TEKS
# =============================================================================

def extract_pdf_text(pdf_path: Path) -> list:
    """
    Ekstrak teks dari file PDF menggunakan PyMuPDF.
    Return: [{"page": 1, "text": "..."}, ...]
    """
    if not PYMUPDF_AVAILABLE:
        return []

    pages = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().strip()
            if text:
                pages.append({
                    "page": page_num + 1,
                    "text": text,
                })
        doc.close()
    except Exception as e:
        logger.error(f"Gagal ekstrak PDF {pdf_path}: {e}")

    return pages


def extract_html_text(html_content: str) -> str:
    """Ekstrak teks bersih dari konten HTML."""
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()

    main = soup.select_one(
        "div#region-main, div.course-content, div.entry-content, article, main"
    )
    text = (main or soup).get_text(separator="\n", strip=True)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def clean_text(text: str) -> str:
    """Normalisasi teks: hapus karakter aneh, normalisasi spasi."""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()


# =============================================================================
# STEP 6: PIPELINE UTAMA
# =============================================================================

def scrape_all(
    category_url: str = CATEGORY_URL,
    output_dir: Path = OUTPUT_DIR,
    course_ids=None,
    dry_run: bool = False,
    skip_existing: bool = True,
):
    """
    Pipeline lengkap scraping OCW UI.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    session = make_session()

    # ── 1. Daftar course ────────────────────────────────────────────────────
    courses = get_course_list(session, category_url)

    if course_ids:
        courses = [c for c in courses if c["id"] in course_ids]
        logger.info(f"Filter aktif: hanya {len(courses)} course diproses.")

    all_documents = []
    all_metadata  = []
    doc_counter   = 0

    # ── 2. Proses setiap course ─────────────────────────────────────────────
    course_iter = tqdm(courses, desc="Course") if TQDM_AVAILABLE else courses
    for course in course_iter:
        course_name_safe = safe_filename(course["name"])
        course_dir       = output_dir / course_name_safe
        course_dir.mkdir(parents=True, exist_ok=True)

        meta_path = course_dir / METADATA_JSON
        if skip_existing and meta_path.exists():
            logger.info(f"Skip (sudah ada): {course['name']}")
            try:
                with open(meta_path, encoding="utf-8") as f:
                    all_metadata.append(json.load(f))
            except Exception:
                pass
            continue

        try:
            content = get_course_content(session, course)
        except Exception as e:
            logger.error(f"Gagal scrape course {course['name']}: {e}")
            continue

        course_meta = {
            **LICENSE_INFO,
            "course_id":    content["course_id"],
            "course_name":  content["course_name"],
            "course_url":   content["course_url"],
            "description":  content["description"],
            "university":   "Universitas Indonesia",
            "faculty":      "Fakultas Ilmu Komputer",
            "category_url": category_url,
            "resources":    [],
        }

        # ── 3. Proses resource setiap section ─────────────────────────────
        for section in content["sections"]:
            sec_title = section["section_title"]

            for res in section["resources"]:
                polite_sleep()
                doc_counter += 1
                doc_id = f"ui_ocw_{doc_counter:06d}"

                res       = resolve_resource_url(session, res)
                final_url = res.get("resolved_url", res["url"])
                res_type  = res.get("resolved_type", res["type"])
                res_title = res["title"]

                resource_meta = {
                    "id":           doc_id,
                    "course_id":    content["course_id"],
                    "course_name":  content["course_name"],
                    "section":      sec_title,
                    "title":        res_title,
                    "type":         res_type,
                    "source_url":   final_url,
                    "original_url": res["url"],
                    **LICENSE_INFO,
                    "file":         None,
                    "pages":        [],
                    "text_preview": "",
                }

                # ── SKIP: bukan PDF ────────────────────────────────────────
                if res_type == "skip":
                    logger.debug(f"  SKIP (bukan PDF): {res_title} → {final_url}")
                    continue

                # ── Download PDF ───────────────────────────────────────────
                if res_type == "pdf" and not dry_run:
                    url_path  = urlparse(final_url).path
                    url_fname = os.path.basename(unquote(url_path))

                    if not url_fname or "pluginfile.php" in url_fname:
                        url_fname = safe_filename(res_title) + ".pdf"
                    else:
                        stem = safe_filename(os.path.splitext(url_fname)[0])
                        ext  = os.path.splitext(url_fname)[1].lower() or ".pdf"
                        url_fname = stem + ext

                    # Pastikan ekstensi .pdf
                    if not url_fname.lower().endswith(".pdf"):
                        url_fname += ".pdf"

                    file_path = course_dir / url_fname
                    if file_path.exists():
                        stem = file_path.stem
                        file_path = course_dir / f"{stem}_{doc_id}.pdf"

                    logger.info(f"  Download PDF [{doc_id}]: {url_fname}")
                    success, nbytes, ct = download_file(session, final_url, file_path)

                    if success:
                        # Rename jika server mengirim .pdf tanpa ekstensi
                        if not str(file_path).lower().endswith(".pdf"):
                            new_path = file_path.with_suffix(".pdf")
                            try:
                                file_path.rename(new_path)
                                file_path = new_path
                            except Exception:
                                pass

                        resource_meta["file"]       = str(file_path.relative_to(output_dir))
                        resource_meta["type"]       = "pdf"
                        resource_meta["size_bytes"] = nbytes

                        pages     = extract_pdf_text(file_path)
                        full_text = clean_text("\n\n".join(p["text"] for p in pages if p.get("text")))
                        resource_meta["pages"]        = pages
                        resource_meta["text_preview"] = full_text[:300]

                        if full_text:
                            all_documents.append({
                                "id":         doc_id,
                                "course":     content["course_name"],
                                "course_id":  content["course_id"],
                                "section":    sec_title,
                                "title":      res_title,
                                "type":       "pdf",
                                "source_url": final_url,
                                "license":    LICENSE_INFO["license"],
                                "text":       full_text,
                            })
                    else:
                        resource_meta["download_failed"] = True

                elif dry_run:
                    logger.info(f"  [DRY RUN] {doc_id}: {res_title} ({res_type}) → {final_url}")

                course_meta["resources"].append(resource_meta)
                all_metadata.append(resource_meta)

        # ── Simpan metadata per course ─────────────────────────────────────
        if not dry_run:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(course_meta, f, ensure_ascii=False, indent=2)
            logger.info(f"  Metadata disimpan: {meta_path}")

    # ── 4. Simpan documents.jsonl global ────────────────────────────────────
    if not dry_run:
        jsonl_path = output_dir / DOCUMENTS_JSONL
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for doc in all_documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        logger.info(f"\n[JSONL] {jsonl_path}  ({len(all_documents)} entri)")

        global_meta_path = output_dir / "all_metadata.json"
        with open(global_meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_resources": len(all_metadata),
                "total_documents": len(all_documents),
                "category_url":    category_url,
                **LICENSE_INFO,
                "resources": all_metadata,
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"[Meta]  {global_meta_path}")

    logger.info("=" * 60)
    logger.info(f"SELESAI — Resource: {len(all_metadata)} | Dokumen teks: {len(all_documents)}")
    logger.info(f"Output: {output_dir.resolve()}")


# =============================================================================
# CLI
# =============================================================================

def main():
    global DELAY_MIN, DELAY_MAX
    parser = argparse.ArgumentParser(
        description="OCW UI Scraper — Dataset Builder untuk CBR/NLP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  # Scrape semua course Fasilkom
  python ocw_ui_scraper.py

  # Scrape course tertentu (berdasarkan ID)
  python ocw_ui_scraper.py --courses 29 31 55

  # Dry run: lihat resource tanpa download
  python ocw_ui_scraper.py --dry-run

  # Output ke folder khusus
  python ocw_ui_scraper.py --output D:/MyDataset

  # Re-scrape meski sudah ada
  python ocw_ui_scraper.py --no-skip
        """,
    )
    parser.add_argument("--output", "-o", default=str(OUTPUT_DIR),
                        help=f"Folder output dataset (default: {OUTPUT_DIR})")
    parser.add_argument("--courses", "-c", nargs="*", metavar="ID",
                        help="Hanya scrape course dengan ID tertentu")
    parser.add_argument("--dry-run", action="store_true",
                        help="Tampilkan resource tanpa download")
    parser.add_argument("--no-skip", action="store_true",
                        help="Re-scrape meski metadata sudah ada")
    parser.add_argument("--category-url", default=CATEGORY_URL,
                        help=f"URL kategori (default: {CATEGORY_URL})")
    parser.add_argument("--delay-min", type=float, default=DELAY_MIN,
                        help=f"Delay minimum antar request (default: {DELAY_MIN}s)")
    parser.add_argument("--delay-max", type=float, default=DELAY_MAX,
                        help=f"Delay maksimum antar request (default: {DELAY_MAX}s)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Aktifkan log detail (DEBUG)")

    args = parser.parse_args()

    DELAY_MIN = args.delay_min
    DELAY_MAX = args.delay_max

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("OCW UI Scraper — Dataset Builder untuk CBR/NLP")
    logger.info(f"Output  : {args.output}")
    logger.info(f"Dry Run : {args.dry_run}")
    logger.info(f"Skip Ex.: {not args.no_skip}")
    logger.info(f"Delay   : {args.delay_min}–{args.delay_max} detik")
    if args.courses:
        logger.info(f"Course  : {', '.join(args.courses)}")
    logger.info("=" * 60)

    scrape_all(
        category_url  = args.category_url,
        output_dir    = Path(args.output),
        course_ids    = args.courses,
        dry_run       = args.dry_run,
        skip_existing = not args.no_skip,
    )


if __name__ == "__main__":
    main()
