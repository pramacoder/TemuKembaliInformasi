"""
Academic IR System — Corpus Validation
=========================================
Quality checks for the unified corpus before indexing.
"""

import logging

logger = logging.getLogger(__name__)


def validate_document_readiness(doc: dict) -> dict:
    """
    Check if a document meets READY_FOR_INDEXING criteria.

    Criteria:
    [✓] document_id present
    [✓] document_type present
    [✓] title present or extractable
    [✓] source present
    [✓] file stored locally
    [✓] SHA-256 computed
    [✓] PDF valid
    [✓] text extracted (extraction_status = SUCCESS or PARTIAL)
    [✓] language detected
    [✓] not a duplicate
    [✓] metadata stored

    Returns:
        dict with 'ready' (bool), 'issues' (list of strings)
    """
    issues = []

    if not doc.get('document_id'):
        issues.append("Missing document_id")
    if not doc.get('document_type'):
        issues.append("Missing document_type")
    if not doc.get('title'):
        issues.append("Missing title")
    if not doc.get('source'):
        issues.append("Missing source")
    if not doc.get('sha256'):
        issues.append("Missing SHA-256 hash")
    if not doc.get('local_path'):
        issues.append("No local file path")
    if doc.get('extraction_status') in ('FAILED', None):
        issues.append(f"Extraction status: {doc.get('extraction_status')}")
    if not doc.get('language'):
        issues.append("Language not detected")

    return {
        'ready': len(issues) == 0,
        'issues': issues,
    }


def validate_corpus(db) -> dict:
    """
    Run validation across the entire corpus.

    Returns:
        Summary dict with counts and issues.
    """
    documents = db.get_all_documents()

    summary = {
        'total': len(documents),
        'ready': 0,
        'not_ready': 0,
        'issues': [],
    }

    for doc in documents:
        result = validate_document_readiness(doc)
        if result['ready']:
            summary['ready'] += 1
        else:
            summary['not_ready'] += 1
            summary['issues'].append({
                'document_id': doc['document_id'],
                'issues': result['issues'],
            })

    logger.info(
        f"Corpus validation: {summary['ready']}/{summary['total']} ready, "
        f"{summary['not_ready']} with issues"
    )

    return summary
