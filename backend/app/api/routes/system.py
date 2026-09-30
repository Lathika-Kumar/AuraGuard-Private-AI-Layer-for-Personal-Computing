from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from app.services.hardware_service import HardwareService

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/hardware")
async def get_hardware() -> dict[str, Any]:
    """Returns detected system hardware specifications (OS, CPU, GPU, RAM, Snapdragon status, NPU status)."""
    return HardwareService.get_hardware_info()


@router.get("/models")
async def get_models() -> dict[str, Any]:
    """Returns actual metadata for configured and active models (embedding and LLM)."""
    return HardwareService.get_models_info()


@router.get("/ai-runtime")
async def get_ai_runtime() -> dict[str, Any]:
    """Returns AI runtime status, active models, active execution provider, and fallback details."""
    return HardwareService.get_ai_runtime_info()


@router.get("/dashboard-stats")
async def get_dashboard_stats_endpoint() -> dict[str, Any]:
    """Returns real database counts for documents, memories, and privacy events."""
    from app.database.database import get_dashboard_stats
    stats = get_dashboard_stats()
    runtime = HardwareService.get_ai_runtime_info()
    stats["active_execution_provider"] = runtime.get("active_execution_provider", "CPUExecutionProvider")
    stats["qnn_available"] = runtime.get("qnn_available", False)
    stats["external_calls"] = 0
    return stats


@router.get("/ai-runtime/verify")
async def verify_ai_runtime() -> dict[str, Any]:
    """Dedicated runtime verification for Qualcomm QNN and Snapdragon NPU execution.

    Returns empirical status of hardware detection, QNN provider availability, session loading,
    model loading, and actual tensor inference execution.
    """
    return HardwareService.verify_qnn_runtime()


@router.get("/security")
async def get_security_status() -> dict[str, Any]:
    """Returns local storage encryption status, algorithm, key protection method, and privacy boundaries.

    Guarantees no raw keys, ciphertext, or private data are ever exposed.
    """
    from app.security.encryption_service import encryption_service
    from app.database.database import get_db_connection
    meta = encryption_service.get_security_metadata()
    meta["local_ai"] = "Enabled"
    meta["cloud_inference"] = "Disabled"
    meta["local_only"] = True
    meta["cloud_leakage"] = False

    with get_db_connection() as conn:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        mem_count = conn.execute("SELECT COUNT(*) FROM memories WHERE status = 'active'").fetchone()[0]
        priv_events = conn.execute("SELECT COUNT(*) FROM privacy_events").fetchone()[0]
        blocked = conn.execute("SELECT COUNT(*) FROM privacy_events WHERE action = 'BLOCK' OR event_type LIKE '%BLOCKED%'").fetchone()[0]

    meta["privacy_events"] = priv_events
    meta["blocked_requests"] = blocked
    meta["encrypted_memories"] = mem_count
    meta["encrypted_documents"] = doc_count
    return meta
