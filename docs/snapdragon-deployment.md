# AuraGuard — Snapdragon Deployment Guide

This guide describes the complete procedure for deploying and running **AuraGuard** on Snapdragon X Series hardware (Windows 11 ARM64), utilizing Qualcomm AI Hub and the ONNX Runtime QNN Execution Provider.

---

## 1. Prerequisites

### Target Hardware Architecture
- **Processor**: Snapdragon® X Elite (e.g., X1E-80-100) or Snapdragon® X Plus
- **NPU**: Qualcomm® Hexagon™ NPU (45 TOPS rated hardware capability)
- **Host OS**: Windows 11 ARM64 (Build 26100+ recommended)
- **System Memory**: 16 GB+ Unified LPDDR5x RAM

### Software Toolchain
- **Python**: 3.10, 3.11, or 3.12 (ARM64 native Windows build)
- **Node.js**: v18.x, v20.x, or v22.x (ARM64 native Windows build)
- **Git for Windows** (ARM64)
- **Qualcomm Snapdragon NPU Driver**: Installed via Windows Update or OEM Driver Pack

---

## 2. Environment Verification: Intel Host vs. Snapdragon Hardware

AuraGuard is architected with a strict hardware abstraction layer (`backend/app/hardware/detection.py`). The table below clarifies the status of components across environments:

| Component | Verified on Intel Core i5 (Baseline) | Requires Snapdragon X Series Hardware |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 x86_64 | Windows 11 ARM64 |
| **Execution Provider** | `CPUExecutionProvider` | `QNNExecutionProvider` |
| **Embedding Engine** | INT8 ONNX MiniLM (CPU) | QNN HTP / NPU Context Binary |
| **Local LLM** | Qwen2.5-0.5B-Instruct (CPU) | QNN Quantized GenAI Model |
| **Vector DB** | FAISS FlatL2 (CPU) | FAISS FlatL2 |
| **Storage Security** | AES-256-GCM + Windows DPAPI | AES-256-GCM + Windows DPAPI |
| **Privacy Engine** | Local Regex & Entropy Tokenizer | Local Regex & Entropy Tokenizer |
| **Hardware Detection** | Reports Intel, CPU provider | Reports Snapdragon, QNN provider |

---

## 3. Environment Variables Configuration

Create a `.env` file in the project root:

```ini
# Execution provider: auto, qnn, or cpu
AURA_EXECUTION_PROVIDER=auto

# Qualcomm AI Hub Token (DO NOT COMMIT REAL VALUE)
QAI_HUB_API_TOKEN=

# Local Server Settings
HOST=127.0.0.1
PORT=8000
FRONTEND_PORT=5173
DATABASE_URL=sqlite:///./auraguard.db
ENCRYPTION_MASTER_KEY_PROTECTION=dpapi
```

> **IMPORTANT**: Never commit `QAI_HUB_API_TOKEN` to source control. It is ignored in `.gitignore`.

---

## 4. Software Installation & Model Artifacts

### 4.1 Backend Setup (Windows ARM64)
```powershell
cd E:\Auraguard\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install onnxruntime-qnn --extra-index-url https://aihub.qualcomm.com/wheels/
```

### 4.2 Frontend Setup
```powershell
cd E:\Auraguard\frontend
npm install
npm run build
```

### 4.3 Model Artifacts Preparation

AuraGuard uses the following models:

1. **Embedding Model**:
   - Model: `sentence-transformers/all-MiniLM-L6-v2`
   - Quantization: Dynamic INT8 (`models/embeddings/model_quantized.onnx`)
   - QNN HTP Context: Generated via Qualcomm AI Hub CLI or `scripts/qualcomm/compile_qnn_artifacts.py`

2. **Generative Language Model**:
   - Model: `Qwen/Qwen2.5-0.5B-Instruct`
   - Runtime: Local ONNX / HuggingFace Transformers pipeline
   - Precision: FP32 (CPU baseline) / INT4/W4A16 (Qualcomm AI Hub NPU target)

---

## 5. Runtime Verification Commands

Run the platform detection test suite:

```powershell
# 1. Verify Snapdragon Hardware Detection
.\scripts\qualcomm\verify_snapdragon.ps1

# 2. Validate Artifact Integrity and Execution Provider
python .\scripts\qualcomm\validate_artifacts.py

# 3. Run Backend Verification
pytest backend/tests/test_hardware_detection.py -v
pytest backend/tests/test_qualcomm_onnx.py -v
```

Expected output on Snapdragon ARM64 with QNN installed:
```text
Platform Architecture: ARM64
Processor: Snapdragon(R) X Elite
Qualcomm NPU Driver: Detected
Execution Provider: QNNExecutionProvider
QNN Fallback Mechanism: Validated (graceful fall-through to CPU on unsupported operators)
```

---

## 6. Benchmarking on Snapdragon

When executing on physical Snapdragon hardware, run the standard suite to record empirical measurements:

```powershell
# Run Full Hardware & Latency Benchmark
.\scripts\qualcomm\run_full_benchmark.ps1
```

The script records:
- Single-query embedding latency (mean, median, p95)
- Batch-8 embedding throughput (texts/sec)
- LLM Time to First Token (TTFT, ms)
- LLM Token Generation Rate (tokens/sec)
- End-to-end RAG retrieval + synthesis latency (ms)
- Peak Resident Set Size (RSS memory in MB)

Output is stored directly to `benchmark_results/` with ISO timestamps and hardware metadata.

---

## 7. Troubleshooting

1. **`QNNExecutionProvider not found in available providers`**:
   - Cause: `onnxruntime-qnn` wheel not installed or `QnnHtp.dll` not on system PATH.
   - Fix: Ensure `onnxruntime-qnn` is installed and the Hexagon driver package is up-to-date. AuraGuard automatically falls back to `CPUExecutionProvider`.

2. **Model Graph Parsing Error during NPU Execution**:
   - Cause: An operator in the ONNX graph is not supported by the Hexagon NPU HTP backend.
   - Fix: AuraGuard's execution layer captures EP initialization errors and transparently switches to CPU fallback without interrupting user queries.

3. **Missing Qualcomm AI Hub Token**:
   - Set the token in PowerShell: `$env:QAI_HUB_API_TOKEN="<token>"`. Do not hardcode into source files.
