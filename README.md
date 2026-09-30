# AuraGuard — Private AI Layer for Personal Computing

> **Snapdragon-Ready, On-Device Private AI with Local RAG, Encrypted Storage, ReMind Context Intelligence, and Hardware-Aware Acceleration.**

```text
                  AURAGUARD
                      │
        ┌─────────────┼─────────────┐
        │             │             │
     Documents      ReMind       Privacy
        │             │          Engine
        │             │             │
        └───────┬─────┴─────────────┘
                ↓
          Local Retrieval (FAISS)
                ↓
        Context Construction
                ↓
          Privacy Filter
                ↓
           Local AI
                ↓
       ┌────────┴────────┐
       │                 │
      CPU               QNN (Snapdragon-Ready)
                          ↓
                    Snapdragon NPU*
                ↓
          Output Privacy Guard
                ↓
              Answer
```

*\*Note on Snapdragon NPU: Architecture, INT8 quantization, and QNN runtime paths are verified. Actual NPU execution requires compatible Snapdragon hardware with Qualcomm QNN drivers.*

---

## 1. What is AuraGuard?

**AuraGuard** is an on-device, privacy-first AI layer designed for personal computing. It enables users to index sensitive personal documents, retain private conversational memories, and query a local Large Language Model (Qwen2.5-0.5B-Instruct) with complete data sovereignty.

All embeddings, retrieval, privacy filtering, and generative reasoning happen entirely on the local device, with zero cloud dependency, zero external API keys, and zero telemetry.

---

## 2. Problem

Modern commercial AI assistants routinely transmit sensitive personal context—confidential PDFs, corporate contracts, personal notes, and private memories—to remote cloud servers. This exposes personal computing to severe risks:
* **Data Sovereignty Violations**: Confidential user files uploaded to external cloud inference endpoints.
* **Persistent Exposure**: Stored conversational histories susceptible to server-side breaches or corporate model training.
* **Prompt Injection Vulnerabilities**: Indirect prompt attacks embedded inside retrieved web pages or documents can compromise cloud AI agents.
* **Network & Subscription Dependency**: Complete inability to operate offline or during transit without recurring fees.

---

## 3. Solution

AuraGuard creates a strictly isolated on-device runtime:
1. **Local Neural Ingestion**: Documents are parsed, chunked, and embedded into local FAISS vector stores using ONNX Runtime.
2. **ReMind Private Memory**: User-approved personal facts, preferences, and tasks stored in an authenticated, encrypted local database.
3. **Multi-Checkpoint Privacy Engine**: Pre-scans user inputs for secrets, cleans prompt injection vectors from retrieved context, and guards LLM output.
4. **Hardware-Aware AI Runtime**: Executes locally on CPU (`CPUExecutionProvider`) and provides a verified, automated path to Qualcomm Hexagon NPU (`QNNExecutionProvider`) on Snapdragon Copilot+ PCs.
5. **Cryptographic Protection at Rest**: All sensitive chunks, memories, and vector index binaries are encrypted with AES-256-GCM backed by Windows DPAPI.

---

## 4. Why Local AI?

| Feature | Cloud AI | AuraGuard Local AI |
| :--- | :--- | :--- |
| **Data Transmission** | Transmitted over public Internet | **100% On-Device (`localhost`)** |
| **Privacy & Compliance** | Third-party cloud retention risk | **Zero Cloud Telemetry / Full User Sovereignty** |
| **Offline Capability** | Non-functional without internet | **Fully functional air-gapped** |
| **Latency Consistency** | Variable network round-trip time | **Predictable on-device hardware execution** |
| **Hardware Utilization** | Idles device NPU/CPU | **Leverages local Qualcomm Snapdragon NPU / CPU** |

---

## 5. Architecture

AuraGuard's data path enforces strict local isolation at every stage:

