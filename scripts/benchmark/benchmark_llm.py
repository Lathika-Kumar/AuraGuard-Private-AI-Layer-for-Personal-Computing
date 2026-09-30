from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import psutil

# Ensure backend app is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.ai_service import AIProvider
from common import (
    get_benchmark_hardware_context,
    compute_statistics,
    save_benchmark_result,
)


def run_llm_benchmark(warmup_runs: int = 1, measurement_runs: int = 3) -> dict:
    print("=" * 60)
    print("AuraGuard Benchmark: Neural LLM Generation (Qwen2.5-0.5B-Instruct)")
    print("=" * 60)

    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    llm = AIProvider()
    meta = llm.metadata
    print(f"Model ID: {meta['model_id']} | Runtime: {meta['runtime']} | Device: {meta['device']}")

    sample_context = (
        "AuraGuard is a privacy-first AI layer designed for personal computing. "
        "It executes all RAG pipelines locally without cloud dependence. "
        "Encryption at rest uses AES-256-GCM authenticated cipher with keys protected by Windows DPAPI. "
        "ReMind is the personal memory module that allows users to persist preferences and facts."
    )
    sample_query = "What encryption algorithm does AuraGuard use, and how is the key protected?"

    # Warm-up run
    print(f"\nPerforming {warmup_runs} warm-up generation...")
    for _ in range(warmup_runs):
        _ = llm.generate(sample_query, sample_context)

    # Measurement runs
    print(f"Executing {measurement_runs} measurement generation runs...")
    total_latencies_ms = []
    tokens_generated_list = []
    tokens_per_sec_list = []
    ttft_latencies_ms = []

    for i in range(measurement_runs):
        # We time both prompt tokenization/TTFT and full generation
        t_start = time.perf_counter()
        
        # Measure prompt processing time (proxy for TTFT)
        inputs = llm.tokenizer(f"{sample_context}\nQuestion: {sample_query}\nAnswer:", return_tensors="pt")
        t_encoded = time.perf_counter()
        ttft_estimate_ms = (t_encoded - t_start) * 1000.0
        ttft_latencies_ms.append(ttft_estimate_ms)

        ans, gen_duration_s = llm.generate(sample_query, sample_context)
        t_finish = time.perf_counter()
        total_time_ms = (t_finish - t_start) * 1000.0
        total_latencies_ms.append(total_time_ms)

        # Count tokens generated
        ans_tokens = len(llm.tokenizer.encode(ans))
        tokens_generated_list.append(ans_tokens)
        tps = ans_tokens / gen_duration_s if gen_duration_s > 0 else 0.0
        tokens_per_sec_list.append(tps)
        print(f"  Run {i+1}: {total_time_ms:.1f} ms | Tokens: {ans_tokens} | Rate: {tps:.2f} tokens/s")

    ram_after_mb = process.memory_info().rss / (1024 * 1024)

    stats_total = compute_statistics(total_latencies_ms)
    stats_ttft = compute_statistics(ttft_latencies_ms)
    stats_tps = compute_statistics(tokens_per_sec_list)

    print("\n--- RESULTS ---")
    print(f"Generation Latency Mean:   {stats_total['mean_ms']:.2f} ms")
    print(f"Generation Latency Median: {stats_total['median_ms']:.2f} ms")
    print(f"Generation Latency p95:    {stats_total['p95_ms']:.2f} ms")
    print(f"TTFT (Prompt Proc) Mean:   {stats_ttft['mean_ms']:.2f} ms")
    print(f"Average Generation Speed:  {stats_tps['mean_ms']:.2f} tokens/sec")
    print(f"Peak RAM:                  {ram_after_mb:.1f} MB (Delta: +{ram_after_mb - ram_before_mb:.1f} MB)")

    result = {
        "benchmark": "local_llm_generation",
        "hardware_context": get_benchmark_hardware_context(),
        "model": meta["model_id"],
        "runtime": meta["runtime"],
        "precision": "float32",
        "provider": meta["active_provider"],
        "iterations": measurement_runs,
        "total_latency": stats_total,
        "ttft": stats_ttft,
        "tokens_per_second": stats_tps,
        "memory": {
            "ram_before_mb": round(ram_before_mb, 2),
            "ram_after_mb": round(ram_after_mb, 2),
            "ram_delta_mb": round(ram_after_mb - ram_before_mb, 2),
        },
    }

    save_benchmark_result("llm_benchmark.json", result)
    return result


if __name__ == "__main__":
    run_llm_benchmark()
