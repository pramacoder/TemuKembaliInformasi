"""
Academic IR System — Institutional Repository Collector (Thesis)
=================================================================
Harvests theses and dissertations from institutional repositories
via OAI-PMH (EPrints, DSpace) or ingests deposited thesis PDFs.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

from .base import BaseCollector
from ..extraction.pdf import extract_pdf
from ..indexing.chunker import create_chunks
from ..normalization.language import detect_language
from ..preprocessing.pipeline import PreprocessingPipeline

logger = logging.getLogger(__name__)

# XML namespaces for Dublin Core OAI-PMH
OAI_NAMESPACES = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class RepositoryCollector(BaseCollector):
    """Collector for student theses and dissertations."""

    def __init__(self, config: dict, output_dir: str = "data", db=None):
        super().__init__(
            source_name="REPOSITORY",
            document_type="THESIS",
            config=config,
            output_dir=output_dir,
            db=db,
        )
        self.oai_endpoints = config.get("endpoints", [
            "http://repository.uin-malang.ac.id/cgi/oai2",
        ])
        self.pipeline = PreprocessingPipeline(default_language="id")

    def discover(self, endpoint: str = None, set_spec: str = "thesis", limit: int = 50) -> list:
        """
        Harvest Dublin Core records via OAI-PMH ListRecords verb.
        """
        target_endpoint = endpoint or (self.oai_endpoints[0] if self.oai_endpoints else "")
        if not target_endpoint:
            logger.warning("[REPOSITORY] No OAI endpoint configured.")
            return []

        logger.info(f"[REPOSITORY] Harvesting records from {target_endpoint}")
        params = {
            "verb": "ListRecords",
            "metadataPrefix": "oai_dc",
        }
        if set_spec:
            params["set"] = set_spec

        discovered = []
        try:
            resp = self.fetch_url(target_endpoint, params=params)
            root = ET.fromstring(resp.content)

            records = root.findall(".//oai:record", OAI_NAMESPACES)
            for rec in records:
                if len(discovered) >= limit:
                    break

                header = rec.find("oai:header", OAI_NAMESPACES)
                if header is not None and header.get("status") == "deleted":
                    continue

                metadata = rec.find(".//oai_dc:dc", OAI_NAMESPACES)
                if metadata is None:
                    continue

                titles = metadata.findall("dc:title", OAI_NAMESPACES)
                creators = metadata.findall("dc:creator", OAI_NAMESPACES)
                descriptions = metadata.findall("dc:description", OAI_NAMESPACES)
                dates = metadata.findall("dc:date", OAI_NAMESPACES)
                identifiers = metadata.findall("dc:identifier", OAI_NAMESPACES)
                subjects = metadata.findall("dc:subject", OAI_NAMESPACES)

                title = titles[0].text.strip() if titles and titles[0].text else None
                if not title:
                    continue

                # Look for PDF URL in dc:identifier
                pdf_url = None
                for ident in identifiers:
                    text = (ident.text or "").strip()
                    if text.lower().endswith(".pdf"):
                        pdf_url = text
                        break

                abstract = descriptions[0].text.strip() if descriptions and descriptions[0].text else None
                year = None
                if dates and dates[0].text:
                    m = re.search(r'(19|20)\d{2}', dates[0].text)
                    if m:
                        year = int(m.group())

                discovered.append({
                    "title": title,
                    "authors": [c.text.strip() for c in creators if c.text],
                    "abstract": abstract,
                    "year": year,
                    "keywords": [s.text.strip() for s in subjects if s.text],
                    "pdf_url": pdf_url,
                    "source_url": identifiers[0].text if identifiers else None,
                })

            logger.info(f"[REPOSITORY] Discovered {len(discovered)} records from OAI endpoint.")

        except Exception as e:
            logger.error(f"[REPOSITORY] OAI-PMH harvest failed: {e}")

        self.stats['discovered'] = len(discovered)
        return discovered

    def collect(self, limit: int = 50) -> list:
        """Collect theses from configured OAI-PMH endpoint."""
        discovered = self.discover(limit=limit)
        return self._ingest_records(discovered, limit=limit)

    def ingest_local_theses(self, folder_path: str, limit: int = None) -> list:
        """
        Ingest thesis PDFs from a local directory (e.g. deposited student papers).
        """
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"[REPOSITORY] Folder does not exist: {folder_path}")
            return []

        pdf_files = list(folder.glob("*.pdf"))
        if limit:
            pdf_files = pdf_files[:limit]

        logger.info(f"[REPOSITORY] Ingesting {len(pdf_files)} local thesis PDFs from {folder_path}")
        records = []
        for p in pdf_files:
            records.append({
                "title": p.stem.replace("_", " "),
                "authors": ["Penulis Skripsi/Tesis"],
                "abstract": None,
                "year": 2024,
                "keywords": ["Skripsi", "Informatika"],
                "local_file": str(p),
                "pdf_url": None,
                "source_url": None,
            })

        return self._ingest_records(records, limit=limit)

    def _ingest_records(self, records: list, limit: int = None) -> list:
        collected = []
        conn = self.db.get_connection() if self.db else None

        try:
            for item in records:
                if limit and len(collected) >= limit:
                    break

                dest_file = None
                if item.get("local_file"):
                    src = Path(item["local_file"])
                    dest_file = self.raw_dir / src.name
                    if str(src.resolve()) != str(dest_file.resolve()):
                        import shutil
                        shutil.copy2(src, dest_file)
                elif item.get("pdf_url"):
                    safe_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', item['title'][:30])
                    dest_file = self.raw_dir / f"thesis_{safe_slug}.pdf"
                    success = self.download_file(item["pdf_url"], dest_file)
                    if not success:
                        self.stats['failed'] += 1
                        continue
                else:
                    continue

                sha256 = self.compute_sha256(dest_file)
                if self.db and self.db.check_duplicate(sha256):
                    self.stats['duplicates'] += 1
                    continue

                extract_res = extract_pdf(str(dest_file))
                doc_id = self.generate_id()
                raw_fulltext = extract_res.full_text

                lang_info = detect_language(raw_fulltext)
                lang_code = lang_info.get("language") or "id"
                lang_conf = lang_info.get("confidence", 0.0)

                doc_meta = {
                    "document_id": doc_id,
                    "document_type": "THESIS",
                    "title": item.get("title"),
                    "abstract": item.get("abstract"),
                    "authors": json.dumps(item.get("authors", [])),
                    "institution": "Institutional Repository",
                    "department": "Fakultas Ilmu Komputer",
                    "course": None,
                    "year": item.get("year"),
                    "language": lang_code,
                    "language_confidence": lang_conf,
                    "keywords": json.dumps(item.get("keywords", [])),
                    "source": "REPOSITORY",
                    "source_url": item.get("source_url"),
                    "fulltext_url": item.get("pdf_url"),
                    "local_path": str(dest_file.relative_to(self.output_dir.parent)),
                    "file_type": "pdf",
                    "file_size": dest_file.stat().st_size,
                    "page_count": extract_res.page_count,
                    "license": "Academic / Educational Use",
                    "sha256": sha256,
                    "doi": None,
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
                        message=f"Thesis ingested: {len(extract_res.pages)} pages, {len(chunks)} chunks",
                        conn=conn
                    )
                    conn.commit()

                self.stats['downloaded'] += 1
                self.stats['extracted'] += 1
                collected.append(doc_meta)

        finally:
            if conn:
                conn.close()

        logger.info(f"[REPOSITORY] Finished: {len(collected)} theses ingested.")
        return collected