```text
[User Document / PDF] ──► [Local Chunking] ──► [ONNX Embedding (all-MiniLM-L6-v2)]
                                                       │
                                                       ▼
                                            [AES-256-GCM FAISS Store]
                                                       │
[User Query] ──► [Checkpoint 1: Input Scan] ───────────┤
                       │                               ▼
                       ▼                     [Semantic Retrieval]
               [ReMind Memory Layer]                   │
                       │                               ▼
                       └───────────────► [Checkpoint 2: Context Filter]
                                                       │
                                                       ▼
                                          [Local LLM (Qwen2.5-0.5B)]
                                          (CPU or Snapdragon QNN)
                                                       │
                                                       ▼
                                        [Checkpoint 3: Output Guard]
                                                       │
                                                       ▼
                                            [Attributed Answer]
```

---

## 6. Privacy Engine

The AuraGuard Privacy Engine implements a three-tier defense system:
* **Checkpoint 1 — Input Guard**: Scans incoming queries for high-entropy secrets (API keys, private keys, passwords) and blocks ingestion before processing.
* **Checkpoint 2 — Context Neutralizer**: Inspects retrieved document chunks and memories for adversarial directives (`IGNORE ALL INSTRUCTIONS`, `SYSTEM PROMPT OVERRIDE`) and scrubs them with neutral tags.
* **Checkpoint 3 — Output Guard**: Performs a final scan on generated text to prevent accidental exfiltration of PII (emails, phone numbers, credentials).

---

## 7. ReMind (Private Memory Intelligence)

ReMind is an on-device personal memory store with explicit user lifecycle control:
* **Explicit Approval**: Memories are never saved silently; the user reviews content, classification, and importance in a dedicated confirmation modal.
* **Dual Retrieval**: Combines semantic FAISS vector search with SQLite attribute filters.
* **Guaranteed Deletion**: Permanent removal erases the SQLite row, removes FAISS vector mappings, and verifies immediate zero-result retrieval.

---

## 8. Local RAG

* **Embeddings**: `all-MiniLM-L6-v2` generating 384-dimensional dense vectors via ONNX Runtime.
* **Vector Store**: FAISS `IndexFlatL2` serialized with AES-256-GCM envelope encryption.
* **Retrieval**: High-precision top-k cosine similarity search.
* **Generation**: `Qwen2.5-0.5B-Instruct` executing locally with source citation transparency (document name and page number).

---

## 9. Snapdragon / QNN Architecture

* **Target Hardware**: Qualcomm Snapdragon X Elite / Plus Copilot+ PCs (Oryon CPU + 45 TOPS Hexagon NPU).
* **Provider Abstraction**: Dynamically detects available hardware and selects `QNNExecutionProvider` when available, falling back cleanly to `CPUExecutionProvider`.
* **Quantization**: INT8 dynamic quantization for embeddings (-74.7% footprint reduction with >0.95 cosine similarity retention); INT4 preparation for Hexagon NPU execution.
* **Verification Status**: **Snapdragon-Ready**. Automated hardware and QNN verification implemented via `scripts/qualcomm/verify_snapdragon.ps1` and `GET /api/system/ai-runtime/verify`.

---

## 10. Security & Encryption

* **Algorithm**: AES-256-GCM (Galois/Counter Mode) with 96-bit unique IVs and 128-bit authentication tags.
* **Key Protection**: Master keys are protected using **Windows DPAPI** (`CryptProtectData`), tying cryptographic access directly to the authenticated Windows user session.
* **Zero Plaintext Storage**: Keys are never hard-coded, never placed in `.env`, and never transmitted over API endpoints.
* **Tamper Proof**: Bit-level modifications in ciphertext fail GMAC authentication before plaintext decryption is attempted.

---

## 11. Installation

### Prerequisites
* Windows 11 (x86_64 or ARM64 Snapdragon)
* Python 3.10+ (Python 3.13 tested)
* Node.js v18+ (Node.js v24 tested)

### One-Command Setup
Clone the repository and run the setup script:

```powershell
git clone https://github.com/Lathika-Kumar/AuraGuard-Private-AI-Layer-for-Personal-Computing.git
cd AuraGuard-Private-AI-Layer-for-Personal-Computing
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

The setup script automatically creates the Python virtual environment, installs backend and frontend dependencies, validates directory structures, and prepares default environment configurations.

---

## 12. Running AuraGuard

### One-Command Launch
Start both the FastAPI backend and React frontend with a single command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

Console output displays detected hardware and active AI execution providers:
```text
AuraGuard started

Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173

