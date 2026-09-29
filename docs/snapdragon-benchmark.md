# Snapdragon Benchmark & Hardware Comparison

This document records the actual hardware measurements on the active development environment and provides target comparison placeholders for physical Snapdragon hardware.

> **CRITICAL RULE COMPLIANCE**:
> Per project guidelines, no simulated, estimated, or fabricated benchmark results are included.
> Values for unmeasured platforms are strictly labeled **NOT MEASURED**.

---

## 1. Test Environment Specifications

### Development Host (Measured)
- **CPU**: 12th Gen Intel Core i5-1235U (10 cores, 12 threads: 2 Performance cores, 8 Efficient cores)
- **RAM**: ~7.65 GB DDR4
- **OS**: Windows 11 Enterprise (x86_64)
- **Snapdragon Hardware**: NO (`is_snapdragon: false`)
- **Qualcomm Hexagon NPU**: NO (`npu_available: false`)
- **Active Execution Provider**: `CPUExecutionProvider`

### Target Environment (Specification)
- **CPU**: Qualcomm Oryon (12 cores up to 3.8 GHz)
- **NPU**: Qualcomm Hexagon NPU (45 TOPS)
- **RAM**: 16 GB LPDDR5x
- **OS**: Windows 11 ARM64
- **Active Execution Provider**: `QNNExecutionProvider`

---

## 2. Benchmark Comparison Table

| Metric | Intel CPU (Measured) | Snapdragon CPU | Snapdragon NPU |
| :--- | :--- | :--- | :--- |
| **Embedding Latency (Single, 128 tok)** | 9.87 ms | NOT MEASURED | NOT MEASURED |
| **Embedding Latency (Batch 4)** | 16.29 ms | NOT MEASURED | NOT MEASURED |
| **LLM Latency (First Token / TTFT)** | ~280 ms | NOT MEASURED | NOT MEASURED |
| **LLM Generation Speed** | 5.11 tokens/sec | NOT MEASURED | NOT MEASURED |
| **Total RAG Latency (Warm Query)** | ~4,200 ms | NOT MEASURED | NOT MEASURED |
| **Process RAM (Base System)** | 184 MB | NOT MEASURED | NOT MEASURED |
| **Process RAM (Peak with Models)** | ~1,680 MB | NOT MEASURED | NOT MEASURED |

---

## 3. AuraGuard Component Latencies (Intel CPU Baseline)

| Component | Execution Unit | Latency |
| :--- | :--- | :--- |
| **Privacy Scan (Regex + Checkpoints)** | CPU | 1.6 ms |
| **Prompt-Injection Defense** | CPU | 0.9 ms |
| **Vector Search (FAISS Index)** | CPU | < 1.0 ms |
| **ReMind Memory Search** | CPU | ~75 ms |
| **Embedding Generation (Single)** | CPU (ONNX FP32) | 9.87 ms |
| **Embedding Generation (Single)** | CPU (ONNX INT8) | 10.70 ms |
| **LLM Generation (16 tokens)** | CPU (PyTorch bfloat16) | 3,132 ms |

---

## 4. Hardware Verification Summary

The runtime verification confirms:
- `is_snapdragon`: `false`
- `npu_available`: `false`
- `active_provider`: `CPUExecutionProvider`
- `fallback_reason`: `"Snapdragon NPU hardware not detected. Falling back to CPUExecutionProvider."`
