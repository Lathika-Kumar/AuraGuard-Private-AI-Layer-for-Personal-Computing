from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.database.database import get_db_connection
from app.services.privacy_service import (
    PrivacyPolicyMode,
    PrivacyService,
)

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


class PrivacyAnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=100000)
    mode: Optional[str] = None


class PrivacyPolicyUpdateRequest(BaseModel):
    mode: str


@router.post("/analyze")
async def analyze_privacy(payload: PrivacyAnalyzeRequest) -> dict[str, Any]:
    """Inspects text before AI processing and returns detected sensitive entities, classifications, and proposed action."""
    result = PrivacyService.analyze(payload.text, mode=payload.mode, stage="general")
    return {
        "classification": result.classification.value,
        "entities": [e.to_dict(mask_value=False) for e in result.entities],
        "allowed": result.allowed,
        "policy_mode": result.policy_mode,
        "redacted_text": result.redacted_text,
        "block_reason": result.block_reason,
    }


@router.get("/events")
async def list_privacy_events(limit: int = 50, offset: int = 0) -> List[dict[str, Any]]:
    """Returns audit log of privacy events without ever exposing sensitive secret values."""
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, event_type, severity, source, description, entity_type, action, created_at, resolved
            FROM privacy_events
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (max(1, min(100, limit)), max(0, offset)),
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/stats")
async def get_privacy_stats() -> dict[str, Any]:
    """Returns aggregate privacy metrics."""
    with get_db_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM privacy_events").fetchone()[0]
        blocked = conn.execute("SELECT COUNT(*) FROM privacy_events WHERE action = 'BLOCK' OR event_type LIKE '%BLOCKED%'").fetchone()[0]
        redacted = conn.execute("SELECT COUNT(*) FROM privacy_events WHERE action = 'REDACT' OR event_type LIKE '%REDACTED%'").fetchone()[0]
        
        # Entity breakdown
        entity_rows = conn.execute(
            "SELECT entity_type, COUNT(*) as cnt FROM privacy_events WHERE entity_type IS NOT NULL GROUP BY entity_type ORDER BY cnt DESC"
        ).fetchall()
        entity_breakdown = {r["entity_type"]: r["cnt"] for r in entity_rows}

    return {
        "total_events": total,
        "blocked_events": blocked,
        "redacted_events": redacted,
        "entity_breakdown": entity_breakdown,
        "policy_mode": settings.privacy_mode,
        "local_processing": "100%",
        "external_network_calls": 0,
    }


@router.get("/policy")
async def get_privacy_policy() -> dict[str, Any]:
    """Returns the active privacy policy mode and rules."""
    return {
        "mode": settings.privacy_mode,
        "available_modes": [m.value for m in PrivacyPolicyMode],
        "rules": {
            "strict": {
                "HIGHLY_SENSITIVE": "BLOCK",
                "SENSITIVE": "REDACT",
                "PERSONAL": "REDACT",
                "description": "Maximum security. Blocks all credentials and redacts any personal identifiers.",
            },
            "balanced": {
                "HIGHLY_SENSITIVE": "BLOCK",
                "SENSITIVE": "REDACT",
                "PERSONAL": "WARN on input / REDACT in output & context",
                "description": "Default mode. Blocks secrets and credentials, redacts sensitive context, warns on personal queries.",
            },
            "permissive": {
                "HIGHLY_SENSITIVE": "REDACT",
                "SENSITIVE": "WARN",
                "PERSONAL": "ALLOW",
                "description": "Permissive mode for debugging. Retains non-secret personal information.",
            },
        },
    }


@router.post("/policy")
async def update_privacy_policy(payload: PrivacyPolicyUpdateRequest) -> dict[str, Any]:
    """Updates the active privacy policy mode."""
    mode = payload.mode.lower().strip()
    if mode not in ("strict", "balanced", "permissive"):
        raise HTTPException(status_code=400, detail="Invalid privacy mode. Must be 'strict', 'balanced', or 'permissive'.")
    settings.privacy_mode = mode
    return {"status": "ok", "mode": settings.privacy_mode}
