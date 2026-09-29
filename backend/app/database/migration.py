from __future__ import annotations

import sqlite3
from typing import Any, Optional

from app.database.database import get_db_connection
from app.security.encryption_service import encryption_service


def migrate_to_encrypted_storage(conn: Optional[sqlite3.Connection] = None) -> dict[str, Any]:
    """Idempotently migrates existing plaintext document chunks and memories to AES-256-GCM.
    
    Verifies every encrypted record via round-trip decryption before committing.
    Rolls back automatically upon any error to guarantee zero data loss.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    chunks_migrated = 0
    memories_migrated = 0

    try:
        # Check if tables exist
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('document_chunks', 'memories')"
            ).fetchall()
        ]

        if "document_chunks" in tables:
            rows = conn.execute("SELECT id, text FROM document_chunks").fetchall()
            for r in rows:
                c_id = r[0]
                raw_text = r[1]
                if not encryption_service.is_encrypted(raw_text):
                    encrypted = encryption_service.encrypt(raw_text)
                    # Verify roundtrip decryption before updating
                    decrypted = encryption_service.decrypt(encrypted)
                    if decrypted != raw_text:
                        raise ValueError(f"Integrity check failed for chunk id {c_id}")
                    conn.execute(
                        "UPDATE document_chunks SET text = ? WHERE id = ?",
                        (encrypted, c_id),
                    )
                    chunks_migrated += 1

        if "memories" in tables:
            rows = conn.execute("SELECT id, content FROM memories").fetchall()
            for r in rows:
                m_id = r[0]
                raw_content = r[1]
                if not encryption_service.is_encrypted(raw_content):
                    encrypted = encryption_service.encrypt(raw_content)
                    decrypted = encryption_service.decrypt(encrypted)
                    if decrypted != raw_content:
                        raise ValueError(f"Integrity check failed for memory id {m_id}")
                    conn.execute(
                        "UPDATE memories SET content = ? WHERE id = ?",
                        (encrypted, m_id),
                    )
                    memories_migrated += 1

        conn.commit()
        return {
            "status": "success",
            "chunks_migrated": chunks_migrated,
            "memories_migrated": memories_migrated,
            "already_encrypted": (chunks_migrated == 0 and memories_migrated == 0),
        }
    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"Database encryption migration failed: {str(exc)}") from exc
    finally:
        if should_close:
            conn.close()
