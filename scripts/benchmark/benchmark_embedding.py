from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import psutil
import numpy as np

# Ensure backend app is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.embedding_service import EmbeddingProvider
from common import (
    get_benchmark_hardware_context,
    compute_statistics,
    save_benchmark_result,
)


def run_embedding_benchmark(warmup_runs: int = 5, measurement_runs: int = 20) -> dict:
    print("=" * 60)
    print("AuraGuard Benchmark: Neural Embeddings (ONNX Runtime)")
    print("=" * 60)

    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    provider = EmbeddingProvider()
    meta = provider.metadata
    print(f"Model: {meta['model_name']} | Dimension: {meta['dimension']}")
    print(f"Active Provider: {meta['active_provider']}")

    test_queries = [
        "What are the quarterly financial highlights for Project AuraGuard?",
        "How does local encrypted storage work with Windows DPAPI?",
        "Qualcomm Hexagon NPU acceleration guidelines for Snapdragon X Elite.",
        "Privacy policy enforcement for credit cards and email redaction.",
        "ReMind context intelligence and semantic memory retrieval.",
    ]

    # Warmup runs
    print(f"\nPerforming {warmup_runs} warm-up runs...")
    for i in range(warmup_runs):
        q = test_queries[i % len(test_queries)]
        _ = provider.embed([q])

    # Measurement runs: Single query
    print(f"Executing {measurement_runs} single-query inference runs...")
    single_latencies_ms = []
    for i in range(measurement_runs):
        q = test_queries[i % len(test_queries)]
        t0 = time.perf_counter()
        emb = provider.embed([q])[0]
        t1 = time.perf_counter()
        single_latencies_ms.append((t1 - t0) * 1000.0)

    # Batch throughput test (10 sentences x 5 iterations)
    batch_texts = test_queries * 2
    batch_latencies_ms = []
    for _ in range(5):
        t0 = time.perf_counter()
        _ = provider.embed(batch_texts)
        t1 = time.perf_counter()
        batch_latencies_ms.append((t1 - t0) * 1000.0)

    ram_after_mb = process.memory_info().rss / (1024 * 1024)
    avg_batch_time_s = (sum(batch_latencies_ms) / len(batch_latencies_ms)) / 1000.0
    throughput_embeds_sec = round(len(batch_texts) / avg_batch_time_s, 2) if avg_batch_time_s > 0 else 0

    stats_single = compute_statistics(single_latencies_ms)
    stats_batch = compute_statistics(batch_latencies_ms)

    print("\n--- RESULTS ---")
    print(f"Single Embed Mean:   {stats_single['mean_ms']:.2f} ms")
    print(f"Single Embed Median: {stats_single['median_ms']:.2f} ms")
    print(f"Single Embed p95:    {stats_single['p95_ms']:.2f} ms")
    print(f"Single Embed Min:    {stats_single['min_ms']:.2f} ms")
    print(f"Single Embed Max:    {stats_single['max_ms']:.2f} ms")
    print(f"Batch Throughput:    {throughput_embeds_sec} embeds/sec")
    print(f"RAM Usage:           {ram_after_mb:.1f} MB (Delta: +{ram_after_mb - ram_before_mb:.1f} MB)")

    result = {
        "benchmark": "neural_embedding",
        "hardware_context": get_benchmark_hardware_context(),
        "model": meta["model_name"],
        "runtime": meta["runtime"],
        "dimension": meta["dimension"],
        "provider": meta["active_provider"],
        "iterations": measurement_runs,
        "single_inference": stats_single,
        "batch_inference": stats_batch,
        "throughput_embeds_per_second": throughput_embeds_sec,
        "memory": {
            "ram_before_mb": round(ram_before_mb, 2),
            "ram_after_mb": round(ram_after_mb, 2),
            "ram_delta_mb": round(ram_after_mb - ram_before_mb, 2),
        },
    }

    save_benchmark_result("embedding_benchmark.json", result)
    return result


if __name__ == "__main__":
    run_embedding_benchmark()
