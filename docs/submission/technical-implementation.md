# AuraGuard — Technical Implementation Details

## Technology Stack

### Backend
* **Language & Runtime**: Python 3.10+ (tested on Python 3.13)
* **Web Framework**: FastAPI with Pydantic v2 schemas and Uvicorn ASGI server
* **Relational Store**: SQLite with WAL mode, parameterized queries, and custom migrations
* **Vector Store**: FAISS (`IndexFlatL2`, 384-dimensional dense vectors)
* **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` via ONNX Runtime
* **Generative LLM**: `Qwen/Qwen2.5-0.5B-Instruct` via HuggingFace Transformers / ONNX Runtime
* **Cryptography**: `cryptography` library (AES-256-GCM authenticated cipher)
* **Key Management**: Windows DPAPI via `ctypes` (`CryptProtectData` / `CryptUnprotectData`)
* **Document Processing**: `pypdf` stream extraction with recursive character chunking

### Frontend
* **Framework**: React 18 with TypeScript
* **Build Tool**: Vite
* **Styling**: Vanilla CSS design system with responsive cards, glassmorphic accents, and CSS variables
* **Icons**: `lucide-react`
* **Routing**: Page-based state routing (`Dashboard`, `Ask`, `Documents`, `Memory`, `Privacy Center`)
* **Testing**: Vitest with React Testing Library

---

## Key Subsystems

### 1. Cryptographic Security Engine (`app/security/`)
* **`encryption_service.py`**: Handles AES-256-GCM chunk and envelope encryption. Prepend format identifier `AG1$` followed by base64-encoded `IV (12 bytes) + Tag (16 bytes) + Ciphertext`.
* **`key_manager.py`**: Manages master key lifecycle. Uses Windows DPAPI to encrypt the master key on disk into `.key_store`.

### 2. Neural Vector Service (`app/services/vector_service.py`)
* Manages dual FAISS indices: `documents` (chunks) and `memories` (ReMind entries).
* Index serialization encrypts the in-memory index using AES-256-GCM before writing to disk.
* Real-time metadata tracking with dimension validation and vector count verification.

### 3. ReMind Memory Service (`app/services/remind_service.py`)
* Implements memory creation lifecycle: pre-validation, Privacy Engine scan, AES-256-GCM encryption, SQLite insertion, and FAISS indexing.
* Implements guaranteed deletion: SQLite record deletion, FAISS index vector removal, and verification query.

### 4. Privacy Engine (`app/services/privacy_service.py`)
* **Checkpoint 1**: Regular expression secret scanner (`AWS_KEY`, `OPENAI_KEY`, `RSA_PRIVATE_KEY`, `PASSWORD`).
* **Checkpoint 2**: Prompt injection sanitization removing patterns like `(?i)(ignore\s+all\s+previous\s+instructions|system\s+prompt\s+override)`.
* **Checkpoint 3**: Output PII scanner redacting emails, phone numbers, and secrets.

### 5. Hardware & AI Runtime (`app/services/hardware_service.py`)
* Detects CPU architecture (`x86_64`, `ARM64`, `AMD64`).
* Inspects Windows registry and WMI processor identifiers to detect Qualcomm Snapdragon silicon.
* Queries ONNX Runtime available providers (`QNNExecutionProvider`, `CPUExecutionProvider`).
* Exposes `GET /api/system/ai-runtime/verify` reporting live empirical status.
