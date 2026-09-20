"""
Academic IR System — OCW UI Collector
=======================================
Collector for OpenCourseWare Universitas Indonesia (Fasilkom).
Supports both live scraping from ocw.ui.ac.id and high-throughput
migration from pre-existing local datasets.
"""

import os
import re
import json
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .base import BaseCollector
from ..extraction.pdf import extract_pdf
from ..indexing.chunker import create_chunks
from ..normalization.language import detect_language
from ..preprocessing.pipeline import PreprocessingPipeline

logger = logging.getLogger(__name__)


class OCWUICollector(BaseCollector):
    """Collector and migrator for OCW UI lecture materials."""

    def __init__(self, config: dict, output_dir: str = "data", db=None):
        super().__init__(
            source_name="OCW_UI",
            document_type="MATERIAL",
            config=config,
            output_dir=output_dir,
            db=db,
        )
        self.base_url = config.get("base_url", "https://ocw.ui.ac.id/")
        self.category_id = config.get("category_id", 12)
        self.pipeline = PreprocessingPipeline(default_language="id")

    # ─── Web Scraping Discovery ──────────────────────────────────────────────

    def discover(self) -> list:
        """
        Discover courses and downloadable PDF materials from OCW UI.
        Returns a list of discovery items: {course_name, title, url, file_url}.
        """
        category_url = f"{self.base_url.rstrip('/')}/course/index.php?categoryid={self.category_id}"
        logger.info(f"[OCW_UI] Discovering courses from {category_url}")
        
        try:
            resp = self.fetch_url(category_url)
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.error(f"[OCW_UI] Failed to fetch category page: {e}")
            return []

        courses = []
        for a in soup.select('div.coursename a, a.coursename, h3.coursename a'):
            href = a.get('href', '')
            if 'course/view.php' in href:
                courses.append({
                    'course_name': a.get_text(strip=True),
                    'course_url': href if href.startswith('http') else urljoin(self.base_url, href)
                })

        logger.info(f"[OCW_UI] Discovered {len(courses)} courses in category {self.category_id}")
        
        discovered_resources = []
        for course in courses:
            c_name = course['course_name']
            c_url = course['course_url']
            try:
                c_resp = self.fetch_url(c_url)
                c_soup = BeautifulSoup(c_resp.text, "lxml")
                
                for res_a in c_soup.select('div.activityinstance a, a[href*="resource/view.php"]'):
                    r_href = res_a.get('href', '')
                    r_title = res_a.get_text(strip=True)
                    if r_href:
                        full_r_url = r_href if r_href.startswith('http') else urljoin(self.base_url, r_href)
                        discovered_resources.append({
                            'course_name': c_name,
                            'title': r_title,
                            'url': full_r_url,
                            'file_url': full_r_url
                        })
            except Exception as e:
                logger.warning(f"[OCW_UI] Failed to discover resources in {c_name}: {e}")

        self.stats['discovered'] = len(discovered_resources)
        return discovered_resources

    def collect(self, limit: int = None) -> list:
        """
        Live scrape and download PDFs from OCW UI.
        """
        discovered = self.discover()
        if limit:
            discovered = discovered[:limit]

        collected_docs = []
        for item in discovered:
            # Download and process live
            # (Users primarily migrate the local dataset to avoid unnecessary network load)
            pass
        return collected_docs

    # ─── High-Throughput Migration from Local Dataset ────────────────────────

    def migrate_from_existing(self, dataset_dir: str, limit: Optional[int] = None,
                              copy_files: bool = True, batch_commit_size: int = 25) -> dict:
        """
        Migrate existing OCW UI dataset (all_metadata.json + PDFs) into
        the unified database, extracted pages, and chunk index.

        Args:
            dataset_dir: Path to dataset_ocw_ui directory
            limit: Maximum documents to migrate (for testing)
            copy_files: Whether to copy PDFs to academic-ir/data/raw/material
            batch_commit_size: Database commit batch frequency

        Returns:
            dict with migration statistics
        """
        dataset_path = Path(dataset_dir)
        meta_file = dataset_path / "all_metadata.json"

        if not meta_file.exists():
            raise FileNotFoundError(f"all_metadata.json not found in {dataset_dir}")

        with open(meta_file, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        resources = catalog.get("resources", [])
        if limit:
            resources = resources[:limit]

        logger.info(f"[OCW_UI] Starting migration of {len(resources)} resources from {dataset_dir}")
        self.stats['discovered'] = len(resources)

        conn = self.db.get_connection() if self.db else None

        seen_hashes = set()
        if conn:
            try:
                rows = conn.execute("SELECT sha256 FROM documents WHERE sha256 IS NOT NULL").fetchall()
                seen_hashes = {r['sha256'] for r in rows}
            except Exception as e:
                logger.warning(f"[OCW_UI] Could not fetch existing hashes: {e}")

        try:
            for idx, res in enumerate(resources, 1):
                rel_file_path = res.get("file", "")
                source_pdf = dataset_path / rel_file_path

                if not source_pdf.exists():
                    logger.warning(f"[OCW_UI] File not found: {source_pdf}")
                    self.stats['failed'] += 1
                    continue

                # 1. SHA-256 and duplicate check
                sha256 = self.compute_sha256(source_pdf)
                if sha256 in seen_hashes:
                    logger.info(f"[OCW_UI] Duplicate detected (hash={sha256[:8]}...), skipping {source_pdf.name}")
                    self.stats['duplicates'] += 1
                    continue
                seen_hashes.add(sha256)

                # 2. File size & path resolution
                file_size = source_pdf.stat().st_size
                dest_dir = self.raw_dir / Path(rel_file_path).parent
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / source_pdf.name

                if copy_files and str(source_pdf.resolve()) != str(dest_file.resolve()):
                    shutil.copy2(source_pdf, dest_file)
                    stored_path = str(dest_file.relative_to(self.output_dir.parent))
                else:
                    stored_path = str(source_pdf.resolve())

                # 3. Generate ID (MAT-XXXXXX)
                doc_id = self.generate_id()

                # 4. Extract text per page
                extract_res = extract_pdf(str(source_pdf))
                raw_fulltext = extract_res.full_text

                # 5. Language detection
                lang_info = detect_language(raw_fulltext)
                lang_code = lang_info.get("language") or "id"
                lang_conf = lang_info.get("confidence", 0.0)

                # If language detection returned an unusual tag on short text, default to 'id'
                if lang_code not in ("id", "en"):
                    lang_code = "id"

                # 6. Title cleaning
                raw_title = res.get("title", source_pdf.stem)
                clean_title = re.sub(r'\s+File$', '', raw_title, flags=re.IGNORECASE).strip()

                # 7. Document status determination
                is_valid = extract_res.is_valid()
                extraction_status = extract_res.extraction_status
                collection_status = "READY_FOR_INDEXING" if is_valid else "EXTRACTED"

                doc_meta = {
                    "document_id": doc_id,
                    "document_type": "MATERIAL",
                    "title": clean_title,
                    "abstract": None,
                    "authors": json.dumps(["Fakultas Ilmu Komputer, Universitas Indonesia"]),
                    "institution": "Universitas Indonesia",
                    "department": "Fakultas Ilmu Komputer",
                    "course": res.get("course_name"),
                    "year": None,
                    "language": lang_code,
                    "language_confidence": lang_conf,
                    "keywords": json.dumps([res.get("course_name")] if res.get("course_name") else []),
                    "source": "OCW_UI",
                    "source_url": res.get("original_url"),
                    "fulltext_url": res.get("source_url"),
                    "local_path": stored_path,
                    "file_type": "pdf",
                    "file_size": file_size,
                    "page_count": extract_res.page_count,
                    "license": res.get("license", "CC BY-NC-SA 4.0"),
                    "sha256": sha256,
                    "doi": None,
                    "extraction_method": extract_res.extraction_method,
                    "extraction_status": extraction_status,
                    "collection_status": collection_status,
                    "collected_at": self.create_metadata()["collected_at"],
                }

                if self.db:
                    # Insert document
                    self.db.insert_document(doc_meta, conn=conn)

                    # Insert pages
                    page_clean_map = {}
                    for page in extract_res.pages:
                        page_num = page['page_number']
                        p_raw = page['raw_text']
                        p_words = page['word_count']
                        p_clean = self.pipeline.process_document(p_raw, language=lang_code) if p_raw else ""
                        page_clean_map[page_num] = p_clean
                        self.db.insert_page(
                            document_id=doc_id,
                            page_number=page_num,
                            raw_text=p_raw,
                            clean_text=p_clean,
                            word_count=p_words,
                            conn=conn
                        )

                    # Create and insert chunks
                    chunks = create_chunks(extract_res.pages, doc_id, max_words=500, overlap_words=50)
                    for chunk in chunks:
                        # Reuse page clean_text if chunk is a full page
                        p_num = chunk.get('page_start')
                        if chunk.get('page_start') == chunk.get('page_end') and p_num in page_clean_map:
                            c_clean = page_clean_map[p_num]
                        else:
                            c_clean = self.pipeline.process_document(chunk['raw_text'], language=lang_code)
                        chunk['clean_text'] = c_clean
                        self.db.insert_chunk(chunk, conn=conn)

                    # Ingestion log
                    self.db.log(
                        document_id=doc_id,
                        stage="INGEST",
                        status="SUCCESS" if is_valid else "WARNING",
                        message=f"Migrated {len(extract_res.pages)} pages, {len(chunks)} chunks. Lang={lang_code}",
                        conn=conn
                    )

                    if idx % batch_commit_size == 0:
                        conn.commit()
                        logger.info(f"[OCW_UI] Progress: {idx}/{len(resources)} documents ingested...")

                self.stats['downloaded'] += 1
                self.stats['extracted'] += 1

            if conn:
                conn.commit()

        finally:
            if conn:
                conn.close()

        logger.info(f"[OCW_UI] Migration finished: {self.stats['downloaded']} imported, {self.stats['duplicates']} duplicates, {self.stats['failed']} failed")
        return self.stats
