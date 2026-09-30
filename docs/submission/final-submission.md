# AuraGuard: Private AI Layer for Personal Computing
**Competition Submission Document**

---

## 1. Executive Summary & Problem

Modern personal computing is rapidly integrating generative AI into everyday workflows—summarizing emails, retrieving desktop documents, remembering conversations, and assisting with sensitive tasks. However, mainstream solutions route raw user context, private documents, personal credentials, and persistent memories to remote cloud datacenters.

This architecture creates three critical risks:
1. **Data Exfiltration & Exposure**: Personal records, API keys, medical notes, and financial reports are transmitted off-device and stored on external cloud infrastructure.
2. **Context Leakage Across Domains**: Centralized cloud models aggregate disparate user interactions, creating persistent surveillance footprints.
3. **Loss of Digital Sovereignty**: Users cannot inspect, independently audit, or permanently purge their data from centralized AI memory banks.

---

## 2. Why Existing Personal AI Creates a Privacy Concern

Most commercial "on-device" or "assistant" implementations are actually thin clients:
- **Cloud Dependency**: The heavy semantic index and LLM generation execute on remote servers.
- **Unencrypted Local State**: Cached context and memory profiles are stored in plaintext databases.
- **Zero Input Sanitization**: Prompts containing secrets or accidental paste-events are forwarded directly to third-party endpoints.
- **Opaque Memory Storage**: User memories cannot be deleted with verifiable guarantees from vector and relational stores simultaneously.

---

## 3. The AuraGuard Solution

**AuraGuard** is an open, auditable, privacy-first local AI layer engineered specifically for personal computing on modern AI PC platforms such as HP Snapdragon-powered devices.

AuraGuard ensures:
- **Zero Cloud Egress**: Document parsing, chunking, neural embedding, vector indexing, retrieval, and LLM synthesis run 100% locally.
- **Active Privacy Guard**: Multi-stage inspection intercepts credentials, API keys, and sensitive tokens *before* they can enter vector memory or LLM prompts.
- **ReMind Context Memory**: User-controlled episodic memory that requires explicit user confirmation before indexing and supports verifiable cryptographic deletion.
- **Hardware-Aware Runtime**: Dynamically detects the host SoC, providing optimized CPU execution on standard PCs and an automated QNN NPU deployment path on Qualcomm Snapdragon X Series hardware.

---

## 4. End-to-End Local Architecture

```text
       [ User / Browser Client ]
                   │
                   ▼ (127.0.0.1 localhost only)
       [ FastAPI Local Gateway ]
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
[ Privacy Engine ]        [ Secure Storage Manager ]
(Regex, Entropy, Tokens)   (AES-256-GCM + Windows DPAPI)
    │                             │
    ▼                             ▼
[ Local RAG Engine ]      [ ReMind Memory Store ]
(Local Chunking & FAISS)   (Encrypted SQLite + Vectors)
    │                             │
    └──────────────┬──────────────┘
                   ▼
       [ Hardware Abstraction ]
       ├─ CPUExecutionProvider (Intel Baseline)
       └─ QNNExecutionProvider (Snapdragon NPU Target)
                   │
                   ▼
     [ Local Neural Models ]
     ├─ INT8 all-MiniLM-L6-v2 (Embedding)
     └─ Local Qwen2.5-0.5B-Instruct (LLM)
                   │
                   ▼
     [ Grounded Local Answer ]
```

---

## 5. ReMind: User-Controlled Personal Memory

ReMind is AuraGuard's episodic memory engine designed with strict privacy boundaries:
1. **Explicit Consent**: Potential memories extracted from conversations are held as "Candidates" until the user explicitly approves them.
2. **Pre-Ingestion Privacy Check**: Candidate memories undergo regex and Shannon entropy inspection to prevent accidental storage of secrets.
3. **Encrypted Storage**: Approved memories are stored in AES-256-GCM encrypted records with DPAPI-protected encryption keys.
4. **Verifiable Deletion**: When a user clicks "Delete Memory", the item is synchronously removed from the relational database, deleted from FAISS vector indices, and evicted from memory caches.

---

## 6. Privacy Engine: 3-Stage Defensive Pipeline

AuraGuard implements defense-in-depth across three distinct checkpoints:
- **Input Checkpoint**: Inspects user queries for API tokens, secret keys, passwords, and prompt injection patterns (`ignore previous instructions`, `system override`).
- **Context Synthesis Checkpoint**: Inspects retrieved chunks and memories to prevent prompt poisoning from untrusted documents.
- **Output Checkpoint**: Scans generated responses before display to prevent accidental echo of sensitive personal data.

