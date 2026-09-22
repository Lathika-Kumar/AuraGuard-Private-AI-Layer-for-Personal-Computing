from __future__ import annotations

import platform
import sys
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": "AuraGuard",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "implementation": "FastAPI",
        "environment": "development",
        "safe_runtime_details": {
            "python_executable": sys.executable,
            "os": platform.system(),
        },
    }
