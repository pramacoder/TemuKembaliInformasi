"""
Academic IR System — CORE API Collector
=========================================
Collector for open access research papers via CORE API v3 (https://core.ac.uk).
Harvests peer-reviewed papers on IR, NLP, and Text Mining topics.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .base import BaseCollector
from ..extraction.pdf import extract_pdf
from ..indexing.chunker import create_chunks
from ..normalization.language import detect_language
from ..preprocessing.pipeline import PreprocessingPipeline

logger = logging.getLogger(__name__)


class CORECollector(BaseCollector):
    """Collector for academic research papers using CORE API v3."""

    def __init__(self, config: dict, output_dir: str = "data", db=None, api_key: str = None):
        super().__init__(
            source_name="CORE",
            document_type="RESEARCH",
            config=config,
            output_dir=output_dir,
            db=db,
        )
        self.base_url = config.get("base_url", "https://api.core.ac.uk/v3/")
        self.topics = config.get("topics", [
            "information retrieval",
            "natural language processing",
            "text mining",
            "vector space model",
            "tf-idf ranking"
        ])
        
        # API Key from parameter, env var, or config
        env_var_name = config.get("api_key_env", "CORE_API_KEY")
        self.api_key = api_key or os.getenv(env_var_name) or config.get("api_key")
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        else:
            logger.warning(
                "[CORE] No API key found. Set CORE_API_KEY in .env or pass api_key. "
                "Get a free API key at https://core.ac.uk/services/api"
            )

        self.pipeline = PreprocessingPipeline(default_language="en")

    def is_configured(self) -> bool:
        """Check whether the collector has a valid API key configured."""
        return bool(self.api_key and self.api_key.strip())

    def discover(self, query: str = None, limit: int = 50) -> list:
        """
        Search CORE API v3 for works matching topic queries.

        Args:
            query: Custom search query, or iterates through configured topics
            limit: Maximum works to discover per topic

        Returns:
            list of discovered work records
        """
        if not self.is_configured():
            logger.error("[CORE] Cannot discover papers: CORE_API_KEY is not configured.")
            return []

        search_url = f"{self.base_url.rstrip('/')}/search/works"
        queries = [query] if query else self.topics
        discovered_records = []

        for q in queries:
            if len(discovered_records) >= limit:
                break
            logger.info(f"[CORE] Searching for query: '{q}' (limit={limit})")
            params = {
                "q": q,
                "limit": min(limit, 100),
            }
            try:
                resp = self.fetch_url(search_url, params=params)
                data = resp.json()
                results = data.get("results", [])

                for item in results:
                    download_url = item.get("downloadUrl")
                    title = item.get("title")
                    if title:
                        discovered_records.append({
                            "core_id": item.get("id"),
                            "title": title,
                            "abstract": item.get("abstract"),
                            "authors": [a.get("name") for a in item.get("authors", []) if a.get("name")],
                            "year": item.get("yearPublished"),
                            "download_url": download_url,
                            "doi": item.get("doi"),
                            "query_topic": q,
                        })

                logger.info(f"[CORE] Found {len(results)} works for '{q}'")

            except Exception as e:
                logger.error(f"[CORE] Discovery failed for '{q}': {e}")

        self.stats['discovered'] = len(discovered_records)
        return discovered_records

    def collect(self, limit: int = 50) -> list:
        """
        Execute full collection: discover -> download -> extract -> chunk -> index in DB.

        Args:
            limit: Total maximum papers to download and ingest

        Returns:
            list of collected document metadata dicts
        """
        if not self.is_configured():
            logger.warning("[CORE] Skipping collection: CORE_API_KEY not configured.")
            return []

        discovered = self.discover(limit=limit)
        if not discovered:
            return []

        collected_docs = []
        conn = self.db.get_connection() if self.db else None

        try:
            for item in discovered:
                if len(collected_docs) >= limit:
                    break

                download_url = item.get("download_url")
                if not download_url:
                    continue

                core_id = str(item.get("core_id", "doc"))
                safe_title = "".join(c for c in item.get("title", "")[:30] if c.isalnum() or c in " _-").strip()
                pdf_filename = f"core_{core_id}_{safe_title}.pdf"
                dest_path = self.raw_dir / pdf_filename

                # 1. Download PDF
                logger.info(f"[CORE] Downloading: {item['title'][:60]}...")
                success = self.download_file(download_url, dest_path)
                if not success:
                    self.stats['failed'] += 1
                    continue

                # 2. SHA-256 and duplicate check
                sha256 = self.compute_sha256(dest_path)
                if self.db and self.db.check_duplicate(sha256):
                    logger.info(f"[CORE] Duplicate hash {sha256[:8]}..., skipping.")
                    self.stats['duplicates'] += 1
                    dest_path.unlink(missing_ok=True)
                    continue

                # 3. Extract text
                extract_res = extract_pdf(str(dest_path))
                if not extract_res.is_valid():
                    logger.warning(f"[CORE] Extraction produced insufficient text for {dest_path.name}")

                doc_id = self.generate_id()
                raw_fulltext = extract_res.full_text

                # 4. Language detection
                lang_info = detect_language(raw_fulltext)
                lang_code = lang_info.get("language") or "en"
                lang_conf = lang_info.get("confidence", 0.0)

                # 5. Insert document metadata
                doc_meta = {
                    "document_id": doc_id,
                    "document_type": "RESEARCH",
                    "title": item.get("title"),
                    "abstract": item.get("abstract"),
                    "authors": json.dumps(item.get("authors", [])),
                    "institution": None,
                    "department": None,
                    "course": None,
                    "year": item.get("year"),
                    "language": lang_code,
                    "language_confidence": lang_conf,
                    "keywords": json.dumps([item.get("query_topic")] if item.get("query_topic") else []),
                    "source": "CORE",
                    "source_url": f"https://core.ac.uk/works/{core_id}",
                    "fulltext_url": download_url,
                    "local_path": str(dest_path.relative_to(self.output_dir.parent)),
                    "file_type": "pdf",
                    "file_size": dest_path.stat().st_size,
                    "page_count": extract_res.page_count,
                    "license": "Open Access",
                    "sha256": sha256,
                    "doi": item.get("doi"),
                    "extraction_method": extract_res.extraction_method,
                    "extraction_status": extract_res.extraction_status,
                    "collection_status": "READY_FOR_INDEXING" if extract_res.is_valid() else "EXTRACTED",
                    "collected_at": self.create_metadata()["collected_at"],
                }

                if self.db:
                    self.db.insert_document(doc_meta, conn=conn)

                    # Insert pages
                    page_clean_map = {}
                    for page in extract_res.pages:
                        p_num = page['page_number']
                        p_raw = page['raw_text']
                        p_clean = self.pipeline.process_document(p_raw, language=lang_code) if p_raw else ""
                        page_clean_map[p_num] = p_clean
                        self.db.insert_page(
                            document_id=doc_id,
                            page_number=p_num,
                            raw_text=p_raw,
                            clean_text=p_clean,
                            word_count=page['word_count'],
                            conn=conn
                        )

                    # Insert chunks
                    chunks = create_chunks(extract_res.pages, doc_id, max_words=500, overlap_words=50)
                    for chunk in chunks:
                        p_num = chunk.get('page_start')
                        if chunk.get('page_start') == chunk.get('page_end') and p_num in page_clean_map:
                            c_clean = page_clean_map[p_num]
                        else:
                            c_clean = self.pipeline.process_document(chunk['raw_text'], language=lang_code)
                        chunk['clean_text'] = c_clean
                        self.db.insert_chunk(chunk, conn=conn)

                    self.db.log(
                        document_id=doc_id,
                        stage="INGEST",
                        status="SUCCESS" if extract_res.is_valid() else "WARNING",
                        message=f"CORE paper ingested: {len(extract_res.pages)} pages, {len(chunks)} chunks",
                        conn=conn
                    )
                    conn.commit()

                self.stats['downloaded'] += 1
                self.stats['extracted'] += 1
                collected_docs.append(doc_meta)

        finally:
            if conn:
                conn.close()

        logger.info(f"[CORE] Collection completed: {len(collected_docs)} papers collected.")
        return collected_docs
