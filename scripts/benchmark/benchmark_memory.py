from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import psutil

# Ensure backend app is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.database.database import init_db
from app.services.remind_service import RemindService
from common import (
    get_benchmark_hardware_context,
    compute_statistics,
    save_benchmark_result,
)


def run_memory_benchmark(warmup_runs: int = 5, measurement_runs: int = 20) -> dict:
    print("=" * 60)
    print("AuraGuard Benchmark: ReMind Memory & Semantic Operations")
    print("=" * 60)

    init_db()
    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    remind = RemindService()

    sample_memories = [
        "Prefers dark mode theme and concise technical explanations.",
        "Working on AuraGuard Phase 6 Snapdragon verification suite.",
        "Primary device is an HP PC targeting Qualcomm Snapdragon X Elite platform.",
        "Never commit secrets, tokens, or encryption keys to version control.",
        "Use AES-256-GCM authenticated cipher with Windows DPAPI key protection.",
    ]

    # Warmup
    print(f"\nPerforming {warmup_runs} warm-up creations & searches...")
    for i in range(warmup_runs):
        text = sample_memories[i % len(sample_memories)]
        mem = remind.create_memory(content=f"Warmup {i}: {text}", memory_type="NOTE", importance=0.5)
        _ = remind.search_memories("AuraGuard platform", top_k=2)
        remind.delete_memory(mem["id"])

    # Measurement: Create Memory (Scan + Encrypt + DB + Embed + FAISS)
    print(f"Executing {measurement_runs} encrypted memory creation runs...")
    create_lats_ms = []
    created_ids = []
    for i in range(measurement_runs):
        text = sample_memories[i % len(sample_memories)]
        t0 = time.perf_counter()
        mem = remind.create_memory(content=f"Benchmark sample {i}: {text}", memory_type="FACT", importance=0.8)
        t1 = time.perf_counter()
        create_lats_ms.append((t1 - t0) * 1000.0)
        created_ids.append(mem["id"])

    # Measurement: Search Memory (Embed + FAISS + DB + Decrypt)
    print(f"Executing {measurement_runs} encrypted semantic memory searches...")
    search_lats_ms = []
    search_queries = [
        "What encryption does AuraGuard use?",
        "What is the preferred UI theme?",
        "Which PC platform is targeted?",
    ]
    for i in range(measurement_runs):
        q = search_queries[i % len(search_queries)]
        t0 = time.perf_counter()
        _ = remind.search_memories(q, top_k=3)
        t1 = time.perf_counter()
        search_lats_ms.append((t1 - t0) * 1000.0)

    # Clean up benchmark memories
    for mid in created_ids:
        try:
            remind.delete_memory(mid)
        except Exception:
            pass

    ram_after_mb = process.memory_info().rss / (1024 * 1024)

    stats_create = compute_statistics(create_lats_ms)
    stats_search = compute_statistics(search_lats_ms)

    print("\n--- RESULTS ---")
    print(f"Memory Create (Encrypt+Index) Mean: {stats_create['mean_ms']:.2f} ms (p95: {stats_create['p95_ms']:.2f} ms)")
    print(f"Memory Search (Embed+Decrypt) Mean: {stats_search['mean_ms']:.2f} ms (p95: {stats_search['p95_ms']:.2f} ms)")
    print(f"RAM Usage:                          {ram_after_mb:.1f} MB")

    result = {
        "benchmark": "remind_memory",
        "hardware_context": get_benchmark_hardware_context(),
        "iterations": measurement_runs,
        "memory_creation": stats_create,
        "memory_search": stats_search,
        "memory": {
            "ram_before_mb": round(ram_before_mb, 2),
            "ram_after_mb": round(ram_after_mb, 2),
            "ram_delta_mb": round(ram_after_mb - ram_before_mb, 2),
        },
    }

    save_benchmark_result("memory_benchmark.json", result)
    return result


if __name__ == "__main__":
    run_memory_benchmark()
