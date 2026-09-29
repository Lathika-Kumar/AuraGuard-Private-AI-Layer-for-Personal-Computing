# AuraGuard Snapdragon X Elite (Windows ARM64) Deployment & Packaging Guide

This guide provides end-to-end instructions for deploying, packaging, and verifying AuraGuard on Qualcomm Snapdragon X Series compute platforms (Snapdragon X Elite, Snapdragon X Plus) running Windows 11 ARM64 with dedicated Qualcomm Hexagon NPU acceleration.

---

## 1. Prerequisites & Environment Specifications

### System Requirements
- **Device**: Windows 11 on ARM (e.g. HP OmniBook X, Snapdragon X Elite CRD)
- **CPU**: Qualcomm Oryon (12 cores up to 3.8 GHz)
- **NPU**: Qualcomm Hexagon NPU (45 TOPS)
- **Operating System**: Windows 11 ARM64 (Build 26100+)
- **System RAM**: 16 GB LPDDR5x (unified memory)
- **Disk Space**: At least 10 GB free space on SSD

### Software Dependencies
- **Python**: Python 3.11 or 3.12 (ARM64 native Windows build from python.org)
- **Node.js**: Node.js v20+ (ARM64 native build)
- **Qualcomm QNN SDK**: Qualcomm Neural Processing SDK for Windows on Snapdragon (v2.22+)
- **ONNX Runtime**: `onnxruntime-qnn` ARM64 wheel (`pip install onnxruntime-qnn`)

---

## 2. Environment Setup

### A. Python Environment
Clone the repository and set up a native ARM64 virtual environment:

```powershell
# In PowerShell (ARM64)
git clone https://github.com/Lathika-Kumar/AuraGuard-Private-AI-Layer-for-Personal-Computing.git
cd AuraGuard-Private-AI-Layer-for-Personal-Computing

# Create virtual environment
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r backend\requirements.txt

# Install ONNX Runtime with Qualcomm QNN Execution Provider
pip install onnxruntime-qnn
```

### B. Environment Configuration (`.env`)
Create or edit `.env` in the repository root:

```env
# Application Settings
APP_NAME=AuraGuard
APP_ENV=production
APP_DEBUG=false

# Storage & Privacy
DATA_DIR=./data
DB_PATH=./data/auraguard.db
PRIVACY_MODE=balanced
REMIND_ENABLED=true

# AI Hardware & Execution Provider
AI_EXECUTION_PROVIDER=auto
QUALCOMM_TARGET=snapdragon_x_elite
EMBEDDING_PRECISION=int8
LLM_PRECISION=int4

# Qualcomm AI Hub Compilation Token (Optional for developers)
QAI_HUB_API_TOKEN=
```

---

## 3. QNN Model Artifacts Deployment

For Snapdragon NPU execution, place the pre-compiled QNN context binaries in `models/qnn/`:

```text
models/
├── onnx/
│   ├── embedding_model.onnx       (86.20 MB - FP32)
│   └── embedding_model_int8.onnx  (21.82 MB - INT8)
└── qnn/
    ├── all_minilm_l6_v2_int8.bin   (QNN NPU context binary)
    └── qwen2_5_0_5b_w4a16.bin      (QNN NPU context binary)
```

### Automatic Hardware Detection & Provider Resolution
AuraGuard's `HardwareService` automatically resolves the execution provider:
1. Queries `sys.platform` and processor architecture for `arm64`.
2. Inspects `onnxruntime.get_available_providers()` for `QNNExecutionProvider`.
3. If both are detected and QNN context binaries exist, activates `QNNExecutionProvider` on Hexagon NPU.
4. If missing, automatically falls back to `CPUExecutionProvider` without raising runtime exceptions.

---

## 4. Verification on Device

### Verify Hardware Detection
```bash
curl http://localhost:8000/api/system/hardware
```

Expected Response on Snapdragon Laptop:
```json
{
  "os": {
    "system": "Windows",
    "release": "11",
    "machine": "ARM64"
  },
  "snapdragon": {
    "is_snapdragon": true,
    "confidence": 1.0,
    "indicators": ["Processor name matches Snapdragon", "Machine architecture is ARM64"]
  },
  "qnn": {
    "available": true,
    "execution_provider": "QNNExecutionProvider"
  }
}
```

### Verify Local Storage Encryption
```bash
curl http://localhost:8000/api/system/security
```

Expected Response:
```json
{
  "storage_encryption": true,
  "algorithm": "AES-256-GCM",
  "key_length_bits": 256,
  "key_protection": "Windows DPAPI",
  "database_encrypted": true,
  "memory_encrypted": true,
  "documents_encrypted": true,
  "faiss_protection": "AES-256-GCM envelope at rest",
  "local_only": true,
  "cloud_leakage": false
}
```

---

## 5. Running the Application

### Start Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Start Frontend
```powershell
cd frontend
npm install
npm run build
npm run preview
```
Visit `http://localhost:5173` to access the AuraGuard Dashboard.
