from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import psutil

# Ensure backend app is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.security.encryption_service import encryption_service
from app.security.key_manager import key_manager
from common import (
    get_benchmark_hardware_context,
    compute_statistics,
    save_benchmark_result,
)


def run_encryption_benchmark(warmup_runs: int = 10, measurement_runs: int = 100) -> dict:
    print("=" * 60)
    print("AuraGuard Benchmark: AES-256-GCM Storage Encryption & DPAPI")
    print("=" * 60)

    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    # 1. Chunk Text Payload (~2KB text)
    sample_chunk_text = (
        "Qualcomm Snapdragon X Elite compute platform is built for high-performance AI workloads on Windows on ARM. "
        "The integrated Hexagon NPU delivers up to 45 TOPS of dedicated tensor processing throughput. "
        "AuraGuard leverages this silicon using Qualcomm AI Hub optimized ONNX models and QNN Execution Provider. "
        "Local memory and document context are protected at rest via AES-256-GCM authenticated encryption. "
    ) * 5

    # 2. Binary Payload (~50KB, simulating FAISS index)
    sample_binary_payload = os.urandom(50 * 1024)

    # Warmup
    print(f"\nPerforming {warmup_runs} warm-up rounds...")
    for _ in range(warmup_runs):
        ct = encryption_service.encrypt(sample_chunk_text)
        _ = encryption_service.decrypt(ct)
        env = encryption_service.encrypt_bytes(sample_binary_payload)
        _ = encryption_service.decrypt_bytes(env)

    # Measurement: Text Chunk Encrypt
    print(f"Executing {measurement_runs} text chunk encryption runs...")
    chunk_enc_lats_ms = []
    chunk_ciphertexts = []
    for _ in range(measurement_runs):
        t0 = time.perf_counter()
        ct = encryption_service.encrypt(sample_chunk_text)
        t1 = time.perf_counter()
        chunk_enc_lats_ms.append((t1 - t0) * 1000.0)
        chunk_ciphertexts.append(ct)

    # Measurement: Text Chunk Decrypt
    print(f"Executing {measurement_runs} text chunk decryption runs...")
    chunk_dec_lats_ms = []
    for ct in chunk_ciphertexts:
        t0 = time.perf_counter()
        _ = encryption_service.decrypt(ct)
        t1 = time.perf_counter()
        chunk_dec_lats_ms.append((t1 - t0) * 1000.0)

    # Measurement: Binary File Envelope Encrypt (50KB)
    print(f"Executing {measurement_runs} binary envelope encryption runs (50KB)...")
    bin_enc_lats_ms = []
    bin_envelopes = []
    for _ in range(measurement_runs):
        t0 = time.perf_counter()
        env = encryption_service.encrypt_bytes(sample_binary_payload)
        t1 = time.perf_counter()
        bin_enc_lats_ms.append((t1 - t0) * 1000.0)
        bin_envelopes.append(env)

    # Measurement: Binary File Envelope Decrypt (50KB)
    print(f"Executing {measurement_runs} binary envelope decryption runs (50KB)...")
    bin_dec_lats_ms = []
    for env in bin_envelopes:
        t0 = time.perf_counter()
        _ = encryption_service.decrypt_bytes(env)
        t1 = time.perf_counter()
        bin_dec_lats_ms.append((t1 - t0) * 1000.0)

    # Measurement: DPAPI Key Unprotect Latency
    print(f"Executing 20 DPAPI key unprotection runs...")
    dpapi_lats_ms = []
    for _ in range(20):
        t0 = time.perf_counter()
        _ = key_manager.get_or_create_key()
        t1 = time.perf_counter()
        dpapi_lats_ms.append((t1 - t0) * 1000.0)

    ram_after_mb = process.memory_info().rss / (1024 * 1024)

    stats_chunk_enc = compute_statistics(chunk_enc_lats_ms)
    stats_chunk_dec = compute_statistics(chunk_dec_lats_ms)
    stats_bin_enc = compute_statistics(bin_enc_lats_ms)
    stats_bin_dec = compute_statistics(bin_dec_lats_ms)
    stats_dpapi = compute_statistics(dpapi_lats_ms)

    print("\n--- RESULTS ---")
    print(f"Chunk Encrypt (2KB) Mean:   {stats_chunk_enc['mean_ms']:.4f} ms (p95: {stats_chunk_enc['p95_ms']:.4f} ms)")
    print(f"Chunk Decrypt (2KB) Mean:   {stats_chunk_dec['mean_ms']:.4f} ms (p95: {stats_chunk_dec['p95_ms']:.4f} ms)")
    print(f"Envelope Encrypt (50KB) Mean:{stats_bin_enc['mean_ms']:.4f} ms (p95: {stats_bin_enc['p95_ms']:.4f} ms)")
    print(f"Envelope Decrypt (50KB) Mean:{stats_bin_dec['mean_ms']:.4f} ms (p95: {stats_bin_dec['p95_ms']:.4f} ms)")
    print(f"DPAPI Key Access Mean:      {stats_dpapi['mean_ms']:.4f} ms")
    print(f"RAM Usage:                  {ram_after_mb:.1f} MB")

    result = {
        "benchmark": "aes_256_gcm_encryption",
        "hardware_context": get_benchmark_hardware_context(),
        "algorithm": "AES-256-GCM",
        "key_protection": "Windows DPAPI" if key_manager.is_dpapi_supported() else "Protected Key",
        "iterations": measurement_runs,
        "chunk_encryption_2kb": stats_chunk_enc,
        "chunk_decryption_2kb": stats_chunk_dec,
        "binary_envelope_encryption_50kb": stats_bin_enc,
        "binary_envelope_decryption_50kb": stats_bin_dec,
        "dpapi_key_access": stats_dpapi,
        "memory": {
            "ram_before_mb": round(ram_before_mb, 2),
            "ram_after_mb": round(ram_after_mb, 2),
            "ram_delta_mb": round(ram_after_mb - ram_before_mb, 2),
        },
    }

    save_benchmark_result("encryption_benchmark.json", result)
    return result


if __name__ == "__main__":
    run_encryption_benchmark()
