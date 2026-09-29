"""Performance measurement script for AuraGuard Phase 2A."""
from __future__ import annotations

import sys
import time
from pathlib import Path
import numpy as np

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.embedding_service import EmbeddingProvider
from app.services.ai_service import AIProvider
from app.services.vector_service import FaissIndex

def main() -> None:
    print("=== AuraGuard Real AI Benchmark ===")

    # 1. Embedding Model Loading
    t0 = time.time()
    embedder = EmbeddingProvider()
    t_load_embed = time.time() - t0

    # 2. Embedding Latency & Throughput
    sentences = [
        "The internship application deadline is Friday.",
        "On-device neural inference guarantees zero data leakage over the network.",
        "Qualcomm Hexagon NPU delivers up to 45 TOPS of local compute.",
        "AuraGuard establishes a private AI layer for personal computing.",
    ]
    # Warmup
    embedder.embed(sentences[:1])

    t0 = time.time()
    iters = 10
    total_texts = len(sentences) * iters
    for _ in range(iters):
        _ = embedder.embed(sentences)
    t_embed_total = time.time() - t0
    embed_latency_per_text = (t_embed_total / total_texts) * 1000 # ms
    embed_throughput = total_texts / t_embed_total # texts / sec

    # 3. FAISS Search Latency
    index = FaissIndex(dim=embedder.dimension)
    sample_vecs = embedder.embed(sentences)
    index.add(sample_vecs)

    q_vec = embedder.embed(["When is the deadline?"])[0]
    t0 = time.time()
    search_iters = 100
    for _ in range(search_iters):
        _, _ = index.search(q_vec, top_k=2)
    t_search_total = time.time() - t0
    search_latency = (t_search_total / search_iters) * 1000 # ms

    # 4. LLM Loading Time
    t0 = time.time()
    ai = AIProvider()
    t_load_llm = time.time() - t0

    # 5. LLM Generation Latency & Throughput
    context = "(p1) The AuraGuard application deadline is Friday, October 15, 2026."
    question = "When is the AuraGuard application deadline?"
    # Warmup
    ai.generate(question, context)

    t0 = time.time()
    answer, t_gen = ai.generate(question, context)
    total_time = time.time() - t0

    print(f"Embedding Model Loading Time : {t_load_embed:.3f} s")
    print(f"Embedding Latency (per chunk): {embed_latency_per_text:.2f} ms")
    print(f"Embedding Throughput         : {embed_throughput:.1f} chunks/sec")
    print(f"FAISS Search Latency         : {search_latency:.3f} ms")
    print(f"LLM Loading Time             : {t_load_llm:.3f} s")
    print(f"LLM Generation Latency       : {t_gen:.3f} s")
    print(f"LLM Generated Answer         : \"{answer}\"")

if __name__ == "__main__":
    main()
