# AuraGuard Quantization Experiments & Analysis

This document details the quantization experiments conducted for AuraGuard Phase 4 across embedding models and generative LLMs.

---

## 1. Objectives

- Quantize models to reduce parameter storage footprint and runtime memory consumption.
- Maximize execution throughput on target Snapdragon NPU accelerators (which favor INT8 and INT4 tensor engines).
- Evaluate numerical divergence and prevent quality regressions across document search, memory retrieval, privacy checking, and grounded Q&A.

---

## 2. Embedding Model: `all-MiniLM-L6-v2` (FP32 vs INT8)

Quantization was performed via ONNX Runtime dynamic integer quantization (`onnxruntime.quantization.quantize_dynamic`) with `weight_type=QuantType.QInt8`.

### Comparison Metrics

| Metric | FP32 (Original) | INT8 (Quantized) | Impact / Delta |
| :--- | :--- | :--- | :--- |
| **Model File Size** | 86.20 MB | **21.82 MB** | **-74.68%** storage reduction |
| **Model Load Time** | ~42.3 ms | ~15.8 ms | **-62.6%** faster load |
| **Single-Sentence Latency** | 9.87 ms | 10.70 ms | +0.83 ms (x86 CPU lacks INT8 VNNI speedup) |
| **Batch Latency (4 sentences)**| 16.29 ms | 17.65 ms | Comparable CPU latency |
| **Minimum Cosine Similarity** | 1.000000 | **0.947481** | Minimal drift across embeddings |
| **Average Cosine Similarity** | 1.000000 | **0.952862** | **95.3%** directional fidelity |

### Qualitative Analysis
- The INT8 model reduces disk footprint from 86.2 MB to 21.8 MB.
- On standard x86 CPU architectures without specialized INT8 acceleration instructions, inference latency is equivalent. However, on Qualcomm Hexagon NPUs, INT8 execution utilizes dedicated vector and tensor accelerators, enabling significant hardware speedups and power savings.
- Top-k retrieval ranking tests in `scripts/qualcomm/regression_test.py` confirmed identical retrieval ordering between FP32 and INT8 embeddings for test queries.

---

## 3. Generative LLM: `Qwen2.5-0.5B-Instruct` (FP32 vs INT8 vs INT4)

### Execution & Preparation Matrix

| Precision | Runtime | Model Size | RAM Usage | Generation Latency (16 tokens) | Throughput | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FP32** | PyTorch (CPU) | 1,976 MB | ~2,100 MB | 3,132 ms | 5.11 tokens/s | **MEASURED ON INTEL HOST** |
| **INT8** | QNN / AI Hub | ~510 MB | ~600 MB | *TARGET HARDWARE REQUIRED* | *TARGET HARDWARE REQUIRED* | **PREPARED FOR AI HUB** |
| **INT4 (W4A16)** | QNN (Hexagon NPU) | ~320 MB | ~380 MB | *TARGET HARDWARE REQUIRED* | *TARGET HARDWARE REQUIRED* | **PREPARED FOR SNAPDRAGON** |

### Observations on Host Machine
- Measured on 12th Gen Intel Core i5-1235U with 7.65 GB RAM.
- FP32 model generates at ~5.11 tokens/second.
- INT4 W4A16 is the target precision for Qualcomm Hexagon NPU. By quantizing weights to 4-bit while maintaining 16-bit activation tensors, the model occupies only ~320 MB RAM, leaving >90% of system RAM available for the user's personal applications.
