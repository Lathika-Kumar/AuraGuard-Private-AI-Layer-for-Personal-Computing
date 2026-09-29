# AuraGuard — Snapdragon NPU Architecture & Integration

## 1. Executive Summary

AuraGuard is engineered as a zero-cloud, privacy-preserving AI layer for personal computing, optimized specifically for **Qualcomm Snapdragon X Elite / Plus** platforms (such as the **HP OmniBook X**). 

By leveraging on-device neural acceleration through the **Qualcomm Hexagon NPU (45 TOPS)**, AuraGuard delivers low-latency retrieval-augmented generation (RAG) while ensuring that no sensitive personal documents or telemetry ever leave the user's physical machine.

---

## 2. Hardware Architecture & Acceleration Hierarchy

AuraGuard employs a dynamic three-tier execution hierarchy:

```
+--------------------------------------------------------------------+
|                       AuraGuard AI Core                            |
+---------------------------------+----------------------------------+
                                  |
            Hardware & Runtime Detection Service
         (backend/app/services/hardware_service.py)
                                  |
         +------------------------+------------------------+
         |                                                 |
[Snapdragon Detected: YES]                      [Snapdragon Detected: NO]
         |                                                 |
+--------v-------------------------+             +---------v-------------------------+
| Qualcomm Hexagon NPU (HTP)       |             | Local CPU (x86_64 / ARM fallback) |
| - QNN Execution Provider (EP)    |             | - CPUExecutionProvider            |
| - 45 TOPS INT8 / FP16 Compute    |             | - OpenMP / AVX2 / AVX-512         |
| - Sub-watt inference efficiency  |             | - Zero-Cloud Guaranteed Fallback  |
+----------------------------------+             +-----------------------------------+
```

### Hardware Acceleration Capabilities

| Component | Target Architecture | AuraGuard Role | Runtime / Execution Provider |
| :--- | :--- | :--- | :--- |
| **Hexagon NPU** | Qualcomm Hexagon V75 / HTP | Primary Neural Accelerator | `QNNExecutionProvider` (Qualcomm AI Engine Direct) |
| **Oryon CPU** | 12-core ARM64 64-bit | Orchestration, SQLite, FAISS | Host Python runtime (`python-3.13-arm64`) |
| **Adreno GPU** | Qualcomm Adreno X1-85 | Visual / Vector Math Fallback | DirectML Execution Provider |
| **Memory** | LPDDR5x (8448 MT/s) | Shared High-Bandwidth Unified RAM | Zero-copy vector buffer access |

---

## 3. Intelligent Runtime Detection & Graceful Fallback

AuraGuard incorporates an automated hardware detection service at `backend/app/services/hardware_service.py` that queries system hardware and ONNX Runtime providers at startup:

1. **System & Architecture Audit**:
   - Queries `platform.machine()`, `platform.processor()`, and system CIM controllers (`Win32_Processor`, `Win32_VideoController`).
   - Identifies Snapdragon platforms via ARM64 architecture and processor signature inspection (`Snapdragon`, `Qualcomm`, `SC8380XP`, `X Elite`, `X Plus`).
2. **NPU Availability Check**:
   - Inspects `onnxruntime.get_available_providers()` for `QNNExecutionProvider`.
   - Inspects Windows PNP `ComputeAccelerator` class for Qualcomm Hexagon NPU devices.
3. **Graceful CPU Fallback**:
   - When running on a non-Snapdragon host (e.g. Intel Core / AMD Ryzen development machines), the runtime automatically selects `CPUExecutionProvider`.
   - The user is notified via the frontend telemetry panel with an exact status reason:
     `"Snapdragon NPU/QNN not detected. Defaulting to optimized CPUExecutionProvider."`
   - Zero crashes, zero degraded functional capabilities.

---

## 4. Model Optimization & Quantization Pipeline

AuraGuard's local neural models are prepared for Snapdragon NPU execution via Qualcomm AI Hub:

| Model | Purpose | Baseline CPU Precision | Snapdragon NPU Target Precision | Optimized Runtime |
| :--- | :--- | :--- | :--- | :--- |
| **all-MiniLM-L6-v2** | Semantic Retrieval / Chunk Embedding | FP32 (ONNX) | INT8 / FP16 quantized (`.onnx` / `.bin`) | QNN EP / HTP Backend |
| **Qwen2.5-0.5B-Instruct** | Grounded Local Generation | FP32 (PyTorch) | INT4 (AWQ/GPTQ) / INT8 QNN Context Binary | Qualcomm AI Engine Direct (QNN) |

---

## 5. Deployment on Snapdragon-Powered HP PCs

To deploy AuraGuard on an HP OmniBook X or Snapdragon Copilot+ PC:

```powershell
# 1. Clone repository
git clone https://github.com/Lathika-Kumar/AuraGuard-Private-AI-Layer-for-Personal-Computing.git
cd AuraGuard-Private-AI-Layer-for-Personal-Computing

# 2. Install Qualcomm AI Hub & QNN ONNX Runtime on Windows on ARM (WoA)
pip install qai-hub onnxruntime-qnn

# 3. Configure environment
$env:AI_EXECUTION_PROVIDER = "auto"   # Automatically chooses QNN on Snapdragon
$env:MODEL_CACHE_DIR = "E:\Auraguard\models"

# 4. Launch backend and frontend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