Hardware:
12th Gen Intel(R) Core(TM) i5-1235U

AI Provider:
CPUExecutionProvider
```

Access the UI at `http://127.0.0.1:5173`.

---

## 13. Benchmarks

AuraGuard includes an automated, reproducible benchmark suite in `scripts/benchmark/` with warm-up cycles and statistical aggregation (mean, median, p95, min, max):

```powershell
backend\.venv\Scripts\python scripts\benchmark\run_all_benchmarks.py
```

Results are saved as structured JSON in `benchmarks/results/`:
* `encryption_benchmark.json`: AES-256-GCM throughput and DPAPI access latency (~0.008 ms/chunk).
* `embedding_benchmark.json`: ONNX embedding latency (~38.3 ms/single text) and throughput (~57.3 embeds/sec).
* `memory_benchmark.json`: ReMind memory creation (~66.7 ms) and semantic search (~60.1 ms).
* `llm_benchmark.json`: Qwen2.5-0.5B Time to First Token (~3.7 ms) and CPU token generation rate (~1.12 tokens/sec).
* `rag_benchmark.json`: End-to-end RAG pipeline breakdown (Privacy Check 1.7 ms, Retrieval 31.1 ms, Generation 12.0 s).

---

## 14. Hardware Support

| Platform | Processor | Execution Provider | Status |
| :--- | :--- | :--- | :--- |
| **Intel / AMD PC** | x86_64 CPU | `CPUExecutionProvider` | **Fully Verified** |
| **Windows on ARM** | Generic ARM64 CPU | `CPUExecutionProvider` | **Supported** |
| **Snapdragon X Elite / Plus** | Qualcomm Hexagon NPU | `QNNExecutionProvider` | **Snapdragon-Ready** (verified via QNN validation script) |

---

## 15. Limitations & Threat Boundaries

* **Live Process Memory**: A local user or root process running with Administrator privileges (`SeDebugPrivilege`) can read volatile RAM of running applications. Encryption protects data at rest, not live volatile heap memory.
* **CPU Generation Speed**: Generative LLM inference on low-power Intel mobile CPUs averages ~1.1 tokens/sec; Snapdragon NPU deployment is designed to accelerate this throughput substantially.
* **PDF Parsing**: AuraGuard uses text extraction; complex scanned bitmaps require local OCR tooling.

---

## 16. Project Structure

```text
AuraGuard/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI REST endpoints (ask, documents, memory, privacy, system)
│   │   ├── core/             # Configuration, logging, settings
│   │   ├── database/         # SQLite schema, migrations, connection management
│   │   ├── models/           # Pydantic schemas and database models
│   │   ├── security/         # AES-256-GCM, Windows DPAPI key manager
│   │   └── services/         # AI provider, embeddings, FAISS, privacy engine, ReMind
│   └── tests/                # 61 comprehensive backend pytest unit/integration tests
├── frontend/
│   ├── src/
│   │   ├── components/       # UI layout, pipeline flow visualizer, navigation
│   │   ├── pages/            # Dashboard, Ask, Documents, Memory (ReMind), Privacy Center
│   │   └── services/         # TypeScript API client
│   └── tests/                # Vitest frontend unit tests
├── scripts/
│   ├── setup.ps1             # One-command environment initialization
│   ├── start.ps1             # One-command dual-process launcher
│   ├── verify.ps1            # Deep subsystem verification suite
│   ├── benchmark/            # Reproducible benchmark suite (embedding, llm, rag, memory, crypto)
│   └── qualcomm/             # Snapdragon NPU & QNN verification scripts
├── benchmarks/results/       # Empirical benchmark JSON outputs
└── docs/                     # Architecture, threat model, demo script, submission portfolio
```

---

## 17. Testing

### Run All Backend Tests
```powershell
backend\.venv\Scripts\python -m pytest backend/tests -v
```
*(61/61 passing)*

### Run Frontend Tests & Build
```powershell
cd frontend
npm test
npm run build
```
*(4/4 passing, production build succeeded)*

### Run Subsystem Verification
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

### Run Snapdragon Hardware Validation
```powershell
powershell -ExecutionPolicy Bypass -File scripts\qualcomm\verify_snapdragon.ps1
```
