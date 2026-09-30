from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_encryption import run_encryption_benchmark
from benchmark_embedding import run_embedding_benchmark
from benchmark_memory import run_memory_benchmark
from benchmark_llm import run_llm_benchmark
from benchmark_rag import run_rag_benchmark


def main():
    print("=" * 70)
    print("AuraGuard Phase 6: Automated Comprehensive Benchmark Suite")
    print("=" * 70)

    print("\n[1/5] Running Encryption Benchmark...")
    run_encryption_benchmark(warmup_runs=5, measurement_runs=50)

    print("\n[2/5] Running Neural Embedding Benchmark...")
    run_embedding_benchmark(warmup_runs=3, measurement_runs=10)

    print("\n[3/5] Running ReMind Memory Benchmark...")
    run_memory_benchmark(warmup_runs=2, measurement_runs=10)

    print("\n[4/5] Running Local LLM Benchmark...")
    run_llm_benchmark(warmup_runs=1, measurement_runs=2)

    print("\n[5/5] Running End-to-End RAG Benchmark...")
    run_rag_benchmark(warmup_runs=1, measurement_runs=2)

    print("\n" + "=" * 70)
    print("ALL BENCHMARKS COMPLETED SUCCESSFULLY")
    print("Results persisted in: benchmarks/results/")
    print("=" * 70)


if __name__ == "__main__":
    main()
