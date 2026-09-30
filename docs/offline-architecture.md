# AuraGuard: Offline & Local Architecture

This document specifies the on-device execution topology of AuraGuard, detailing the local pipeline that operates without external cloud LLM dependencies.

---

## 1. Local Processing Pipeline Topology

Every user interaction—from document ingestion to conversational query resolution—is processed strictly within the local host boundary:

```text
User
 ↓
Local Frontend (React / Vite on 127.0.0.1:5173)
 ↓
Local Backend (FastAPI on 127.0.0.1:8000)
 ↓
Local Privacy Engine (Pre-scan for API keys, passwords, prompt injections)
 ↓
Local Embedding Engine (all-MiniLM-L6-v2 dynamic INT8 via ONNX Runtime)
 ↓
Local FAISS Vector Store (FlatL2 384-d dense index with AES-256-GCM envelope encryption)
 ↓
Local ReMind Store (Encrypted SQLite episodic memories)
 ↓
Local LLM (Qwen2.5-0.5B-Instruct on-device neural synthesis)
 ↓
Local Answer (Attributed output with exact source and page references)
```

---

## 2. Snapdragon Hardware Acceleration Path

When running on Snapdragon X Series hardware with active Qualcomm QNN drivers, the local AI execution path routes through the dedicated NPU:

```text
Local AI
 ↓
QNN Execution Provider (ONNX Runtime QNN EP / QnnHtp.dll)
 ↓
Hexagon NPU (45 TOPS rated hardware capability)
```

On non-Snapdragon or development systems (such as the verified Intel Core i5 host), the system automatically routes to:

```text
Local AI
 ↓
CPUExecutionProvider (Multi-threaded Intel/AMD CPU execution)
```

---

## 3. Network Isolation Boundary & Scope

- **Local Host Binding**: All backend endpoints are bound exclusively to the local loopback interface (`127.0.0.1`).
- **Zero Cloud Inference**: No generative inference, embedding vectorization, or semantic ranking request leaves the machine.
- **Initial Setup Scope**: The initial environment installation and model weight downloads require internet connectivity. Once weights are cached in `models/` or HuggingFace local cache, normal runtime operation requires zero outbound internet traffic.
- **No Telemetry**: AuraGuard contains zero telemetry tracking, zero usage analytics reporting, and zero external logging endpoints.
