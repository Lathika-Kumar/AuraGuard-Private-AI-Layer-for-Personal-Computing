from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from app.core.config import settings
from app.database.database import get_db_connection
from app.services.embedding_service import EmbeddingProvider
from app.services.privacy_service import PrivacyAction, PrivacyClassification, PrivacyService
from app.services.vector_service import (
    FaissIndex,
    ensure_mapping_table,
    get_memory_for_vector,
    map_vector_to_memory,
)
from app.security.encryption_service import encryption_service

VALID_MEMORY_TYPES = {"FACT", "PREFERENCE", "TASK", "GOAL", "NOTE", "CONTEXT"}
VALID_STATUSES = {"active", "archived", "expired"}


class RemindService:
    """ReMind — Private Local Context & Memory Engine.
    
    Provides on-device personal context management for user-approved memories.
    Enforces local-only storage, semantic retrieval, explicit user control,
    lifecycles (create, read, update, delete, archive, expire), and privacy gating.
    """

    def __init__(self):
        self.embedder = EmbeddingProvider()
        self.index = FaissIndex(dim=self.embedder.dimension, namespace="memories")
        ensure_mapping_table(table_name="memory_faiss_mappings")

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _is_expired(self, expires_at: Optional[str]) -> bool:
        if not expires_at:
            return False
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except Exception:
            return False

    def create_memory(
        self,
        content: str,
        memory_type: str = "NOTE",
        importance: float = 0.5,
        confidence: float = 1.0,
        expires_at: Optional[str] = None,
        source: str = "user",
        user_confirmed: int = 1,
    ) -> dict[str, Any]:
        """Creates an approved local memory after privacy verification."""
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Memory content cannot be empty.")

        clean_type = memory_type.upper().strip()
        if clean_type not in VALID_MEMORY_TYPES:
            raise ValueError(f"Invalid memory type '{memory_type}'. Valid types: {sorted(list(VALID_MEMORY_TYPES))}")

        importance = max(0.0, min(1.0, float(importance)))
        confidence = max(0.0, min(1.0, float(confidence)))

        # 1. Privacy Scan on Candidate Memory
        privacy_res = PrivacyService.analyze(clean_content, stage="memory_create")
        if not privacy_res.allowed:
            blocked_types = [e.type for e in privacy_res.entities if e.action == PrivacyAction.BLOCK]
            for btype in set(blocked_types):
                PrivacyService.log_event(
                    event_type="MEMORY_BLOCKED",
                    severity="HIGH",
                    source="remind",
                    description=f"Memory creation blocked due to prohibited {btype}.",
                    entity_type=btype,
                    action="BLOCK",
                )
            raise ValueError(
                f"Memory creation rejected: content contains prohibited sensitive data ({privacy_res.block_reason})."
            )

        # Determine privacy level
        privacy_level = privacy_res.classification.value

        # 2. Embed content using real local model
        vec = self.embedder.embed([clean_content])[0]

        # 3. Store in SQLite (with AES-256-GCM encryption at rest)
        encrypted_content = encryption_service.encrypt(clean_content)
        conn = get_db_connection()
        try:
            now = self._now_iso()
            cur = conn.execute(
                """
                INSERT INTO memories (
                    memory_type, content, source, importance, confidence,
                    privacy_level, created_at, updated_at, expires_at, status,
                    user_confirmed, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (
                    clean_type,
                    encrypted_content,
                    source,
                    importance,
                    confidence,
                    privacy_level,
                    now,
                    now,
                    expires_at,
                    user_confirmed,
                    vec.tobytes(),
                ),
            )
            memory_id = cur.lastrowid
            conn.commit()

            # 4. Add to Memory FAISS index and mapping table
            v_total = self.index.add([vec])
            vector_id = v_total - 1
            map_vector_to_memory(vector_id, memory_id, conn=conn)
            conn.commit()

            return self.get_memory(memory_id, conn=conn)  # type: ignore
        finally:
            conn.close()

    def get_memory(self, memory_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[dict[str, Any]]:
        should_close = False
        if conn is None:
            conn = get_db_connection()
            should_close = True
        try:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            # Remove raw blob for JSON serialization
            data.pop("embedding", None)
            data["content"] = encryption_service.decrypt(data.get("content", ""))
            data["type"] = data.get("memory_type", "NOTE")

            # Check expiration
            if data.get("status") == "active" and self._is_expired(data.get("expires_at")):
                data["status"] = "expired"
                conn.execute("UPDATE memories SET status = 'expired' WHERE id = ?", (memory_id,))
                conn.commit()

            return data
        finally:
            if should_close:
                conn.close()

    def list_memories(
        self,
        memory_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        include_expired: bool = False,
    ) -> List[dict[str, Any]]:
        """Lists stored memories with optional filtering."""
        conn = get_db_connection()
        try:
            query = "SELECT * FROM memories WHERE 1=1"
            params: List[Any] = []

            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type.upper().strip())

            if status:
                query += " AND status = ?"
                params.append(status.lower().strip())
            elif not include_expired:
                query += " AND status != 'expired'"

            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()

            search_term = search.strip().lower() if search else None
            results = []
            for r in rows:
                item = dict(r)
                item.pop("embedding", None)
                item["content"] = encryption_service.decrypt(item.get("content", ""))
                item["type"] = item.get("memory_type", "NOTE")

                # If text search requested, filter against decrypted plaintext
                if search_term and search_term not in item["content"].lower():
                    continue

                # Check expiration
                if item.get("status") == "active" and self._is_expired(item.get("expires_at")):
                    item["status"] = "expired"
                    conn.execute("UPDATE memories SET status = 'expired' WHERE id = ?", (item["id"],))
                    if not include_expired and not status:
                        continue
                results.append(item)

            conn.commit()
            return results
        finally:
            conn.close()

    def update_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        memory_type: Optional[str] = None,
        importance: Optional[float] = None,
        confidence: Optional[float] = None,
        expires_at: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        """Updates memory metadata or content. Re-indexes vectors if content changes."""
        existing = self.get_memory(memory_id)
        if not existing:
            raise KeyError(f"Memory {memory_id} not found.")

        updates = []
        params = []

        if memory_type is not None:
            clean_type = memory_type.upper().strip()
            if clean_type not in VALID_MEMORY_TYPES:
                raise ValueError(f"Invalid memory type: {memory_type}")
            updates.append("memory_type = ?")
            params.append(clean_type)

        if importance is not None:
            updates.append("importance = ?")
            params.append(max(0.0, min(1.0, float(importance))))

        if confidence is not None:
            updates.append("confidence = ?")
            params.append(max(0.0, min(1.0, float(confidence))))

        if expires_at is not None:
            updates.append("expires_at = ?")
            params.append(expires_at if expires_at else None)

        if status is not None:
            clean_status = status.lower().strip()
            if clean_status not in VALID_STATUSES:
                raise ValueError(f"Invalid status: {status}")
            updates.append("status = ?")
            params.append(clean_status)

        content_changed = False
        new_vec = None
        if content is not None and content.strip() != existing["content"]:
            clean_content = content.strip()
            # Privacy check
            privacy_res = PrivacyService.analyze(clean_content, stage="memory_create")
            if not privacy_res.allowed:
                raise ValueError(f"Memory update rejected: contains sensitive data ({privacy_res.block_reason})")
            
            new_vec = self.embedder.embed([clean_content])[0]
            encrypted_content = encryption_service.encrypt(clean_content)
            updates.append("content = ?")
            params.append(encrypted_content)
            updates.append("privacy_level = ?")
            params.append(privacy_res.classification.value)
            updates.append("embedding = ?")
            params.append(new_vec.tobytes())
            content_changed = True

        updates.append("updated_at = ?")
        params.append(self._now_iso())

        params.append(memory_id)
        conn = get_db_connection()
        try:
            conn.execute(f"UPDATE memories SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()

            # If content changed, rebuild memory FAISS index to reflect new embedding
            if content_changed:
                self.rebuild_memory_index(conn=conn)

            return self.get_memory(memory_id, conn=conn)  # type: ignore
        finally:
            conn.close()

    def archive_memory(self, memory_id: int) -> dict[str, Any]:
        """Archives a memory so it remains stored locally but is excluded from RAG retrieval."""
        return self.update_memory(memory_id, status="archived")

    def delete_memory(self, memory_id: int) -> bool:
        """Deletes a memory permanently from SQLite and clears its vector representation from FAISS.
        
        Guarantees that deleted memories can never be retrieved again.
        """
        conn = get_db_connection()
        try:
            row = conn.execute("SELECT id FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if not row:
                return False

            conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.execute("DELETE FROM memory_faiss_mappings WHERE memory_id = ?", (memory_id,))
            conn.commit()

            # Rebuild memory FAISS index to completely remove the vector
            self.rebuild_memory_index(conn=conn)
            return True
        finally:
            conn.close()

    def rebuild_memory_index(self, conn: Optional[sqlite3.Connection] = None) -> dict[str, Any]:
        """Reconstructs the memory FAISS index from all active stored memories with embeddings."""
        should_close = False
        if conn is None:
            conn = get_db_connection()
            should_close = True
        try:
            self.index.reset()
            conn.execute("DELETE FROM memory_faiss_mappings")
            conn.commit()

            rows = conn.execute(
                "SELECT id, content, embedding FROM memories WHERE status = 'active' ORDER BY id ASC"
            ).fetchall()

            if not rows:
                return {"status": "ok", "indexed_memories": 0}

            vecs_to_add = []
            for r in rows:
                if r["embedding"]:
                    import numpy as np
                    vec = np.frombuffer(r["embedding"], dtype="float32")
                else:
                    decrypted_content = encryption_service.decrypt(r["content"])
                    vec = self.embedder.embed([decrypted_content])[0]
                    conn.execute("UPDATE memories SET embedding = ? WHERE id = ?", (vec.tobytes(), r["id"]))
                vecs_to_add.append(vec)

            self.index.add(vecs_to_add)
            for offset, r in enumerate(rows):
                map_vector_to_memory(offset, r["id"], conn=conn)
            conn.commit()

            return {"status": "ok", "indexed_memories": len(rows)}
        finally:
            if should_close:
                conn.close()

    def search_memories(
        self,
        query: str,
        top_k: int = 3,
        min_importance: float = 0.0,
    ) -> Tuple[List[dict[str, Any]], float, float]:
        """Performs semantic retrieval of active, relevant memories for context augmentation.
        
        Returns (memories, embedding_latency, search_latency).
        """
        if not getattr(settings, "remind_enabled", True):
            return [], 0.0, 0.0

        t0 = time.time()
        q_vec = self.embedder.embed([query])[0]
        t1 = time.time()
        embed_lat = t1 - t0

        ids, distances = self.index.search(q_vec, top_k=top_k)
        t2 = time.time()
        search_lat = t2 - t1

        results = []
        conn = get_db_connection()
        try:
            for v_id, score in zip(ids, distances):
                if v_id < 0:
                    continue
                mem_id = get_memory_for_vector(v_id, conn=conn)
                if mem_id is None:
                    continue

                row = conn.execute("SELECT * FROM memories WHERE id = ?", (mem_id,)).fetchone()
                if not row:
                    continue

                mem = dict(row)
                mem.pop("embedding", None)
                mem["content"] = encryption_service.decrypt(mem.get("content", ""))
                mem["type"] = mem.get("memory_type", "NOTE")

                # Filter inactive, expired, or low importance
                if mem.get("status") != "active":
                    continue
                if self._is_expired(mem.get("expires_at")):
                    continue
                if float(mem.get("importance", 0.5)) < min_importance:
                    continue

                # Normalization for L2 distance on normalized embeddings
                score_norm = 1.0 / (1.0 + float(score))
                if score_norm < settings.memory_min_score:
                    continue

                mem["score"] = round(score_norm, 4)
                results.append(mem)
        finally:
            conn.close()

        return results, embed_lat, search_lat

    @staticmethod
    def calculate_expiration_timestamp(mode: str, custom_iso: Optional[str] = None) -> Optional[str]:
        """Calculates ISO expiration timestamp based on preset mode (Part 7)."""
        from datetime import datetime, timezone, timedelta
        mode_clean = mode.lower().strip()
        now = datetime.now(timezone.utc)
        if mode_clean in ("never", "none", ""):
            return None
        elif mode_clean in ("7_days", "7d", "7 days"):
            return (now + timedelta(days=7)).isoformat()
        elif mode_clean in ("30_days", "30d", "30 days"):
            return (now + timedelta(days=30)).isoformat()
        elif mode_clean in ("90_days", "90d", "90 days"):
            return (now + timedelta(days=90)).isoformat()
        elif mode_clean == "custom":
            return custom_iso
        return None

    def cleanup_expired_memories(self) -> int:
        """Finds all active memories past their expiration date and marks them expired.

        Rebuilds the FAISS memory index if any expired memories were purged from active search.
        Returns count of cleaned up memories.
        """
        conn = get_db_connection()
        try:
            rows = conn.execute("SELECT id, expires_at FROM memories WHERE status = 'active' AND expires_at IS NOT NULL").fetchall()
            expired_ids = []
            for r in rows:
                if self._is_expired(r["expires_at"]):
                    expired_ids.append(r["id"])

            if not expired_ids:
                return 0

            placeholders = ", ".join("?" for _ in expired_ids)
            conn.execute(f"UPDATE memories SET status = 'expired' WHERE id IN ({placeholders})", expired_ids)
            conn.commit()

            # Rebuild FAISS index so expired memories are purged from vector search
            self.rebuild_memory_index(conn=conn)
            return len(expired_ids)
        finally:
            conn.close()
