from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable, List, Tuple

from app.core.config import settings
from app.database.database import get_db_connection
from app.security.encryption_service import encryption_service
from pypdf import PdfReader


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pages(pdf_path: Path) -> List[str]:
    reader = PdfReader(str(pdf_path))
    pages_text = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages_text.append(text)
    return pages_text


def is_scanned_pdf(pages: List[str]) -> bool:
    # naive heuristic: if most pages have no extractable text, consider scanned
    empty = sum(1 for p in pages if not p.strip())
    return empty >= max(1, len(pages) // 2)


def clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def chunk_text(page_text: str, chunk_size: int = None, overlap: int = None) -> Iterable[str]:
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap

    tokens = page_text.split()
    if not tokens:
        return []
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + chunk_size)
        chunk = " ".join(tokens[start:end])
        chunks.append(chunk)
        start = end - overlap if end - overlap > start else end
    return chunks


def ingest_document(file_path: Path, filename: str, mime_type: str | None = None, document_id: int | None = None) -> dict:
    conn = get_db_connection()
    if document_id is not None:
        doc_id = document_id
        dest = file_path
    else:
        file_hash = compute_sha256(file_path)
        existing = conn.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,)).fetchone()
        if existing:
            return {"status": "duplicate", "document_id": existing["id"]}

        # store file into document_dir
        settings.document_dir.mkdir(parents=True, exist_ok=True)
        dest = settings.document_dir / filename
        os.replace(file_path, dest)
        file_size = dest.stat().st_size

        cur = conn.execute(
            "INSERT INTO documents (filename, file_path, file_hash, mime_type, file_size, status) VALUES (?, ?, ?, ?, ?, 'uploaded')",
            (filename, str(dest), file_hash, mime_type, file_size),
        )
        doc_id = cur.lastrowid
        conn.commit()

    # process extraction
    try:
        pages = extract_pages(dest)
        pages_count = len(pages)
        conn.execute("UPDATE documents SET pages = ?, status = 'processing' WHERE id = ?", (pages_count, doc_id))
        conn.commit()

        if is_scanned_pdf(pages):
            conn.execute("UPDATE documents SET status = 'failed', processed_at = CURRENT_TIMESTAMP WHERE id = ?", (doc_id,))
            conn.commit()
            return {"status": "failed", "reason": "scanned_or_unextractable", "document_id": doc_id}

        # iterate pages and create chunks
        chunk_index = 0
        for page_num, page_text in enumerate(pages, start=1):
            cleaned = clean_text(page_text)
            page_chunks = chunk_text(cleaned)
            for c in page_chunks:
                encrypted_chunk = encryption_service.encrypt(c)
                conn.execute(
                    "INSERT INTO document_chunks (document_id, chunk_index, page_number, text, character_count) VALUES (?, ?, ?, ?, ?)",
                    (doc_id, chunk_index, page_num, encrypted_chunk, len(c)),
                )
                chunk_index += 1
        conn.execute("UPDATE documents SET status = 'processed', processed_at = CURRENT_TIMESTAMP WHERE id = ?", (doc_id,))
        conn.commit()
        return {"status": "processed", "document_id": doc_id}
    except Exception as exc:
        conn.execute("UPDATE documents SET status = 'failed', processed_at = CURRENT_TIMESTAMP WHERE id = ?", (doc_id,))
        conn.commit()
        return {"status": "failed", "reason": str(exc), "document_id": doc_id}
