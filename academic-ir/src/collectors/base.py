"""
Academic IR System — Abstract Base Collector
=============================================
All data source collectors must inherit from this base class.
Provides common functionality: rate limiting, logging, retry, hashing.
"""

import os
import time
import hashlib
import logging
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all data source collectors."""

    def __init__(self, source_name: str, document_type: str, config: dict,
                 output_dir: str = "data", db=None):
        """
        Args:
            source_name: Identifier for this source (e.g., 'OCW_UI', 'CORE')
            document_type: 'MATERIAL', 'RESEARCH', or 'THESIS'
            config: Source-specific configuration from sources.yaml
            output_dir: Base output directory for data
            db: Database instance
        """
        self.source_name = source_name
        self.document_type = document_type
        self.config = config
        self.output_dir = Path(output_dir)
        self.db = db

        # Subdirectories
        type_lower = document_type.lower()
        self.raw_dir = self.output_dir / "raw" / type_lower
        self.extracted_dir = self.output_dir / "extracted" / type_lower
        self.metadata_dir = self.output_dir / "metadata"

        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.rate_limit = config.get('rate_limit_seconds', 2)
        self.last_request_time = 0

        # HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent',
                'AcademicIR-Bot/1.0 (Academic Research Project)')
        })
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)

        # Statistics
        self.stats = {
            'discovered': 0,
            'downloaded': 0,
            'failed': 0,
            'duplicates': 0,
            'extracted': 0,
        }

    # ─── Rate Limiting ───────────────────────────────────────────────────

    def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    # ─── HTTP Helpers ────────────────────────────────────────────────────

    def fetch_url(self, url: str, **kwargs) -> requests.Response:
        """Fetch a URL with rate limiting and retry."""
        self._rate_limit_wait()

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"[{self.source_name}] Attempt {attempt}/{self.max_retries} "
                             f"failed for {url}: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # exponential backoff
                else:
                    logger.error(f"[{self.source_name}] All retries failed for {url}")
                    raise

    def download_file(self, url: str, save_path: Path) -> bool:
        """Download a file to disk. Returns True on success."""
        try:
            self._rate_limit_wait()
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # Validate content type
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.lower().endswith('.pdf'):
                logger.warning(f"[{self.source_name}] Unexpected content type: {content_type} for {url}")

            # Write to disk
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Validate file size and PDF magic bytes
            file_size = save_path.stat().st_size
            if file_size < 1024:  # less than 1KB
                logger.warning(f"[{self.source_name}] File too small ({file_size} bytes): {save_path}")
                save_path.unlink(missing_ok=True)
                return False

            with open(save_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    logger.warning(f"[{self.source_name}] File is not a valid PDF (magic bytes={header!r}): {save_path}")
                    f.close()
                    save_path.unlink(missing_ok=True)
                    return False

            return True

        except requests.RequestException as e:
            logger.error(f"[{self.source_name}] Download failed for {url}: {e}")
            return False

    # ─── Hashing ─────────────────────────────────────────────────────────

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(65536), b''):
                sha256.update(block)
        return sha256.hexdigest()

    # ─── Document ID ─────────────────────────────────────────────────────

    def get_id_prefix(self) -> str:
        """Return the ID prefix based on document type."""
        prefixes = {
            'MATERIAL': 'MAT',
            'RESEARCH': 'RES',
            'THESIS': 'THS',
        }
        return prefixes.get(self.document_type, 'DOC')

    def generate_id(self) -> str:
        """Generate the next sequential document ID."""
        prefix = self.get_id_prefix()
        if not hasattr(self, '_id_counter') or self._id_counter is None:
            if self.db:
                next_id = self.db.get_next_id(prefix)
                self._id_counter = int(next_id.split('-')[1])
            else:
                existing = list(self.raw_dir.glob('*.pdf'))
                self._id_counter = len(existing) + 1
        else:
            self._id_counter += 1
        return f"{prefix}-{self._id_counter:06d}"

    # ─── Metadata Template ───────────────────────────────────────────────

    def create_metadata(self, **kwargs) -> dict:
        """Create a metadata dict with defaults and overrides."""
        metadata = {
            'document_id': None,
            'document_type': self.document_type,
            'title': None,
            'abstract': None,
            'authors': None,
            'institution': None,
            'department': None,
            'course': None,
            'year': None,
            'language': None,
            'language_confidence': None,
            'keywords': None,
            'source': self.source_name,
            'source_url': None,
            'fulltext_url': None,
            'local_path': None,
            'file_type': 'pdf',
            'file_size': None,
            'page_count': None,
            'license': None,
            'sha256': None,
            'doi': None,
            'extraction_method': None,
            'extraction_status': None,
            'collection_status': 'DOWNLOADED',
            'collected_at': datetime.now(timezone.utc).isoformat(),
        }
        metadata.update(kwargs)
        return metadata

    # ─── Abstract Methods ────────────────────────────────────────────────

    @abstractmethod
    def discover(self) -> list:
        """
        Discover available documents from the source.
        Returns a list of discovery records (dicts) with at minimum:
            - url: source page URL
            - file_url: direct file download URL (if available)
            - title: document title
        """
        pass

    @abstractmethod
    def collect(self, limit: int = None) -> list:
        """
        Execute the full collection pipeline:
            discover → download → validate → hash → deduplicate → save metadata
        Returns a list of collected document metadata dicts.
        """
        pass

    # ─── Reporting ───────────────────────────────────────────────────────

    def report(self) -> str:
        """Generate a collection summary report."""
        lines = [
            f"{'=' * 50}",
            f"Collection Report: {self.source_name}",
            f"{'=' * 50}",
            f"Document Type:  {self.document_type}",
            f"Discovered:     {self.stats['discovered']}",
            f"Downloaded:     {self.stats['downloaded']}",
            f"Duplicates:     {self.stats['duplicates']}",
            f"Failed:         {self.stats['failed']}",
            f"Extracted:      {self.stats['extracted']}",
            f"{'=' * 50}",
        ]
        return "\n".join(lines)
