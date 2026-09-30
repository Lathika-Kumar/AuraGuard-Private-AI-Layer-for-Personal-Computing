from __future__ import annotations

import json
import os
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List
import psutil

# Ensure backend app is on sys.path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.hardware_service import HardwareService
from app.core.config import settings

BENCHMARK_RESULTS_DIR = ROOT_DIR / "benchmarks" / "results"
BENCHMARK_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def get_benchmark_hardware_context() -> dict[str, Any]:
    """Captures real host hardware and provider context for benchmark records."""
    hw = HardwareService.get_hardware_info()
    runtime = HardwareService.get_ai_runtime_info()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cpu_brand": hw["cpu"]["brand"],
        "architecture": hw["cpu"]["architecture"],
        "physical_cores": hw["cpu"]["physical_cores"],
        "logical_cores": hw["cpu"]["logical_cores"],
        "total_ram_gb": hw["memory"]["total_gb"],
        "os_platform": hw["os"]["platform"],
        "snapdragon_detected": hw["snapdragon"]["is_snapdragon"],
        "npu_available": hw["npu"]["npu_available"],
        "qnn_available": runtime["qnn_available"],
        "execution_provider": runtime["active_execution_provider"],
    }


def compute_statistics(latencies_ms: List[float]) -> dict[str, float]:
    """Computes mean, median, p95, min, max for a sequence of latencies in ms."""
    if not latencies_ms:
        return {"mean_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}
    sorted_lats = sorted(latencies_ms)
    p95_idx = int(len(sorted_lats) * 0.95)
    p95_val = sorted_lats[min(p95_idx, len(sorted_lats) - 1)]
    return {
        "mean_ms": round(statistics.mean(latencies_ms), 4),
        "median_ms": round(statistics.median(latencies_ms), 4),
        "p95_ms": round(p95_val, 4),
        "min_ms": round(min(latencies_ms), 4),
        "max_ms": round(max(latencies_ms), 4),
    }


def save_benchmark_result(filename: str, payload: dict[str, Any]) -> Path:
    """Saves structured benchmark result to benchmarks/results/<filename>."""
    out_path = BENCHMARK_RESULTS_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[BENCHMARK] Saved results to: {out_path}")
    return out_path
