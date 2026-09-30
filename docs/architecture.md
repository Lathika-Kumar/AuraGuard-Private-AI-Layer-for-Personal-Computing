# AuraGuard — System Architecture & Data Flow

**Core Principle:** 100% On-Device Sovereign AI Layer for Personal Computing.
Zero external API transmissions. Zero cloud telemetry. Local authenticated encryption at rest with Windows DPAPI key management.

---

## 1. High-Level Architecture Diagram

```text
                                  AURAGUARD
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
      [LOCAL DOCUMENTS]       [LOCAL REMIND MEMORY]    [LOCAL PRIVACY SHIELD]
       (PDF Partitioning)      (Personal Context)       (Entity Detection)
              │                       │                       │
              │                       │                       │
              └───────────────┬───────┴───────────────────────┘
                              ↓
                    [LOCAL RETRIEVAL LAYER]
              (FAISS Semantic Search + SQLite Chunks)
                              ↓
                  [CONTEXT CONSTRUCTION]
              (Document Attribution + Memory Provenance)
                              ↓
              [PRIVACY CHECKPOINT 2: CONTEXT FILTER]
              (Adversarial Prompt Injection Stripping & Redaction)
                              ↓
                    [LOCAL AI REASONING]
                   (Qwen2.5-0.5B-Instruct)
                              ↓
                 ┌────────────┴────────────┐
                 │                         │
          [CPU EXECUTION]          [QUALCOMM QNN RUNTIME]
      (Intel/AMD x86_64 Fallback)          │
                                           ↓
                                [SNAPDRAGON HEXAGON NPU]*
                               (Hardware Acceleration Target)
                 │                         │
                 └────────────┬────────────┘
                              ↓
              [PRIVACY CHECKPOINT 3: OUTPUT GUARD]
              (Leakage Prevention & Redaction Shield)
                              ↓
                      [VERIFIED LOCAL ANSWER]
           (Grounded Citations + Strict Provenance)
```

*\*Note on Snapdragon NPU: The execution provider architecture dynamically routes tensors to the Qualcomm QNN execution provider when compatible Qualcomm silicon (Snapdragon X Elite / Plus) and drivers are detected; otherwise, it executes via optimized CPUExecutionProvider.*

---

## 2. Storage & Security Data Path

```text
User File / Thought
        ↓
[Privacy Checkpoint 1: Input Analysis]
        ↓
[Memory / Document Processor]
        ↓
[Neural Embeddings: BGE-small INT8/FP32]
  ├──> FAISS Vector Index (In-Memory uint8 Array)
  │         ↓ (Encrypted at Rest)
  │    [AES-256-GCM Envelope on Disk: index.faiss]
  │
  └──> Chunk Text / Memory Content
            ↓ (Encrypted at Rest)
       [AES-256-GCM Dynamic Nonce Ciphertext: auraguard.db]
            ▲
            │ (Protected Master Key)
       [Windows DPAPI (CryptProtectData via crypt32.dll)]
```

---

## 3. Subsystem Breakdown

### A. Local Documents & Ingestion
* **Format Support:** PDF documents parsed on-device via `pypdf`.
* **Page-Aware Chunking:** Partitions text into contiguous chunks with strict page-number mapping (`Page N`, `Chunk #ID`).
* **Zero Cloud Extraction:** OCR and parsing execute strictly within local process space.

### B. ReMind Context Engine
* **Purpose:** User-controlled persistent personal memory (Preferences, Facts, Tasks, Goals, Context).
* **Explicit Approval Flow:** Requires explicit user review of classification, importance, and expiration before encrypted persistence.
* **Cryptographic Purge:** Deleting a memory purges the SQLite record, metadata, and FAISS vector simultaneously.

### C. Three-Checkpoint Privacy Engine
* **Checkpoint 1 (Input):** Scans user query for sensitive credentials (API keys, passwords, private keys). Prohibited secrets trigger an immediate `BLOCK`.
* **Checkpoint 2 (Context):** Strips adversarial prompt injection commands (`IGNORE PREVIOUS INSTRUCTIONS`, `SYSTEM OVERRIDE`) from untrusted documents before LLM ingestion.
* **Checkpoint 3 (Output Guard):** Evaluates synthesized response against privacy policy rules to prevent credential or personal data exfiltration.

### D. AI Runtime & Acceleration
* **Embedding Model:** BGE-small-en-v1.5 (384 dimensions) with validated INT8 quantization.
* **Language Model:** Qwen2.5-0.5B-Instruct running locally in PyTorch causal LM mode.
* **Hardware Abstraction:** `AI_EXECUTION_PROVIDER=auto` probes host silicon:
  * On Snapdragon PCs: Selects `QNNExecutionProvider` targeted to Qualcomm Hexagon NPU.
  * On Intel/AMD PCs: Automatically falls back to `CPUExecutionProvider` with zero errors.
