"""Bounded text-only PDF worker. Bytes arrive on stdin; no files are retained.
This process is independent of the authoritative engineering engine.
"""
import io
import json
import logging
import sys
import resource

# Bound a malformed PDF's CPU/memory in addition to the parent wall-clock timeout.
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
try:
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024, 768 * 1024 * 1024))
except (ValueError, OSError):
    pass  # Some macOS Python builds do not support RLIMIT_AS; parent timeout still applies.
logging.disable(logging.CRITICAL)


def extract(data):
    from pypdf import PdfReader
    if not data.startswith(b'%PDF-'):
        return {'error': 'INVALID_PDF'}
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted:
        return {'error': 'ENCRYPTED_PDF'}
    if not 0 < len(reader.pages) <= 40:
        return {'error': 'PDF_PAGE_LIMIT'}
    pages = []
    total = 0
    for index, page in enumerate(reader.pages):
        # extract_text reads content streams, never JavaScript, attachments or actions.
        text = page.extract_text() or ''
        total += len(text)
        if total > 60000:
            return {'error': 'PDF_TEXT_LIMIT'}
        pages.append({'page': index + 1, 'text': text})
    if not any(any(c.isalnum() for c in p['text']) for p in pages):
        return {'error': 'PDF_NO_TEXT'}
    return {'pages': pages, 'empty_pages': [p['page'] for p in pages if not p['text'].strip()]}


if __name__ == '__main__':
    try:
        data = sys.stdin.buffer.read(5 * 1024 * 1024 + 1)
        result = {'error': 'PDF_SIZE_LIMIT'} if len(data) > 5 * 1024 * 1024 else extract(data)
    except ImportError:
        result = {'error': 'PDF_NOT_CONFIGURED'}
    except Exception:
        result = {'error': 'INVALID_PDF'}
    print(json.dumps(result, ensure_ascii=True))
