#!/usr/bin/env python3
"""
Academic IR System — Multi-Disciplinary Lecture Materials Harvester
===================================================================
Scrapes lecture materials (PDF & PPTX slides) from ALL faculties and
study programs on OCW Universitas Indonesia, extracts text, chunks them,
and ingests them into SQLite (database/academic_ir.db).

Supported Faculties:
  - Kedokteran (cid=2)
  - FMIPA (cid=4)
  - Teknik (cid=5)
  - Ekonomi dan Bisnis (cid=7)
  - Ilmu Pengetahuan Budaya (cid=8)
  - Psikologi (cid=9)
  - FISIP (cid=10)
  - Kesehatan Masyarakat (cid=11)
  - Ilmu Keperawatan (cid=13)
  - Farmasi (cid=17)
  - Ilmu Administrasi (cid=18)

Usage:
    python scripts/collect_materials_all_prodi.py [--faculty all|5|7|...] [--limit-per-faculty N] [--rebuild-index]
"""

import sys
import os
import re
import io
import json
import time
import zipfile
import argparse
import logging
from pathlib import Path
from urllib.parse import urljoin, quote
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.extraction.pdf import extract_pdf, PDFExtractionResult
from src.indexing.chunker import create_chunks
from src.normalization.language import detect_language
from src.preprocessing.pipeline import PreprocessingPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("collect_materials")

