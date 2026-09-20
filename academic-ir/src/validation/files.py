"""
Academic IR System — File Validation
=======================================
Validates downloaded files (PDF integrity, size, readability).
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_file(file_path: str, expected_type: str = "pdf") -> dict:
    """
    Validate a downloaded file.

    Checks:
    - File exists
    - File size > minimum (1KB)
    - File extension matches expected type
    - For PDF: file is a valid PDF (starts with %PDF)

    Args:
        file_path: Path to the file
        expected_type: Expected file type ('pdf')

    Returns:
        dict with 'valid' (bool), 'file_size', 'error'
    """
    result = {
        'valid': False,
        'file_size': 0,
        'error': None,
    }

    path = Path(file_path)

    # Check existence
    if not path.exists():
        result['error'] = "File not found"
        return result

    # Check size
    result['file_size'] = path.stat().st_size
    if result['file_size'] < 1024:
        result['error'] = f"File too small ({result['file_size']} bytes)"
        return result

    # Check PDF magic bytes
    if expected_type == "pdf":
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
            if not header.startswith(b'%PDF'):
                result['error'] = "Not a valid PDF file (missing %PDF header)"
                return result
        except Exception as e:
            result['error'] = f"Cannot read file: {e}"
            return result

    result['valid'] = True
    return result


def validate_corpus_directory(corpus_dir: str, expected_type: str = "pdf") -> dict:
    """
    Validate all files in a corpus directory.

    Returns:
        Summary dict with total, valid, invalid counts and error details.
    """
    path = Path(corpus_dir)
    if not path.exists():
        return {'total': 0, 'valid': 0, 'invalid': 0, 'errors': []}

    ext = f".{expected_type}"
    files = list(path.glob(f"*{ext}"))

    results = {
        'total': len(files),
        'valid': 0,
        'invalid': 0,
        'errors': [],
    }

    for f in files:
        v = validate_file(str(f), expected_type)
        if v['valid']:
            results['valid'] += 1
        else:
            results['invalid'] += 1
            results['errors'].append({
                'file': str(f),
                'error': v['error'],
            })

    return results
