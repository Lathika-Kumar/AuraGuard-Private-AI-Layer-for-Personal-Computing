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
from app.services.ai_service import AIProvider
from app.services.remind_service import RemindService
from common import (
    get_benchmark_hardware_context,
    compute_statistics,
    save_benchmark_result,
)


def run_rag_benchmark(warmup_runs: int = 1, measurement_runs: int = 3) -> dict:
    print("=" * 60)
    print("AuraGuard Benchmark: End-to-End Local RAG Pipeline")
    print("=" * 60)

    init_db()
    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    ai = AIProvider()
    remind = RemindService()

    # Ensure at least one test memory exists for grounded multi-source retrieval benchmark
    test_mem_content = "Project AuraGuard target hardware platform is Qualcomm Snapdragon X Elite with Windows on ARM."
    try:
        remind.create_memory(content=test_mem_content, memory_type="FACT", importance=0.9)
    except Exception:
        pass

    test_queries = [
        "What is the target hardware platform for AuraGuard?",
        "Explain the private local AI architecture.",
    ]

    # Warmup
    print(f"\nPerforming {warmup_runs} warm-up run...")
    for _ in range(warmup_runs):
        _ = ai.answer(test_queries[0])

    # Measurement runs
    print(f"Executing {measurement_runs} full RAG pipeline runs...")
    total_lats_ms = []
    privacy_lats_ms = []
    embed_lats_ms = []
    doc_search_lats_ms = []
    mem_search_lats_ms = []
    llm_lats_ms = []

    for i in range(measurement_runs):
        q = test_queries[i % len(test_queries)]
        t0 = time.perf_counter()
        res = ai.answer(q)
        t1 = time.perf_counter()

        m = res.get("metrics", {})
        total_ms = (t1 - t0) * 1000.0
        total_lats_ms.append(total_ms)
        privacy_lats_ms.append((m.get("privacy_scan_latency_seconds", 0.0) + m.get("output_guard_latency_seconds", 0.0)) * 1000.0)
        embed_lats_ms.append(m.get("embedding_latency_seconds", 0.0) * 1000.0)
        doc_search_lats_ms.append(m.get("document_search_latency_seconds", 0.0) * 1000.0)
        mem_search_lats_ms.append(m.get("memory_search_latency_seconds", 0.0) * 1000.0)
        llm_lats_ms.append(m.get("llm_latency_seconds", 0.0) * 1000.0)

        print(f"  Run {i+1}: Total {total_ms:.1f} ms | LLM: {llm_lats_ms[-1]:.1f} ms | Privacy: {privacy_lats_ms[-1]:.2f} ms")

    ram_after_mb = process.memory_info().rss / (1024 * 1024)

    stats_total = compute_statistics(total_lats_ms)
    stats_privacy = compute_statistics(privacy_lats_ms)
    stats_embed = compute_statistics(embed_lats_ms)
    stats_doc = compute_statistics(doc_search_lats_ms)
    stats_mem = compute_statistics(mem_search_lats_ms)
    stats_llm = compute_statistics(llm_lats_ms)

    print("\n--- RESULTS ---")
    print(f"Total RAG Latency Mean: {stats_total['mean_ms']:.2f} ms (p95: {stats_total['p95_ms']:.2f} ms)")
    print(f"  - Privacy Engine Mean: {stats_privacy['mean_ms']:.2f} ms")
    print(f"  - Embeddings Mean:     {stats_embed['mean_ms']:.2f} ms")
    print(f"  - FAISS Doc Retrieval: {stats_doc['mean_ms']:.2f} ms")
    print(f"  - ReMind Memory Search:{stats_mem['mean_ms']:.2f} ms")
    print(f"  - Local LLM Synthesis: {stats_llm['mean_ms']:.2f} ms")
    print(f"Peak RAM:                {ram_after_mb:.1f} MB")

    result = {
        "benchmark": "end_to_end_rag",
        "hardware_context": get_benchmark_hardware_context(),
        "iterations": measurement_runs,
        "stages_ms": {
            "total_pipeline": stats_total,
            "privacy_engine": stats_privacy,
            "embedding": stats_embed,
            "document_retrieval": stats_doc,
            "memory_retrieval": stats_mem,
            "llm_generation": stats_llm,
        },
        "memory": {
            "ram_before_mb": round(ram_before_mb, 2),
            "ram_after_mb": round(ram_after_mb, 2),
            "ram_delta_mb": round(ram_after_mb - ram_before_mb, 2),
        },
    }

    save_benchmark_result("rag_benchmark.json", result)
    return result


if __name__ == "__main__":
    run_rag_benchmark()
