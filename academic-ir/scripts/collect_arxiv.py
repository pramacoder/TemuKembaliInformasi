#!/usr/bin/env python3
"""
Academic IR System — arXiv Research Harvester Script
===================================================
Collects peer-reviewed open access research papers from arXiv API
in domains of Information Retrieval (cs.IR) and NLP (cs.CL).

Usage:
    python scripts/collect_arxiv.py [--limit N] [--category CATEGORY]
"""

import sys
import os
import re
import time
import json
import yaml
import argparse
import logging
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

# Ensure academic-ir root is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Database
from src.collectors.base import BaseCollector
from src.extraction.pdf import extract_pdf
from src.indexing.chunker import create_chunks
from src.normalization.language import detect_language
from src.preprocessing.pipeline import PreprocessingPipeline
from src.validation.corpus import validate_corpus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("collect_arxiv")


class ArxivCollector(BaseCollector):
    """Collector for academic research papers from arXiv API."""

    ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

    def __init__(self, config: dict, output_dir: str = "data", db=None):
        super().__init__(
            source_name="arXiv",
            document_type="RESEARCH",
            config=config,
            output_dir=output_dir,
            db=db,
        )
        self.api_url = "http://export.arxiv.org/api/query"
        self.pipeline = PreprocessingPipeline(default_language="en")
        self.session.headers.update({
            "User-Agent": "AcademicIR-Bot/1.0 (Information Retrieval Research)"
        })

    def discover(self, search_query: str = "cat:cs.IR", limit: int = 30) -> list:
        """
        Query arXiv Atom API and extract paper metadata and PDF links with pagination.
        """
        logger.info(f"[arXiv] Querying papers with query: '{search_query}' (limit={limit})")
        discovered = []
        start_offset = 0
        batch_size = 50

        try:
            while len(discovered) < limit:
                params = {
                    "search_query": search_query,
                    "start": start_offset,
                    "max_results": min(limit - len(discovered), batch_size),
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                }

                resp = self.fetch_url(self.api_url, params=params)
                root = ET.fromstring(resp.content)
                entries = root.findall("atom:entry", self.ATOM_NS)
                if not entries:
                    logger.info(f"[arXiv] No more entries at offset {start_offset}.")
                    break

                for entry in entries:
                    if len(discovered) >= limit:
                        break

                    title_elem = entry.find("atom:title", self.ATOM_NS)
                    summary_elem = entry.find("atom:summary", self.ATOM_NS)
                    published_elem = entry.find("atom:published", self.ATOM_NS)
                    id_elem = entry.find("atom:id", self.ATOM_NS)

                    if title_elem is None or not title_elem.text:
                        continue

                    raw_title = " ".join(title_elem.text.split())
                    abstract = " ".join(summary_elem.text.split()) if summary_elem is not None and summary_elem.text else None

                    year = None
                    if published_elem is not None and published_elem.text:
                        m = re.search(r'(19|20)\d{2}', published_elem.text)
                        if m:
                            year = int(m.group())

                    authors = []
                    for author in entry.findall("atom:author", self.ATOM_NS):
                        name_elem = author.find("atom:name", self.ATOM_NS)
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())

                    # Find PDF link or construct from entry ID
                    id_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
                    arxiv_id = id_url.split("/abs/")[-1] if "/abs/" in id_url else ""
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

                    # Secondary check from link tags
                    for link in entry.findall("atom:link", self.ATOM_NS):
                        if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                            pdf_url = link.get("href")
                            break

                    categories = [
                        c.get("term") for c in entry.findall("atom:category", self.ATOM_NS)
                        if c.get("term")
                    ]

                    primary_cat = categories[0] if categories else "cs.IR"

                    discovered.append({
                        "title": raw_title,
                        "authors": authors,
                        "abstract": abstract,
                        "year": year or 2023,
                        "keywords": categories,
                        "source": f"arXiv {primary_cat}",
                        "source_url": id_url,
                        "pdf_url": pdf_url,
                        "institution": "Cornell University / arXiv",
                    })

                start_offset += len(entries)
                time.sleep(1)  # polite delay between pagination calls

            logger.info(f"[arXiv] Discovered {len(discovered)} papers matching query.")
        except Exception as e:
            logger.error(f"[arXiv] Discovery failed: {e}")

        self.stats['discovered'] = len(discovered)
        return discovered

    def collect(self, limit: int = 30, query: str = "cat:cs.IR") -> list:
        """Download, extract, chunk, and index arXiv research papers."""
        discovered = self.discover(search_query=query, limit=limit * 2)
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

                safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', item["title"][:30]).strip("_")
                dest_file = self.raw_dir / f"arxiv_{safe_title}.pdf"

                logger.info(f"[arXiv] Downloading: {item['title'][:60]}...")
                success = self.download_file(pdf_url, dest_file)
                if not success:
                    self.stats['failed'] += 1
                    continue

                sha256 = self.compute_sha256(dest_file)
                if self.db and self.db.check_duplicate(sha256):
                    logger.info(f"[arXiv] Duplicate detected, skipping.")
                    self.stats['duplicates'] += 1
                    dest_file.unlink(missing_ok=True)
                    continue

                extract_res = extract_pdf(str(dest_file))
                if not extract_res.is_valid() or extract_res.total_words < 50:
                    logger.warning(f"[arXiv] Insufficient text extracted ({extract_res.total_words} words), skipping.")
                    dest_file.unlink(missing_ok=True)
                    continue

                doc_id = self.generate_id()
                raw_fulltext = extract_res.full_text

                lang_info = detect_language(raw_fulltext)
                lang_code = lang_info.get("language") or "en"
                lang_conf = lang_info.get("confidence", 0.95)

                doc_meta = {
                    "document_id": doc_id,
                    "document_type": "RESEARCH",
                    "title": item["title"],
                    "abstract": item.get("abstract"),
                    "authors": json.dumps(item.get("authors", [])),
                    "institution": item.get("institution", "Cornell University / arXiv"),
                    "department": "Computer Science / Information Retrieval",
                    "course": None,
                    "year": item.get("year", 2023),
                    "language": lang_code,
                    "language_confidence": lang_conf,
                    "keywords": json.dumps(item.get("keywords", [])),
                    "source": item.get("source", "arXiv"),
                    "source_url": item.get("source_url"),
                    "fulltext_url": pdf_url,
                    "local_path": str(dest_file.relative_to(self.output_dir.parent)),
                    "file_type": "pdf",
                    "file_size": dest_file.stat().st_size,
                    "page_count": extract_res.page_count,
                    "license": "Open Access (arXiv.org)",
                    "sha256": sha256,
                    "doi": None,
                    "extraction_method": extract_res.extraction_method,
                    "extraction_status": extract_res.extraction_status,
                    "collection_status": "READY_FOR_INDEXING",
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
                        status="SUCCESS",
                        message=f"arXiv paper ingested: {len(extract_res.pages)} pages, {len(chunks)} chunks",
                        conn=conn
                    )
                    conn.commit()

                self.stats['downloaded'] += 1
                self.stats['extracted'] += 1
                collected_docs.append(doc_meta)
                logger.info(f"[arXiv] Successfully ingested {doc_id}: {item['title'][:50]} ({len(chunks)} chunks)")

        finally:
            if conn:
                conn.close()

        logger.info(f"[arXiv] Finished: {len(collected_docs)} research papers collected.")
        return collected_docs


