# AuraGuard Evidence: Empirical Benchmark Results

## Comparative Performance Matrix

| Metric | Intel Core i5-1235U (Measured) | Snapdragon CPU | Snapdragon NPU (Qualcomm Hexagon) |
| :--- | :---: | :---: | :---: |
| **Embedding Mean Latency** | **38.32 ms** | Not measured | Not measured |
| **Embedding p95 Latency** | **56.12 ms** | Not measured | Not measured |
| **Embedding Throughput** | **57.32 texts/sec** | Not measured | Not measured |
| **LLM Time To First Token (TTFT)** | **14,278.46 ms** (full prompt) / **510.4 ms** (short prompt) | Not measured | Not measured |
| **LLM Generation Speed** | **4.29 tokens/sec** | Not measured | Not measured |
| **Total RAG Pipeline Latency** | **12.05 s** | Not measured | Not measured |
| **Peak Process RSS** | **992.0 MB** | Not measured | Not measured |
| **Power Consumption (W)** | **Not measured** | Not measured | Not measured |

---

## Storage & Encryption Performance (AES-256-GCM + Windows DPAPI)
* **Chunk Encryption (1 KB)**: Mean `0.0083 ms` (p95: `0.0163 ms`)
* **Chunk Decryption (1 KB)**: Mean `0.0070 ms` (p95: `0.0142 ms`)
* **Envelope Encryption (64 KB)**: Mean `0.0894 ms` (p95: `0.1259 ms`)
* **Envelope Decryption (64 KB)**: Mean `0.0526 ms` (p95: `0.0709 ms`)
* **DPAPI Key Access**: Mean `0.0002 ms`

---

## ReMind Memory Operations
* **Memory Creation & FAISS Indexing**: Mean `66.69 ms`
* **Semantic Memory Retrieval**: Mean `60.11 ms`
