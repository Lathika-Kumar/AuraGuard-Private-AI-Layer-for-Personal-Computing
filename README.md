# AuraGuard — Private AI Layer for Personal Computing

AuraGuard is an on-device, privacy-first personal AI computing layer designed for local RAG, context-aware memory intelligence, and secure personal assistance with hardware acceleration on Qualcomm Snapdragon platforms.

```text
                    AURAGUARD
                        │
              ┌─────────┴─────────┐
              │                   │
         Private AI          Secure Storage
              │                   │
           ReMind              AES-256-GCM
              │                   │
            RAG                 DPAPI
              │                   │
         Privacy Engine           │
              │                   │
              └─────────┬─────────┘
                        ↓
                  AI Runtime
                        ↓
               ┌────────┴────────┐
               │                 │
              CPU              QNN
                                 ↓
                            Snapdragon
                                NPU
```

---

## Key Capabilities

1. **Zero-Cloud Local Neural AI**:
   - Neural semantic embeddings via `sentence-transformers/all-MiniLM-L6-v2` (FastEmbed / ONNX Runtime).
   - Local generative answering via `Qwen/Qwen2.5-0.5B-Instruct` (on-device CPU fallback and QNN NPU target).
   - 100% of user queries, documents, embeddings, and generative responses execute on the local machine with zero cloud API dependencies.

2. **Secure Local Storage & Encryption at Rest (Phase 5)**:
   - **Authenticated Encryption**: All document chunk text and ReMind memories are protected using **AES-256-GCM** (256-bit key, 96-bit IV, 128-bit authentication tag).
   - **Hardware/OS-Backed Key Management**: The master encryption key is protected using **Windows DPAPI** (`CryptProtectData`), tying key security directly to the authenticated Windows user session.
   - **FAISS Vector Index Protection**: Serialized FAISS indices are protected at rest via AES-256-GCM envelope encryption.
   - **Fail-Safe Integrity**: Any bit-flip or ciphertext tampering triggers instantaneous rejection and fail-safe abortion before decryption.
   - **Non-Destructive Migration**: Automatically detects and migrates pre-existing plaintext records to authenticated ciphertext with zero data loss.

3. **ReMind Private Context Intelligence**:
   - Long-term on-device personal memory store with semantic retrieval across personal facts, preferences, tasks, and goals.
   - Explicit user lifecycle control: create, inspect, update, archive, expire, and permanent cryptographic deletion.

4. **Multi-Checkpoint Privacy Engine**:
   - **Checkpoint 1 (Input Scan)**: Scans incoming user queries for sensitive credentials (API keys, private keys, passwords) and blocks prohibited inputs.
   - **Checkpoint 2 (Context Filtering)**: Sanitizes retrieved document and memory contexts; automatically neutralizes adversarial prompt injection vectors before passing to the LLM.
   - **Checkpoint 3 (Output Guard)**: Scans generated text to guarantee no accidental credential exfiltration before displaying answers.

5. **Qualcomm AI Hub & Snapdragon NPU Acceleration Path**:
   - *Target Architecture*: Qualcomm Snapdragon X Series (Oryon CPU + 45 TOPS Hexagon NPU).
   - *Model Precision*: INT8 dynamic quantization for embeddings (-74.7% disk footprint); INT4 (W4A16) preparation for Hexagon NPU.
   - *Execution Provider Abstraction*: Supports `auto`, `cpu`, and `qnn`.
   - *Current Verification Status*: Snapdragon NPU deployment path prepared and supported when compatible Qualcomm hardware and runtime are available. Active development host gracefully and automatically runs via `CPUExecutionProvider`.

---

## Architecture & Data Flow

```text
User Query / Document
         │
         ▼
[ Privacy Engine Checkpoint 1 ] ──> (Blocks raw credentials / injections)
         │
         ▼
[ Neural Embedding Generation ] ──> (ONNX Runtime FP32 / INT8)
         │
         ▼
[ Dense FAISS Vector Search ] ───> (Decrypted in-memory from AES-256-GCM envelope)
         │
         ▼
[ Secure SQLite Retrieval ] ─────> (AES-256-GCM Decryption with DPAPI Master Key)
         │
         ▼
[ Context Merger & Provenance ]
         │
         ▼
[ Privacy Engine Checkpoint 2 ] ──> (Neutralizes prompt injections & redacts PII)
         │
         ▼
[ Local LLM (Qwen2.5-0.5B) ] ───> (CPU Execution Provider / QNN NPU target)
         │
         ▼
[ Output Privacy Guard ] ────────> (Final output verification & shielding)
         │
         ▼
Grounded Local Answer
```

---

## Security Specifications

| Layer | Mechanism | Protection Scope |
| :--- | :--- | :--- |
| **Document Chunks** | AES-256-GCM | Encrypted at rest in SQLite `document_chunks` table |
| **ReMind Memories** | AES-256-GCM | Encrypted at rest in SQLite `memories` table |
| **Vector Index** | AES-256-GCM Envelope | Encrypted at rest in `data/index/faiss.index` |
| **Master Key** | Windows DPAPI | Protected on disk using local Windows user credentials |
| **Network Boundaries** | Localhost Bound | 0 External outbound network requests for inference |
| **Integrity** | 128-bit GCM Auth Tag | Detects and rejects any single-bit ciphertext tampering |

---

## Quick Start

### 1. Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to access the AuraGuard Dashboard, Ask Page, Privacy Center, and ReMind Memory interface.

---

## Running Automated Verification Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

---

## Verification & Limitations

- **Current Machine**: 12th Gen Intel Core i5-1235U, Windows 11 x86_64, ~7.65 GB RAM.
- **Active Execution Provider**: `CPUExecutionProvider` (Qualcomm Hexagon NPU is not physically present on Intel development host).
- **Physical Snapdragon Verification**: Snapdragon benchmarks and NPU execution require deployment on physical Windows on ARM hardware (e.g. Snapdragon X Elite laptop).