def generate_manifest(db: Database, manifest_path: Path) -> int:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    docs = db.get_documents_by_type("RESEARCH")
    with open(manifest_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    return len(docs)


def main():
    parser = argparse.ArgumentParser(description="Collect research papers from arXiv API.")
    parser.add_argument("--limit", type=int, default=25, help="Number of papers to collect")
    parser.add_argument("--query", type=str, default="cat:cs.IR OR cat:cs.CL", help="arXiv query")
    parser.add_argument("--manifest", type=str, default="data/manifests/research.jsonl")

    args = parser.parse_args()

    full_db_path = PROJECT_ROOT / "database" / "academic_ir.db"
    db = Database(str(full_db_path))
    db.initialize()

    collector = ArxivCollector(
        config={"rate_limit_seconds": 2, "timeout": 45},
        output_dir=str(PROJECT_ROOT / "data"),
        db=db,
    )

    logger.info(f"Starting arXiv research collection (limit={args.limit}, query='{args.query}')...")
    collector.collect(limit=args.limit, query=args.query)

    manifest_file = PROJECT_ROOT / args.manifest
    count = generate_manifest(db, manifest_file)

    val_summary = validate_corpus(db)
    print("\n" + "=" * 60)
    print("  ARXIV RESEARCH COLLECTION SUMMARY")
    print("=" * 60)
    print(f"Total Research in DB:       {len(db.get_documents_by_type('RESEARCH'))}")
    print(f"Total Documents in DB:      {val_summary['total']}")
    print(f"Manifest Generated:         {manifest_file} ({count} entries)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
