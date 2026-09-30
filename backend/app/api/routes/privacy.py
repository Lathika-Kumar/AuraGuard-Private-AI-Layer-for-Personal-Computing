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


from app.services.decision_service import PrivateAIDecisionService

class PrivacyPolicyUpdateRequest(BaseModel):
    mode: Optional[str] = None
    privacy_mode: Optional[str] = None
    local_processing: Optional[str] = None
    external_ai: Optional[str] = None
    memory_mode: Optional[str] = None
    sensitive_data_action: Optional[str] = None
    document_retrieval: Optional[str] = None
    automatic_memory: Optional[str] = None


class PrivacyDecisionRequest(BaseModel):
    query: str = Field(..., max_length=10000)
    policy_override: Optional[dict[str, Any]] = None


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


@router.post("/decision")
async def evaluate_decision(payload: PrivacyDecisionRequest) -> dict[str, Any]:
    """Evaluates the Private AI Decision Layer for a proposed query without running inference (Part 2)."""
    decision = PrivateAIDecisionService.evaluate(payload.query, policy_override=payload.policy_override)
    return decision.to_dict()


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


@router.get("/ledger")
async def get_privacy_ledger(limit: int = 50, event_type: Optional[str] = None) -> List[dict[str, Any]]:
    """Returns the privacy event ledger with optional event type filtering (Part 14)."""
    with get_db_connection() as conn:
        if event_type:
            rows = conn.execute(
                """
                SELECT id, event_type, severity, source, description, entity_type, action, created_at, resolved
                FROM privacy_events
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (event_type, max(1, min(100, limit))),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, event_type, severity, source, description, entity_type, action, created_at, resolved
                FROM privacy_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, min(100, limit)),),
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

    policy = PrivateAIDecisionService.get_effective_policy()
    return {
        "total_events": total,
        "blocked_events": blocked,
        "redacted_events": redacted,
        "entity_breakdown": entity_breakdown,
        "policy_mode": policy.get("privacy_mode", settings.privacy_mode),
        "local_processing": "100%",
        "external_network_calls": 0,
        "policy": policy,
    }


@router.get("/policy")
async def get_privacy_policy() -> dict[str, Any]:
    """Returns the active privacy policy mode, persisted user policy, and rules."""
    policy = PrivateAIDecisionService.get_effective_policy()
    return {
        "mode": policy.get("privacy_mode", settings.privacy_mode),
        "privacy_mode": policy.get("privacy_mode", settings.privacy_mode),
        "policy": policy,
        "available_modes": [m.value for m in PrivacyPolicyMode],
        "rules": {
            "strict": {
                "SECRET": "BLOCK",
                "HIGHLY_SENSITIVE": "BLOCK",
                "SENSITIVE": "REDACT",
                "PERSONAL": "REDACT",
                "description": "Maximum security. Blocks all credentials and redacts any personal identifiers.",
            },
            "balanced": {
                "SECRET": "BLOCK",
                "HIGHLY_SENSITIVE": "BLOCK",
                "SENSITIVE": "REDACT",
                "PERSONAL": "WARN on input / REDACT in output & context",
                "description": "Default mode. Blocks secrets and credentials, redacts sensitive context, warns on personal queries.",
            },
            "permissive": {
                "SECRET": "REDACT",
                "HIGHLY_SENSITIVE": "REDACT",
                "SENSITIVE": "WARN",
                "PERSONAL": "ALLOW",
                "description": "Permissive mode for debugging. Retains non-secret personal information.",
            },
        },
    }


@router.post("/policy")
@router.put("/policy")
async def update_privacy_policy(payload: PrivacyPolicyUpdateRequest) -> dict[str, Any]:
    """Updates the user privacy policy (Part 4)."""
    updates = {}
    mode = payload.privacy_mode or payload.mode
    if mode is not None:
        clean_mode = mode.lower().strip()
        if clean_mode not in ("strict", "balanced", "permissive"):
            raise HTTPException(status_code=400, detail="Invalid privacy mode. Must be 'strict', 'balanced', or 'permissive'.")
        updates["privacy_mode"] = clean_mode
        settings.privacy_mode = clean_mode

    for key in ("local_processing", "external_ai", "memory_mode", "sensitive_data_action", "document_retrieval", "automatic_memory"):
        val = getattr(payload, key, None)
        if val is not None:
            updates[key] = str(val).upper().strip()

    updated_policy = PrivateAIDecisionService.update_policy(updates)
    return {
        "status": "ok",
        "mode": updated_policy.get("privacy_mode", settings.privacy_mode),
        "policy": updated_policy,
    }
