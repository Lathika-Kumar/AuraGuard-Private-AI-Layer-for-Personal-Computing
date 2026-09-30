# AuraGuard — Final Hardware & Accelerator Benchmark Report

## 1. Executive Hardware Status
* **Host Processor**: 12th Gen Intel(R) Core(TM) i5-1235U
* **Architecture**: AMD64
* **Active Execution Provider**: CPU (Clean Fallback Verified)
* **Qualcomm Snapdragon Silicon**: NOT AVAILABLE (Development Workstation)
* **Qualcomm Hexagon NPU**: NOT MEASURED (Physical Snapdragon Hardware Required)

---

## 2. Comparative Benchmark Matrix

| Metric | Intel CPU | Snapdragon CPU | Snapdragon NPU |
| :--- | :---: | :---: | :---: |
| **Embedding mean** | NA | Not measured | Not measured |
| **Embedding p95** | NA | Not measured | Not measured |
| **Embedding throughput** | NA | Not measured | Not measured |
| **LLM TTFT** | 14278.46 ms | Not measured | Not measured |
| **LLM tokens/sec** | 4.29 tokens/s | Not measured | Not measured |
| **RAG latency** | NA | Not measured | Not measured |
| **Peak RAM** | 991.96 MB | Not measured | Not measured |
| **Power** | Not measured | Not measured | Not measured |

*Methodology Notice: In accordance with competition rules, zero values are fabricated. Snapdragon CPU and NPU metrics are recorded as 'Not measured' pending physical Snapdragon Copilot+ PC deployment.*

---

## 3. Storage & Encryption Performance
* **Chunk Encryption (AES-256-GCM)**: NA ms
* **Chunk Decryption (AES-256-GCM)**: NA ms
* **Envelope Encryption (64 KB)**: NA ms
* **Envelope Decryption (64 KB)**: NA ms
* **DPAPI Key Access Latency**: NA ms

---

## 4. ReMind Memory Operations
* **Memory Creation & FAISS Indexing**: NA ms
* **Semantic Memory Retrieval**: NA ms
