"""
Academic IR System — DOAJ (Directory of Open Access Journals) Collector
=======================================================================
Harvests peer-reviewed open access research articles via DOAJ REST API.
Does not require any API key.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote

from .base import BaseCollector
from ..extraction.pdf import extract_pdf
from ..indexing.chunker import create_chunks
from ..normalization.language import detect_language
from ..preprocessing.pipeline import PreprocessingPipeline

logger = logging.getLogger(__name__)


class DOAJCollector(BaseCollector):
    """Collector for academic articles from Directory of Open Access Journals."""

    def __init__(self, config: dict, output_dir: str = "data", db=None):
        super().__init__(
            source_name="DOAJ",
            document_type="RESEARCH",
            config=config,
            output_dir=output_dir,
            db=db,
        )
        self.api_endpoint = "https://doaj.org/api/search/articles"
        self.topics = config.get("topics", [
            "information retrieval",
            "natural language processing",
            "text mining",
        ])
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })
        self.pipeline = PreprocessingPipeline(default_language="en")

    def discover(self, query: str = None, limit: int = 50) -> list:
        """
        Discover research articles matching queries via DOAJ search API.

        Args:
            query: Custom search query, or iterates through configured topics
            limit: Maximum articles to discover

        Returns:
            list of discovered article records
        """
        queries = [query] if query else self.topics
        discovered_articles = []
        page_size = min(limit, 50)

        for q in queries:
            logger.info(f"[DOAJ] Querying articles for: '{q}'")
            encoded_query = quote(q)
            url = f"{self.api_endpoint}/{encoded_query}?page=1&pageSize={page_size}"

            try:
                resp = self.fetch_url(url)
                data = resp.json()
                results = data.get("results", [])

                for item in results:
                    bib = item.get("bibjson", {})
                    title = bib.get("title")
                    if not title:
                        continue

                    # Look for PDF fulltext link
                    pdf_url = None
                    links = bib.get("link", [])
                    for l in links:
                        content_type = l.get("content_type", "").lower()
                        link_url = l.get("url", "")
                        if "pdf" in content_type or link_url.lower().endswith(".pdf"):
                            pdf_url = link_url
                            break
                    if not pdf_url and links:
                        pdf_url = links[0].get("url")

                    # Authors
                    author_names = [a.get("name") for a in bib.get("author", []) if a.get("name")]

                    # DOI
                    doi = None
                    for identifier in bib.get("identifier", []):
                        if identifier.get("type", "").lower() == "doi":
                            doi = identifier.get("id")
                            break

                    discovered_articles.append({
                        "doaj_id": item.get("id"),
                        "title": title,
                        "abstract": bib.get("abstract"),
                        "authors": author_names,
                        "year": bib.get("year"),
                        "journal": bib.get("journal", {}).get("title"),
                        "keywords": bib.get("keywords", []),
                        "pdf_url": pdf_url,
                        "doi": doi,
                        "query_topic": q,
                    })

                logger.info(f"[DOAJ] Discovered {len(results)} articles for '{q}'")

            except Exception as e:
                logger.error(f"[DOAJ] Query failed for '{q}': {e}")

        self.stats['discovered'] = len(discovered_articles)
        return discovered_articles

    def collect(self, limit: int = 50) -> list:
        """
        Download, extract, chunk, and index articles from DOAJ.
        """
        discovered = self.discover(limit=limit)
        if not discovered:
            return []

        collected_docs = []
        conn = self.db.get_connection() if self.db else None

        try:
            for item in discovered:
                if len(collected_docs) >= limit:
                    break

                pdf_url = item.get("pdf_url")
                if not pdf_url:
                    continue

                doaj_id = item.get("doaj_id", "art")
                clean_title_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', item.get("title", "")[:30])
                dest_file = self.raw_dir / f"doaj_{doaj_id}_{clean_title_slug}.pdf"

                # 1. Download
                logger.info(f"[DOAJ] Downloading: {item['title'][:60]}...")
                success = self.download_file(pdf_url, dest_file)
                if not success:
                    self.stats['failed'] += 1
                    continue

                # 2. SHA-256 and duplicate check
                sha256 = self.compute_sha256(dest_file)
                if self.db and self.db.check_duplicate(sha256):
                    logger.info(f"[DOAJ] Duplicate detected (hash={sha256[:8]}...), skipping.")
                    self.stats['duplicates'] += 1
                    dest_file.unlink(missing_ok=True)
                    continue

                # 3. Extract text
                extract_res = extract_pdf(str(dest_file))
                doc_id = self.generate_id()
                raw_fulltext = extract_res.full_text

                # 4. Language detection
                lang_info = detect_language(raw_fulltext)
                lang_code = lang_info.get("language") or "en"
                lang_conf = lang_info.get("confidence", 0.0)

                # 5. Metadata
                doc_meta = {
                    "document_id": doc_id,
                    "document_type": "RESEARCH",
                    "title": item.get("title"),
                    "abstract": item.get("abstract"),
                    "authors": json.dumps(item.get("authors", [])),
                    "institution": item.get("journal"),
                    "department": None,
                    "course": None,
                    "year": item.get("year"),
                    "language": lang_code,
                    "language_confidence": lang_conf,
                    "keywords": json.dumps(item.get("keywords", [])),
                    "source": "DOAJ",
                    "source_url": f"https://doaj.org/article/{doaj_id}",
                    "fulltext_url": pdf_url,
                    "local_path": str(dest_file.relative_to(self.output_dir.parent)),
                    "file_type": "pdf",
                    "file_size": dest_file.stat().st_size,
                    "page_count": extract_res.page_count,
                    "license": "Open Access (DOAJ)",
                    "sha256": sha256,
                    "doi": item.get("doi"),
                    "extraction_method": extract_res.extraction_method,
                    "extraction_status": extract_res.extraction_status,
                    "collection_status": "READY_FOR_INDEXING" if extract_res.is_valid() else "EXTRACTED",
                    "collected_at": self.create_metadata()["collected_at"],
                }

                if self.db:
                    self.db.insert_document(doc_meta, conn=conn)

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
                        message=f"DOAJ article ingested: {len(extract_res.pages)} pages, {len(chunks)} chunks",
                        conn=conn
                    )
                    conn.commit()

                self.stats['downloaded'] += 1
                self.stats['extracted'] += 1
                collected_docs.append(doc_meta)

        finally:
            if conn:
                conn.close()

        logger.info(f"[DOAJ] Collection finished: {len(collected_docs)} articles collected.")
        return collected_docs