UI_FACULTIES = {
    2: "Fakultas Kedokteran",
    4: "Fakultas Matematika & Ilmu Pengetahuan Alam",
    5: "Fakultas Teknik",
    7: "Fakultas Ekonomi dan Bisnis",
    8: "Fakultas Ilmu Pengetahuan Budaya",
    9: "Fakultas Psikologi",
    10: "Fakultas Ilmu Sosial & Ilmu Politik",
    11: "Fakultas Kesehatan Masyarakat",
    13: "Fakultas Ilmu Keperawatan",
    17: "Fakultas Farmasi",
    18: "Fakultas Ilmu Administrasi",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def extract_pptx_content(content_bytes: bytes) -> PDFExtractionResult:
    """Extract slides text from a PPTX presentation."""
    res = PDFExtractionResult()
    res.extraction_method = "pptx_xml"
    try:
        z = zipfile.ZipFile(io.BytesIO(content_bytes))
        slide_files = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        
        # Sort naturally by slide number
        def slide_sort_key(name):
            m = re.search(r'slide(\d+)\.xml', name)
            return int(m.group(1)) if m else 0
        slide_files.sort(key=slide_sort_key)

        total_words = 0
        for idx, sfile in enumerate(slide_files, start=1):
            root = ET.fromstring(z.read(sfile))
            texts = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
            slide_text = " ".join(texts)
            words = slide_text.split()
            word_count = len(words)
            total_words += word_count
            res.pages.append({
                "page_number": idx,
                "raw_text": slide_text,
                "word_count": word_count,
            })

        res.page_count = len(slide_files)
        res.total_words = total_words
        res.extraction_status = "SUCCESS" if total_words >= 10 else "PARTIAL"
    except Exception as e:
        logger.warning(f"PPTX extraction error: {e}")
        res.extraction_status = "FAILED"
        res.error_message = str(e)
    return res


def harvest_faculty_materials(db: Database, pipeline: PreprocessingPipeline,
                              cid: int, faculty_name: str,
                              max_courses: int = 3, max_files_per_course: int = 5) -> int:
    """Harvest courses and lecture materials for a specific faculty."""
    category_url = f"https://ocw.ui.ac.id/course/index.php?categoryid={cid}"
    logger.info(f"[{faculty_name}] Discovering courses from {category_url}")

    try:
        r = requests.get(category_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.error(f"[{faculty_name}] Failed to fetch category: {e}")
        return 0

    courses = []
    for a in soup.find_all("a", href=True):
        if "course/view.php" in a["href"]:
            cname = a.get_text(strip=True)
            if cname and a["href"] not in [c["url"] for c in courses]:
                courses.append({"name": cname, "url": a["href"]})

    logger.info(f"[{faculty_name}] Discovered {len(courses)} courses.")
    if not courses:
        return 0

    if max_courses and max_courses > 0:
        courses = courses[:max_courses]
    total_ingested = 0
    raw_material_dir = PROJECT_ROOT / "data" / "raw" / "material" / re.sub(r'[^a-zA-Z0-9_\-]', '_', faculty_name)
    raw_material_dir.mkdir(parents=True, exist_ok=True)

    for course in courses:
        cname = course["name"]
        curl = course["url"]
        logger.info(f"[{faculty_name}] Inspecting course: '{cname}'")

        try:
            cr = requests.get(curl, headers=HEADERS, timeout=20, verify=False)
            csoup = BeautifulSoup(cr.text, "html.parser")
        except Exception as e:
            logger.warning(f"Failed to fetch course {cname}: {e}")
            continue

        resource_links = []
        for ra in csoup.find_all("a", href=True):
            href = ra["href"]
            if "mod/resource/view.php" in href or "pluginfile.php" in href:
                rtitle = ra.get_text(strip=True)
                if href not in [x["url"] for x in resource_links]:
                    resource_links.append({"title": rtitle, "url": href})

        logger.info(f"[{faculty_name} | {cname}] Found {len(resource_links)} material resources.")
        ingested_course = 0

        for ritem in resource_links:
            if max_files_per_course and max_files_per_course > 0 and ingested_course >= max_files_per_course:
                break

            r_title = ritem["title"]
            r_url = ritem["url"]

            try:
                # Download resource with redirects
                resp = requests.get(r_url, headers=HEADERS, timeout=25, stream=True, verify=False)
                if resp.status_code != 200:
                    continue

                content_type = resp.headers.get("Content-Type", "").lower()
                final_url = resp.url.lower()

                is_pdf = "pdf" in content_type or final_url.endswith(".pdf") or resp.content[:4] == b"%PDF"
                is_pptx = "presentation" in content_type or final_url.endswith(".pptx") or final_url.endswith(".ppt") or resp.content[:4] == b"PK\x03\x04"

                if not (is_pdf or is_pptx):
                    continue  # skip video, audio, webm, web page labels

                import hashlib
                sha256 = hashlib.sha256(resp.content).hexdigest()

                if db.check_duplicate(sha256):
                    logger.info(f"Duplicate material detected ({r_title[:30]}), skipping.")
                    continue

                safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', r_title[:30]).strip("_")
                ext = "pdf" if is_pdf else "pptx"
                dest_file = raw_material_dir / f"{safe_title}.{ext}"

                with open(dest_file, "wb") as f:
                    f.write(resp.content)

                if is_pdf:
                    extract_res = extract_pdf(str(dest_file))
                else:
                    extract_res = extract_pptx_content(resp.content)

                if not extract_res.is_valid() or extract_res.total_words < 20:
                    logger.warning(f"Insufficient text in {dest_file.name} ({extract_res.total_words} words), skipping.")
                    dest_file.unlink(missing_ok=True)
                    continue

                doc_id = db.get_next_id("MAT")
                raw_fulltext = extract_res.full_text
                lang_info = detect_language(raw_fulltext)
                lang_code = lang_info.get("language") or "id"

                clean_title = re.sub(r'\s+File$', '', r_title, flags=re.IGNORECASE).strip()

                doc_meta = {
                    "document_id": doc_id,
                    "document_type": "MATERIAL",
                    "title": clean_title or cname,
                    "abstract": None,
                    "authors": json.dumps([f"{faculty_name}, Universitas Indonesia"]),
                    "institution": "Universitas Indonesia",
                    "department": faculty_name,
                    "course": cname,
                    "year": 2023,
                    "language": lang_code,
                    "language_confidence": lang_info.get("confidence", 0.9),
                    "keywords": json.dumps([faculty_name, cname]),
                    "source": "OCW_UI",
                    "source_url": r_url,
                    "fulltext_url": resp.url,
                    "local_path": str(dest_file.relative_to(PROJECT_ROOT)),
                    "file_type": ext,
                    "file_size": len(resp.content),
                    "page_count": extract_res.page_count,
                    "license": "OpenCourseWare UI (CC BY-NC-SA 4.0)",
                    "sha256": sha256,
                    "doi": None,
                    "extraction_method": extract_res.extraction_method,
                    "extraction_status": extract_res.extraction_status,
                    "collection_status": "READY_FOR_INDEXING",
                    "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }

                conn = db.get_connection()
                try:
                    db.insert_document(doc_meta, conn=conn)

                    page_clean_map = {}
                    for p in extract_res.pages:
                        p_num = p["page_number"]
                        p_raw = p["raw_text"]
                        p_clean = pipeline.process_document(p_raw, language=lang_code) if p_raw else ""
                        page_clean_map[p_num] = p_clean
                        db.insert_page(
                            document_id=doc_id,
                            page_number=p_num,
                            raw_text=p_raw,
                            clean_text=p_clean,
                            word_count=p["word_count"],
                            conn=conn
                        )

                    chunks = create_chunks(extract_res.pages, doc_id, max_words=500, overlap_words=50)
                    for chunk in chunks:
                        p_num = chunk.get("page_start")
                        if chunk.get("page_start") == chunk.get("page_end") and p_num in page_clean_map:
                            c_clean = page_clean_map[p_num]
                        else:
                            c_clean = pipeline.process_document(chunk["raw_text"], language=lang_code)
                        chunk["clean_text"] = c_clean
                        db.insert_chunk(chunk, conn=conn)

                    db.log(
                        document_id=doc_id,
                        stage="INGEST",
                        status="SUCCESS",
                        message=f"Material ingested: {faculty_name} / {cname} ({len(chunks)} chunks)",
                        conn=conn
                    )
                    conn.commit()
                finally:
                    conn.close()

                ingested_course += 1
                total_ingested += 1
                logger.info(f"Successfully ingested {doc_id}: [{faculty_name}] {clean_title} ({len(chunks)} chunks)")

            except Exception as e:
                logger.warning(f"Error processing resource {r_title}: {e}")

    return total_ingested


def export_manifest(db: Database, manifest_path: Path) -> int:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    docs = db.get_documents_by_type("MATERIAL")
    with open(manifest_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Harvest lecture materials across all UI faculties.")
    parser.add_argument("--faculty", type=str, default="all", help="Faculty ID or 'all'")
    parser.add_argument("--max-courses", type=int, default=0, help="Max courses per faculty (0 = all courses)")
    parser.add_argument("--limit-per-course", type=int, default=0, help="Max files per course (0 = all files)")
    parser.add_argument("--rebuild-index", action="store_true", default=True, help="Rebuild TF-IDF index after collection")

    args = parser.parse_args()

    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    full_db_path = PROJECT_ROOT / "database" / "academic_ir.db"
    db = Database(str(full_db_path))
    db.initialize()
    pipeline = PreprocessingPipeline(default_language="id")

    if args.faculty.lower() == "all":
        targets = UI_FACULTIES.items()
    else:
        try:
            cid = int(args.faculty)
            targets = [(cid, UI_FACULTIES.get(cid, f"Fakultas {cid}"))]
        except ValueError:
            matched = [(cid, name) for cid, name in UI_FACULTIES.items() if args.faculty.lower() in name.lower()]
            targets = matched or UI_FACULTIES.items()

    grand_total = 0
    start_time = time.time()

    for cid, fname in targets:
        logger.info(f"\n{'='*60}\n  COLLECTING: {fname} (Category ID: {cid})\n{'='*60}")
        count = harvest_faculty_materials(
            db=db,
            pipeline=pipeline,
            cid=cid,
            faculty_name=fname,
            max_courses=args.max_courses,
            max_files_per_course=args.limit_per_course
        )
        grand_total += count

    manifest_file = PROJECT_ROOT / "data" / "manifests" / "material.jsonl"
    mat_count = export_manifest(db, manifest_file)

    if args.rebuild_index and grand_total > 0:
        logger.info("\n=== Rebuilding TF-IDF Index with New Materials ===")
        from scripts.build_index import build_unified_manifest
        from src.indexing.tfidf import TFIDFIndex
        import yaml

        manifest_csv = PROJECT_ROOT / "data" / "manifests" / "unified_manifest.csv"
        build_unified_manifest(db, manifest_csv)

        config_file = PROJECT_ROOT / "config" / "sources.yaml"
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        tfidf_cfg = cfg.get("tfidf", {})

        chunks = db.get_all_indexed_chunks()
        tfidf = TFIDFIndex(
            ngram_range=tuple(tfidf_cfg.get("ngram_range", [1, 2])),
            sublinear_tf=tfidf_cfg.get("sublinear_tf", True),
            min_df=tfidf_cfg.get("min_df", 2),
            max_df=tfidf_cfg.get("max_df", 0.95),
        )
        tfidf.fit(chunks)
        models_dir = PROJECT_ROOT / "models"
        tfidf.save(str(models_dir))
        logger.info(f"TF-IDF model updated with {len(chunks)} chunks.")

    elapsed = round(time.time() - start_time, 1)
    print("\n" + "=" * 65)
    print("  MULTI-DISCIPLINARY MATERIAL COLLECTION COMPLETE")
    print("=" * 65)
    print(f"Elapsed Time:               {elapsed}s")
    print(f"Total New Materials Added:  {grand_total}")
    print(f"Total Materials in DB:      {mat_count}")
    print(f"Manifest Generated:         {manifest_file}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
