# AuraGuard — Empirical Benchmark Methodology & TTFT Audit

## Executive Overview

This document defines the formal benchmarking methodology for the AuraGuard on-device AI system, documenting an important methodology revision regarding **Time To First Token (TTFT)** between Phase 6 and Phase 7.

---

## 1. Audit of Phase 6 TTFT Measurement

### The Discrepancy
In Phase 6, the automated LLM benchmark reported:
```text
LLM TTFT: 3.74 ms
Generation Speed: 1.12 tokens/sec
Total Generation Time: 18.37 s
```

### Root Cause Analysis
Code inspection of `scripts/benchmark/benchmark_llm.py` revealed:
```python
# Flawed timing in Phase 6:
inputs = llm.tokenizer(f"{sample_context}\nQuestion: {sample_query}\nAnswer:", return_tensors="pt")
t_encoded = time.perf_counter()
ttft_estimate_ms = (t_encoded - t_start) * 1000.0
```
This measured **only CPU string tokenization** into an integer tensor using HuggingFace's fast Rust tokenizer (~3.74 ms). **Zero forward pass computations, zero prompt prefill, and zero transformer attention layers** were executed during that 3.74 ms interval.

### Definition of True TTFT
In Large Language Model systems, **Time To First Token (TTFT)** is formally defined as:
$$\text{TTFT} = t_{\text{first\_token}} - t_{\text{request\_start}}$$
Where:
* $t_{\text{request\_start}}$: The exact timestamp when prompt text is handed to the inference pipeline.
* $t_{\text{first\_token}}$: The exact timestamp when the model completes prompt prefill (evaluation of all input tokens through all transformer layers) and emits the first generated output token.

---

## 2. Corrected Phase 7 TTFT Methodology

To measure true TTFT without modifying the underlying generation model weights, AuraGuard Phase 7 introduces the `TTFTStreamer` class derived from `transformers.generation.streamers.BaseStreamer`:

```python
class TTFTStreamer(BaseStreamer):
    """Accurately records the exact timestamp when token #1 is generated."""
    def __init__(self, t_start: float):
        super().__init__()
        self.t_start = t_start
        self.t_first_token = None
        self.first_token_received = False

    def put(self, value):
        # HuggingFace streamer first sends prompt tokens (2D tensor [batch, prompt_len])
        if hasattr(value, "ndim") and value.ndim > 1:
            return  # Ignore prompt echo
        if not self.first_token_received:
            self.t_first_token = time.perf_counter()
            self.first_token_received = True

    def end(self):
        pass
```

### Empirical Baseline Difference on Intel Core i5-1235U:
* **Tokenization-only proxy (Phase 6 flawed)**: `3.74 ms`
* **True TTFT (Phase 7 corrected)**: `~510.4 ms`

The corrected methodology reflects the real physical reality of transformer prompt evaluation on mobile x86 CPUs.

---

## 3. Standardized Measurement Protocols

### Warm-Up Protocol
To eliminate cold-start distortions (JIT compilation, paging, OS file caching), every benchmark mandates:
* **1 warm-up iteration** (unrecorded).
* **N measurement iterations** (recorded).

### Statistical Metrics
Every metric is reported with full distribution statistics:
* **Mean ($\mu$)**
* **Median ($50^{\text{th}}\%$)**
* **$95^{\text{th}}$ Percentile (p95)**
* **Minimum ($Min$)**
* **Maximum ($Max$)**

### Granular Stage Breakdown for Local RAG
End-to-end RAG latency is measured across all 9 individual stages:
1. `Input Guard (Checkpoint 1)`
2. `Query Embedding (ONNX all-MiniLM-L6-v2)`
3. `Document Vector Search (FAISS)`
4. `ReMind Memory Vector & Attribute Search`
5. `Context Construction & Provenance Labeling`
6. `Context Neutralizer (Checkpoint 2 Anti-Injection)`
7. `LLM Generation (Qwen2.5-0.5B)`
8. `Output Guard (Checkpoint 3 PII Redaction)`
9. `Total End-to-End Pipeline Latency`
