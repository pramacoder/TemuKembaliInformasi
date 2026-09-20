"""
Academic IR System — Chunker
==============================
Splits page-level text into retrieval chunks.
Default strategy: 1 page = 1 chunk.
Long pages (>max_words) are split into overlapping sub-chunks.
"""

import logging

logger = logging.getLogger(__name__)


def create_chunks(pages: list, document_id: str,
                  max_words: int = 500, overlap_words: int = 50,
                  chunk_counter_start: int = 0) -> list:
    """
    Convert page-level text into retrieval chunks.

    Strategy:
    - If a page has <= max_words: the entire page becomes one chunk.
    - If a page has > max_words: split into overlapping sub-chunks.
    - Empty pages are skipped.

    Args:
        pages: List of page dicts with 'page_number', 'raw_text', 'word_count'
        document_id: Parent document ID
        max_words: Maximum words per chunk before splitting
        overlap_words: Number of overlapping words between sub-chunks
        chunk_counter_start: Starting index for chunk numbering

    Returns:
        List of chunk dicts ready for DB insertion
    """
    chunks = []
    chunk_index = chunk_counter_start

    for page in pages:
        text = page.get('raw_text', '')
        if not text or not text.strip():
            continue

        page_num = page['page_number']
        words = text.split()
        word_count = len(words)

        if word_count <= max_words:
            # Single chunk for this page
            chunk_id = f"{document_id}-C{chunk_index + 1:04d}"
            chunks.append({
                'chunk_id': chunk_id,
                'document_id': document_id,
                'page_start': page_num,
                'page_end': page_num,
                'chunk_index': chunk_index,
                'raw_text': text,
                'clean_text': None,  # filled during preprocessing
                'word_count': word_count,
            })
            chunk_index += 1
        else:
            # Split into overlapping sub-chunks
            start = 0
            while start < word_count:
                end = min(start + max_words, word_count)
                sub_text = " ".join(words[start:end])
                sub_word_count = end - start

                chunk_id = f"{document_id}-C{chunk_index + 1:04d}"
                chunks.append({
                    'chunk_id': chunk_id,
                    'document_id': document_id,
                    'page_start': page_num,
                    'page_end': page_num,
                    'chunk_index': chunk_index,
                    'raw_text': sub_text,
                    'clean_text': None,
                    'word_count': sub_word_count,
                })
                chunk_index += 1

                # Move start forward, accounting for overlap
                start = end - overlap_words
                if start >= word_count or end == word_count:
                    break

    logger.info(f"Created {len(chunks)} chunks for document {document_id}")
    return chunks
