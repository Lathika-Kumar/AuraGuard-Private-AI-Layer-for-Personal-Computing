from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.core.config import settings


def get_db_connection() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def _add_column_if_missing(conn: sqlite3.Connection, table_name: str, column_name: str, column_definition: str) -> None:
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    if not any(column[1] == column_name for column in columns):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")


def init_db() -> None:
    db_path = settings.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                mime_type TEXT,
                file_size INTEGER,
                pages INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                page_number INTEGER NOT NULL DEFAULT 1,
                text TEXT NOT NULL,
                character_count INTEGER NOT NULL DEFAULT 0,
                embedding BLOB,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_document_id INTEGER,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_confirmed INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                source_document_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS privacy_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                source TEXT,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_faiss_mappings (
                vector_id INTEGER PRIMARY KEY,
                memory_id INTEGER UNIQUE NOT NULL
            )
            """
        )

        _add_column_if_missing(conn, "documents", "pages", "pages INTEGER DEFAULT 0")
        _add_column_if_missing(conn, "document_chunks", "page_number", "page_number INTEGER NOT NULL DEFAULT 1")
        _add_column_if_missing(conn, "document_chunks", "character_count", "character_count INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "document_chunks", "embedding", "embedding BLOB")

        _add_column_if_missing(conn, "memories", "source", "source TEXT DEFAULT 'user'")
        _add_column_if_missing(conn, "memories", "importance", "importance REAL DEFAULT 0.5")
        _add_column_if_missing(conn, "memories", "confidence", "confidence REAL DEFAULT 1.0")
        _add_column_if_missing(conn, "memories", "privacy_level", "privacy_level TEXT DEFAULT 'PERSONAL'")
        _add_column_if_missing(conn, "memories", "updated_at", "updated_at TEXT")
        _add_column_if_missing(conn, "memories", "expires_at", "expires_at TEXT")
        _add_column_if_missing(conn, "memories", "status", "status TEXT NOT NULL DEFAULT 'active'")
        _add_column_if_missing(conn, "memories", "embedding", "embedding BLOB")

        _add_column_if_missing(conn, "privacy_events", "entity_type", "entity_type TEXT")
        _add_column_if_missing(conn, "privacy_events", "action", "action TEXT")

        conn.commit()

        # Phase 5: Automatically & idempotently migrate plaintext data to AES-256-GCM
        from app.database.migration import migrate_to_encrypted_storage
        migrate_to_encrypted_storage(conn)


def get_dashboard_stats() -> dict[str, Any]:
    with get_db_connection() as conn:
        documents = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        memories = conn.execute("SELECT COUNT(*) FROM memories WHERE status = 'active'").fetchone()[0]
        privacy_events = conn.execute("SELECT COUNT(*) FROM privacy_events").fetchone()[0]
        return {
            "documents_indexed": documents,
            "memories_stored": memories,
            "privacy_events": privacy_events,
            "privacy_mode": settings.privacy_mode,
        }
