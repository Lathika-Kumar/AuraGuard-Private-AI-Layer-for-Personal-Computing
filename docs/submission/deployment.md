# AuraGuard — Deployment Guide

## Target Environments

### 1. Windows x86_64 PC (Development & Baseline Host)
* **Processor**: 12th Gen Intel Core i5-1235U (or equivalent modern x86 CPU)
* **RAM**: 8 GB+
* **Execution Provider**: `CPUExecutionProvider`
* **Status**: Fully verified; 100% tests passing.

### 2. Qualcomm Snapdragon Copilot+ PC (Production Hardware Target)
* **Processor**: Snapdragon X Elite / Snapdragon X Plus (Oryon CPU + Hexagon NPU 45 TOPS)
* **OS**: Windows 11 on ARM64
* **Execution Provider**: `QNNExecutionProvider` (Qualcomm Neural Network)
* **Status**: Architecture and validation workflows complete; ready for hardware verification.

---

## One-Command Deployment

### Step 1: Environment Setup
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```
This automated script:
1. Validates Python and Node.js runtimes.
2. Creates the Python virtual environment in `backend/.venv`.
3. Installs backend requirements from `backend/requirements.txt`.
4. Installs frontend dependencies via `npm install` in `frontend/`.
5. Prepares configuration `.env` file from `.env.example`.
6. Initializes directory structures and verifies model dependencies.

### Step 2: Subsystem Verification
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```
Executes deep automated checks across SQLite, AES-256-GCM encryption, DPAPI, FAISS, ONNX, Privacy Engine, and ReMind.

### Step 3: Application Launch
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```
Spawns the FastAPI backend (`http://127.0.0.1:8000`) and Vite frontend (`http://127.0.0.1:5173`) in parallel, printing detected hardware and active AI execution providers in the console.

---

## Snapdragon NPU Validation Workflow

When deploying on a Snapdragon Copilot+ PC:
1. Install Qualcomm QNN SDK and `onnxruntime-qnn` for Windows ARM64.
2. Run the dedicated validation script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\qualcomm\verify_snapdragon.ps1
   ```
3. The script verifies:
   * ARM64 Windows architecture.
   * Snapdragon processor silicon identification.
   * `QNNExecutionProvider` availability in ONNX Runtime.
   * Model artifact loading and on-device Hexagon NPU inference.