---

## 7. Grounded Local RAG

- **True Ingestion**: Real PDF parsing with page-level metadata preservation.
- **Deterministic Chunking**: 500-character chunks with 100-character overlap.
- **Vector Indexing**: FAISS FlatL2 index storing 384-dimensional dense vectors.
- **Honest Attribution**: Responses explicitly cite exact source filenames and page numbers. When no relevant information is found, the system clearly states it cannot find corroborating context rather than hallucinating.

---

## 8. Cryptographic Architecture

- **Symmetric Encryption**: AES-256-GCM with unique 96-bit nonces per record for all document metadata, stored chunks, and ReMind memories.
- **Key Protection**: Key encryption keys managed via Windows Data Protection API (DPAPI), binding cryptographic security directly to the authenticated Windows user profile.
- **Vector Security**: FAISS indices are stored using envelope encryption at rest.

---

## 9. Snapdragon Optimization & Hardware-Aware Runtime

AuraGuard features a dedicated hardware detection and execution layer:
- **Architecture Detection**: Probes Windows platform registry, CPUID, and processor name strings (`Snapdragon`, `ARM64`).
- **NPU Awareness**: Probes for Qualcomm Hexagon NPU drivers and `QnnHtp.dll`.
- **Execution Provider Management**: Dynamically routes ONNX Runtime execution between `QNNExecutionProvider` (Qualcomm Hexagon NPU) and `CPUExecutionProvider` (fallback).
- **Graceful Fallback**: If an ONNX operator cannot be executed on the NPU, the system seamlessly executes the node on the CPU without failure.

---

## 10. Current Measured Results (Intel Baseline)

AuraGuard's performance on the development host (Intel Core i5-1235U, 8 GB RAM, Windows 11 x86_64) provides an empirical baseline:

| Workload | Metric | Measured Intel Baseline | Snapdragon Target |
| :--- | :--- | :--- | :--- |
| **Embedding** | Single Query Latency | 38.32 ms | Target: < 15 ms |
| **Embedding** | Batch-8 Throughput | 57.32 texts/sec | Target: > 120 texts/sec |
| **Quantization** | INT8 Compression | 86.20 MB → 21.82 MB (74.7% reduction) | 21.82 MB HTP Context |
| **Cosine Agreement** | INT8 vs FP32 Fidelity | 0.952862 avg cosine sim (100% Top-3 match) | Preserved |
| **LLM Inference** | Time to First Token (TTFT) | 14,278.46 ms (long prompt) | Target: < 2,500 ms |
| **LLM Generation** | Generation Speed | 4.29 tokens/sec | Target: > 15 tokens/sec |
| **End-to-End RAG** | Mean Query Latency | 12.05 sec | Target: < 3.5 sec |
| **Memory Footprint**| Peak Process RSS | 992 MB | Target: < 1,200 MB |

*Note: Snapdragon performance metrics represent technical targets for the Qualcomm Hexagon NPU and must be determined via physical measurement on compatible hardware.*

---

## 11. Deployment

AuraGuard is packaged with comprehensive deployment scripts:
- `scripts/verify.ps1`: End-to-end full system sanity test.
- `scripts/qualcomm/verify_snapdragon.ps1`: Platform and NPU driver verification.
- `scripts/qualcomm/validate_artifacts.py`: Model checksum, quantization, and EP validation.
- `scripts/qualcomm/run_full_benchmark.ps1`: Standardized latency and throughput suite.

---

## 12. Verified Limitations

1. **Host Hardware Constraints**: Development and baseline benchmarking were conducted on an Intel x86_64 host; physical Qualcomm NPU execution remains pending verification on Snapdragon X Series hardware.
2. **Context Window**: Local Qwen2.5-0.5B-Instruct operates with a 2,048 token context limit to maintain low RAM overhead (< 1 GB RSS).
3. **Single User Binding**: Windows DPAPI key management is tied to the active Windows login account.

---

## 13. Future Snapdragon Validation Path

Upon deployment to an HP Snapdragon X Elite or X Plus laptop:
1. Run `.\scripts\qualcomm\verify_snapdragon.ps1` to confirm ARM64 OS, Hexagon NPU driver, and QNN EP availability.
2. Execute `.\scripts\qualcomm\run_full_benchmark.ps1` to replace Intel baseline numbers with direct on-device physical measurements.
3. Validate NPU power efficiency and thermal stability during sustained multi-turn conversation and batch document indexing.
