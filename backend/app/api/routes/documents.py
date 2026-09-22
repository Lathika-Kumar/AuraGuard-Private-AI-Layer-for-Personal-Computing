from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.database.database import get_db_connection

router = APIRouter(prefix="/api", tags=["documents"])


class SearchRequest(BaseModel):
    query: str


def _validate_pdf(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    allowed_extensions = {".pdf"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF files are supported in the MVP.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file.size and file.size > max_bytes:
        raise HTTPException(status_code=413, detail="File is too large for the configured upload limit.")


@router.get("/documents")
async def list_documents() -> list[dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, filename, file_path, file_hash, mime_type, file_size, created_at, processed_at, status FROM documents ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/documents/{document_id}")
async def get_document(document_id: int) -> dict[str, Any]:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, filename, file_path, file_hash, mime_type, file_size, created_at, processed_at, status FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        return dict(row)


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    _validate_pdf(file)

    file_bytes = await file.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM documents WHERE file_hash = ?",
            (file_hash,),
        ).fetchone()
        if existing is not None:
            raise HTTPException(status_code=409, detail="This file has already been uploaded and processed.")

        safe_name = Path(file.filename).name
        content_dir = settings.data_dir / "documents"
        content_dir.mkdir(parents=True, exist_ok=True)
        destination = content_dir / safe_name

        if destination.exists():
            counter = 1
            while True:
                candidate = content_dir / f"{Path(safe_name).stem}_{counter}{Path(safe_name).suffix}"
                if not candidate.exists():
                    destination = candidate
                    break
                counter += 1

        with open(destination, "wb") as handle:
            handle.write(file_bytes)

        conn.execute(
            "INSERT INTO documents (filename, file_path, file_hash, mime_type, file_size, status) VALUES (?, ?, ?, ?, ?, 'uploaded')",
            (safe_name, str(destination), file_hash, "application/pdf", len(file_bytes)),
        )
        conn.commit()
        document_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return {
        "id": document_id,
        "filename": safe_name,
        "file_hash": file_hash,
        "status": "uploaded",
        "message": "PDF received and stored locally.",
    }


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int) -> dict[str, str]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Document not found.")

        file_path = row["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)

        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        conn.commit()

    return {"status": "deleted", "message": "Document deleted from local storage."}


@router.post("/search")
async def search_documents(payload: SearchRequest) -> dict[str, Any]:
    return {
        "answer": "I couldn't find enough relevant information in your local documents.",
        "sources": [],
        "query": payload.query,
    }
