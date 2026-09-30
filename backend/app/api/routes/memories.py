from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.remind_service import RemindService

router = APIRouter(prefix="/api/memories", tags=["memories"])
remind_service = RemindService()


class MemoryCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    type: str = Field(default="NOTE", description="Memory type: FACT, PREFERENCE, TASK, GOAL, NOTE, CONTEXT")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    expires_at: Optional[str] = Field(default=None, description="ISO-8601 expiration timestamp")
    expiration_mode: Optional[str] = Field(default=None, description="Preset expiration: never, 7_days, 30_days, 90_days, custom")
    source: str = Field(default="user")


class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    type: Optional[str] = None
    importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    expires_at: Optional[str] = None
    status: Optional[str] = None


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    min_importance: float = Field(default=0.0, ge=0.0, le=1.0)


@router.get("")
async def list_memories(
    type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    include_expired: bool = False,
) -> List[dict[str, Any]]:
    """Lists local ReMind memories with optional filtering by type, status, or search keywords."""
    return remind_service.list_memories(
        memory_type=type,
        status=status,
        search=search,
        include_expired=include_expired,
    )


@router.post("", status_code=201)
async def create_memory(payload: MemoryCreateRequest) -> dict[str, Any]:
    """Explicitly creates a new user memory in ReMind after privacy verification."""
    expires_at = payload.expires_at
    if payload.expiration_mode and not expires_at:
        expires_at = RemindService.calculate_expiration_timestamp(payload.expiration_mode)

    try:
        return remind_service.create_memory(
            content=payload.content,
            memory_type=payload.type,
            importance=payload.importance,
            confidence=payload.confidence,
            expires_at=expires_at,
            source=payload.source,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cleanup-expired")
async def cleanup_expired() -> dict[str, Any]:
    """Finds and purges all expired memories from active vector search (Part 7)."""
    count = remind_service.cleanup_expired_memories()
    return {"status": "ok", "cleaned_up": count}


@router.get("/{memory_id}")
async def get_memory(memory_id: int) -> dict[str, Any]:
    """Retrieves a single memory by ID."""
    memory = remind_service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return memory


@router.patch("/{memory_id}")
async def update_memory(memory_id: int, payload: MemoryUpdateRequest) -> dict[str, Any]:
    """Updates a memory's content or metadata. Automatically recalculates embeddings if content changed."""
    try:
        return remind_service.update_memory(
            memory_id=memory_id,
            content=payload.content,
            memory_type=payload.type,
            importance=payload.importance,
            confidence=payload.confidence,
            expires_at=payload.expires_at,
            status=payload.status,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Memory not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int) -> dict[str, str]:
    """Deletes a memory permanently from SQLite and clears its vector representation from the FAISS index."""
    deleted = remind_service.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"status": "deleted", "message": f"Memory {memory_id} permanently removed from local storage and vector index."}


@router.post("/{memory_id}/archive")
async def archive_memory(memory_id: int) -> dict[str, Any]:
    """Archives a memory so it remains viewable locally but excluded from RAG retrieval."""
    try:
        return remind_service.archive_memory(memory_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Memory not found.")


@router.post("/search")
async def search_memories(payload: MemorySearchRequest) -> dict[str, Any]:
    """Performs semantic vector search across active local memories."""
    results, embed_lat, search_lat = remind_service.search_memories(
        query=payload.query,
        top_k=payload.top_k,
        min_importance=payload.min_importance,
    )
    return {
        "results": results,
        "query": payload.query,
        "embedding_latency_seconds": round(embed_lat, 4),
        "search_latency_seconds": round(search_lat, 4),
        "total_results": len(results),
    }
