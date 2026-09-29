from __future__ import annotations

import time
from typing import List, Tuple
import numpy as np

from app.services.embedding_service import EmbeddingProvider
from app.services.vector_service import (
    FaissIndex,
    ensure_mapping_table,
    get_chunk_for_vector,
    map_vector_to_chunk,
)
from app.database.database import get_db_connection
from app.core.config import settings


class RetrievalService:
    def __init__(self):
        self.embedder = EmbeddingProvider()
        self.index = FaissIndex(dim=self.embedder.dimension)
        ensure_mapping_table()

    def search(self, query: str, top_k: int = 4) -> Tuple[List[dict], float, float]:
        """Search relevant chunks. Returns (results, embedding_latency, search_latency)."""
        t0 = time.time()
        q_vec = self.embedder.embed([query])[0]
        t1 = time.time()
        embedding_latency = t1 - t0

        ids, distances = self.index.search(q_vec, top_k=top_k)
        t2 = time.time()
        search_latency = t2 - t1

        results = []
        conn = get_db_connection()
        try:
            for v_id, score in zip(ids, distances):
                if v_id < 0:
                    continue
                chunk_id = get_chunk_for_vector(v_id, conn=conn)
                if chunk_id is None:
                    continue
                row = conn.execute("SELECT * FROM document_chunks WHERE id = ?", (chunk_id,)).fetchone()
                if not row:
                    continue
                # Score normalization for L2 distance on normalized embeddings
                score_norm = 1.0 / (1.0 + float(score))
                if score_norm < settings.retrieval_min_score:
                    continue
                doc = conn.execute("SELECT * FROM documents WHERE id = ?", (row["document_id"],)).fetchone()
                results.append(
                    {
                        "chunk_id": row["id"],
                        "document_id": row["document_id"],
                        "page_number": row["page_number"],
                        "text": row["text"],
                        "score": score_norm,
                        "document_filename": doc["filename"] if doc else None,
                    }
                )
        finally:
            conn.close()
        return results, embedding_latency, search_latency

    def index_document_chunks(self, document_id: int) -> int:
        conn = get_db_connection()
        try:
            rows = conn.execute(
                "SELECT id, text FROM document_chunks WHERE document_id = ? AND embedding IS NULL",
                (document_id,),
            ).fetchall()
            if not rows:
                return 0
            texts = [r["text"] for r in rows]
            vecs = self.embedder.embed(texts)
            total = self.index.add(vecs)
            start_id = total - len(vecs)
            for offset, r in enumerate(rows):
                v_id = start_id + offset
                conn.execute("UPDATE document_chunks SET embedding = ? WHERE id = ?", (vecs[offset].tobytes(), r["id"]))
                map_vector_to_chunk(v_id, r["id"], conn=conn)
            conn.commit()
            return len(rows)
        finally:
            conn.close()

    def rebuild_index(self) -> dict:
        """Re-embed all chunks with the real neural model and recreate the FAISS index."""
        conn = get_db_connection()
        try:
            rows = conn.execute("SELECT id, text FROM document_chunks ORDER BY id ASC").fetchall()
            self.index.reset()
            conn.execute("DELETE FROM faiss_mappings")
            conn.commit()

            if not rows:
                return {
                    "status": "ok",
                    "indexed_chunks": 0,
                    "embedding_model": self.embedder.model_name,
                    "embedding_dimension": self.embedder.dimension,
                    "message": "No document chunks to index.",
                }

            texts = [r["text"] for r in rows]
            t0 = time.time()
            vecs = self.embedder.embed(texts)
            t_embed = time.time() - t0

            self.index.add(vecs)
            for i, r in enumerate(rows):
                conn.execute("UPDATE document_chunks SET embedding = ? WHERE id = ?", (vecs[i].tobytes(), r["id"]))
                map_vector_to_chunk(i, r["id"], conn=conn)
            conn.commit()

            return {
                "status": "ok",
                "indexed_chunks": len(rows),
                "embedding_model": self.embedder.model_name,
                "embedding_dimension": self.embedder.dimension,
                "embedding_latency_seconds": round(t_embed, 3),
                "message": f"Successfully re-indexed {len(rows)} chunks with {self.embedder.model_name}.",
            }
        finally:
            conn.close()
