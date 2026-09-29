from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple
import faiss
import numpy as np

from app.core.config import settings
from app.database.database import get_db_connection


class FaissIndex:
    def __init__(self, dim: int, namespace: str = "documents"):
        self.dim = dim
        self.namespace = namespace
        settings.vector_index_dir.mkdir(parents=True, exist_ok=True)
        if namespace == "memories":
            self.index_path = settings.memory_vector_index_path
            self.meta_path = settings.vector_index_dir / "memory_index_meta.json"
        else:
            self.index_path = settings.vector_index_path
            self.meta_path = settings.vector_index_dir / "index_meta.json"
        self._load_or_create()

    def _load_or_create(self) -> None:
        if self.index_path.exists() and self.meta_path.exists():
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                # Verify model and dimension compatibility
                if (
                    meta.get("embedding_dimension") == self.dim
                    and meta.get("embedding_model") == settings.embedding_model
                ):
                    self.index = faiss.read_index(str(self.index_path))
                    return
            except Exception:
                pass
        # Reset if missing or incompatible
        self.reset()

    def reset(self) -> None:
        """Create fresh empty index and clear file."""
        self.index = faiss.IndexFlatL2(self.dim)
        self._save()

    def add(self, vectors: List[np.ndarray]) -> int:
        if not vectors:
            return self.index.ntotal
        arr = np.vstack(vectors).astype("float32")
        self.index.add(arr)
        self._save()
        return self.index.ntotal

    def search(self, query_vector: np.ndarray, top_k: int = 4) -> Tuple[List[int], List[float]]:
        if self.index.ntotal == 0:
            return [], []
        q = np.array([query_vector], dtype="float32")
        dists, idxs = self.index.search(q, min(top_k, self.index.ntotal))
        return idxs[0].tolist(), dists[0].tolist()

    def _save(self) -> None:
        settings.vector_index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        meta = {
            "namespace": self.namespace,
            "embedding_model": settings.embedding_model,
            "embedding_dimension": self.dim,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ntotal": self.index.ntotal,
        }
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def get_metadata(self) -> dict:
        if self.meta_path.exists():
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "namespace": self.namespace,
            "embedding_model": settings.embedding_model,
            "embedding_dimension": self.dim,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ntotal": self.index.ntotal,
        }


def ensure_mapping_table(conn: sqlite3.Connection | None = None, table_name: str = "faiss_mappings") -> None:
    # Whitelist table names to prevent SQL injection
    safe_table = "memory_faiss_mappings" if table_name == "memory_faiss_mappings" else "faiss_mappings"
    id_col = "memory_id" if safe_table == "memory_faiss_mappings" else "chunk_id"
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {safe_table} (vector_id INTEGER PRIMARY KEY, {id_col} INTEGER UNIQUE NOT NULL)"
    )
    if should_close:
        conn.commit()
        conn.close()


def map_vector_to_chunk(vector_id: int, chunk_id: int, conn: sqlite3.Connection | None = None, table_name: str = "faiss_mappings") -> None:
    safe_table = "memory_faiss_mappings" if table_name == "memory_faiss_mappings" else "faiss_mappings"
    id_col = "memory_id" if safe_table == "memory_faiss_mappings" else "chunk_id"
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    conn.execute(f"INSERT OR REPLACE INTO {safe_table} (vector_id, {id_col}) VALUES (?, ?)", (vector_id, chunk_id))
    if should_close:
        conn.commit()
        conn.close()


def get_chunk_for_vector(vector_id: int, conn: sqlite3.Connection | None = None, table_name: str = "faiss_mappings") -> int | None:
    safe_table = "memory_faiss_mappings" if table_name == "memory_faiss_mappings" else "faiss_mappings"
    id_col = "memory_id" if safe_table == "memory_faiss_mappings" else "chunk_id"
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    row = conn.execute(f"SELECT {id_col} FROM {safe_table} WHERE vector_id = ?", (vector_id,)).fetchone()
    res = row[0] if row else None
    if should_close:
        conn.close()
    return res


def map_vector_to_memory(vector_id: int, memory_id: int, conn: sqlite3.Connection | None = None) -> None:
    map_vector_to_chunk(vector_id, memory_id, conn=conn, table_name="memory_faiss_mappings")


def get_memory_for_vector(vector_id: int, conn: sqlite3.Connection | None = None) -> int | None:
    return get_chunk_for_vector(vector_id, conn=conn, table_name="memory_faiss_mappings")
