from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from app.services.hardware_service import HardwareService

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/hardware")
async def get_hardware() -> dict[str, Any]:
    """Returns detected system hardware specifications (OS, CPU, GPU, RAM, Snapdragon status, NPU status)."""
    return HardwareService.get_hardware_info()


@router.get("/ai-runtime")
async def get_ai_runtime() -> dict[str, Any]:
    """Returns AI runtime status, active models, active execution provider, and fallback details."""
    return HardwareService.get_ai_runtime_info()
