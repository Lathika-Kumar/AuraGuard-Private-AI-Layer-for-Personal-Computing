from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import psutil
import torch
from transformers.generation.streamers import BaseStreamer

# Ensure backend app is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.ai_service import AIProvider, AURA_GUARD_SYSTEM_PROMPT
from common import (
    get_benchmark_hardware_context,
    compute_statistics,
    save_benchmark_result,
)


class TTFTStreamer(BaseStreamer):
    """Accurately records the exact timestamp when token #1 is generated."""
    def __init__(self, t_start: float):
        super().__init__()
        self.t_start = t_start
        self.t_first_token: float | None = None
        self.first_token_received = False

    def put(self, value):
        # In HuggingFace streamers, the prompt tensor is echoed first (2D tensor [batch, prompt_len])
        if hasattr(value, "ndim") and value.ndim > 1:
            return  # Skip prompt echo
        if not self.first_token_received:
            self.t_first_token = time.perf_counter()
            self.first_token_received = True

    def end(self):
        pass


def run_llm_benchmark(warmup_runs: int = 1, measurement_runs: int = 2) -> dict:
    print("=" * 60)
    print("AuraGuard Benchmark: Neural LLM Generation (Qwen2.5-0.5B-Instruct)")
    print("=" * 60)

    vm_before = psutil.virtual_memory()
    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    llm = AIProvider()
    llm._ensure_model_loaded()
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

    # Multi-length evaluations: 16, 32, 64 tokens
    length_results = {}
    print("\nEvaluating structured generation lengths (16, 32, 64 tokens)...")
    for max_tok in [16, 32, 64]:
        messages = [
            {"role": "system", "content": AURA_GUARD_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"UNTRUSTED LOCAL CONTEXT:\n\"\"\"\n{sample_context}\n\"\"\"\n\nQUESTION: {sample_query}",
            },
        ]
        prompt = llm.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = llm.tokenizer(prompt, return_tensors="pt").to(llm.device)
        input_tokens = inputs.input_ids.shape[1]

        t_start = time.perf_counter()
        streamer = TTFTStreamer(t_start)
        with torch.inference_mode():
            outputs = llm.model.generate(
                **inputs,
                max_new_tokens=max_tok,
                do_sample=False,
                streamer=streamer,
            )
        t_finish = time.perf_counter()
        total_time_ms = (t_finish - t_start) * 1000.0
        ttft_ms = ((streamer.t_first_token or t_finish) - t_start) * 1000.0
        out_tokens = outputs[0].shape[0] - input_tokens
        gen_duration_s = (t_finish - (streamer.t_first_token or t_start))
        tps = out_tokens / gen_duration_s if gen_duration_s > 0 else 0.0

        length_results[f"{max_tok}_tokens"] = {
            "max_new_tokens": max_tok,
            "input_tokens": input_tokens,
            "output_tokens": out_tokens,
            "ttft_ms": round(ttft_ms, 2),
            "total_latency_ms": round(total_time_ms, 2),
            "tokens_per_sec": round(tps, 2),
        }
        print(f"  [{max_tok} tokens] TTFT: {ttft_ms:.1f} ms | Total: {total_time_ms:.1f} ms | Speed: {tps:.2f} tok/s")

    # Full generation measurement runs
    print(f"\nExecuting {measurement_runs} full measurement generation runs...")
    total_latencies_ms = []
    tokens_generated_list = []
    tokens_per_sec_list = []
    ttft_latencies_ms = []

    for i in range(measurement_runs):
        messages = [
            {"role": "system", "content": AURA_GUARD_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"UNTRUSTED LOCAL CONTEXT:\n\"\"\"\n{sample_context}\n\"\"\"\n\nQUESTION: {sample_query}",
            },
        ]
        prompt = llm.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = llm.tokenizer(prompt, return_tensors="pt").to(llm.device)
        input_tokens = inputs.input_ids.shape[1]

        t_start = time.perf_counter()
        streamer = TTFTStreamer(t_start)
        with torch.inference_mode():
            outputs = llm.model.generate(
                **inputs,
                max_new_tokens=40,
                do_sample=False,
                streamer=streamer,
            )
        t_finish = time.perf_counter()

        total_time_ms = (t_finish - t_start) * 1000.0
        total_latencies_ms.append(total_time_ms)
        ttft_ms = ((streamer.t_first_token or t_finish) - t_start) * 1000.0
        ttft_latencies_ms.append(ttft_ms)

        out_tokens = outputs[0].shape[0] - input_tokens
        tokens_generated_list.append(out_tokens)
        gen_duration_s = (t_finish - (streamer.t_first_token or t_start))
        tps = out_tokens / gen_duration_s if gen_duration_s > 0 else 0.0
        tokens_per_sec_list.append(tps)
        print(f"  Run {i+1}: TTFT: {ttft_ms:.1f} ms | Total: {total_time_ms:.1f} ms | Tokens: {out_tokens} | Rate: {tps:.2f} tokens/s")

    vm_after = psutil.virtual_memory()
    ram_after_mb = process.memory_info().rss / (1024 * 1024)

    stats_total = compute_statistics(total_latencies_ms)
    stats_ttft = compute_statistics(ttft_latencies_ms)
    stats_tps = compute_statistics(tokens_per_sec_list)

    print("\n--- RESULTS ---")
    print(f"Generation Latency Mean:   {stats_total['mean_ms']:.2f} ms")
    print(f"Generation Latency Median: {stats_total['median_ms']:.2f} ms")
    print(f"Generation Latency p95:    {stats_total['p95_ms']:.2f} ms")
    print(f"True TTFT Mean:            {stats_ttft['mean_ms']:.2f} ms")
    print(f"Average Generation Speed:  {stats_tps['mean_ms']:.2f} tokens/sec")
    print(f"Peak Process RSS:          {ram_after_mb:.1f} MB (Delta: +{ram_after_mb - ram_before_mb:.1f} MB)")

    result = {
        "benchmark": "local_llm_generation",
        "methodology": "Phase 7 True TTFT (Request start to Token 1 emit via TTFTStreamer)",
        "hardware_context": get_benchmark_hardware_context(),
        "model": meta["model_id"],
        "runtime": meta["runtime"],
        "precision": "bfloat16" if meta.get("precision") == "bfloat16" else "float32",
        "provider": meta["active_provider"],
        "iterations": measurement_runs,
        "token_length_evaluations": length_results,
        "total_latency": stats_total,
        "ttft": stats_ttft,
        "tokens_per_second": stats_tps,
        "memory": {
            "process_rss_before_mb": round(ram_before_mb, 2),
            "process_rss_after_mb": round(ram_after_mb, 2),
            "process_rss_delta_mb": round(ram_after_mb - ram_before_mb, 2),
            "system_ram_used_percent": vm_after.percent,
            "system_ram_available_gb": round(vm_after.available / (1024**3), 2),
        },
    }

    save_benchmark_result("llm_benchmark.json", result)
    return result


if __name__ == "__main__":
    run_llm_benchmark()
