# AuraGuard AI Runtime Architecture & System Endpoints

## 1. Overview

The AuraGuard AI Runtime provides a unified, hardware-aware execution layer for local neural models on personal computing devices. It orchestrates neural embeddings, vector retrieval, and local causal language models while dynamically adapting to available hardware acceleration (Qualcomm Hexagon NPU vs. Host CPU).

---

## 2. System Endpoints

The backend exposes two dedicated REST API endpoints under `/api/system` for hardware telemetry and AI runtime inspection:

### `GET /api/system/hardware`
Returns exhaustive host hardware specifications and acceleration device availability.

**Example Response:**
```json
{
  "os": {
    "system": "Windows",
    "release": "11",
    "version": "10.0.26200",
    "platform": "Windows-11-10.0.26200-SP0"
  },
  "cpu": {
    "brand": "12th Gen Intel(R) Core(TM) i5-1235U",
    "architecture": "AMD64",
    "physical_cores": 10,
    "logical_cores": 12
  },
  "gpu": {
    "name": "Intel(R) UHD Graphics"
  },
  "memory": {
    "total_bytes": 8216313856,
    "total_gb": 7.65,
    "available_bytes": 1782579200,
    "available_gb": 1.66,
    "percent_used": 78.3
  },
  "snapdragon": {
    "is_snapdragon": false,
    "processor_detected": null,
    "target_device": "Intel/AMD x86_64 Host"
  },
  "npu": {
    "npu_available": false,
    "npu_type": "None",
    "acceleration_active": false
  }
}
```

---

### `GET /api/system/ai-runtime`
Returns active AI execution providers, configured models, fallback status, and Qualcomm AI Hub readiness.

**Example Response:**
```json
{
  "runtime_status": "ready",
  "active_execution_provider": "CPUExecutionProvider",
  "configured_execution_provider": "auto",
  "fallback_occurred": false,
  "status_reason": "Snapdragon NPU/QNN not detected. Defaulting to optimized CPUExecutionProvider.",
  "available_execution_providers": [
    "AzureExecutionProvider",
    "CPUExecutionProvider"
  ],
  "qnn_available": false,
  "snapdragon_hardware": false,
  "npu_available": false,
  "models": {
    "embedding": {
      "model_name": "sentence-transformers/all-MiniLM-L6-v2",
      "runtime": "onnxruntime",
      "execution_provider": "CPUExecutionProvider",
      "dimension": 384,
      "precision": "float32",
      "device": "cpu"
    },
    "llm": {
      "model_id": "Qwen/Qwen2.5-0.5B-Instruct",
      "runtime": "pytorch",
      "execution_provider": "CPU",
      "device": "cpu",
      "precision": "float32",
      "max_new_tokens": 128
    }
  },
  "qualcomm_ai_hub": {
    "target_architecture": "Qualcomm Hexagon NPU / Snapdragon X Elite",
    "toolchain": "Qualcomm AI Hub SDK / QNN SDK",
    "compilation_targets": [
      "snapdragon_x_elite",
      "snapdragon_x_plus"
    ],
    "status": "ready_for_export"
  }
}
```

---

## 3. Provider Abstraction & Fallback Logic

The execution provider resolution is managed by `HardwareService.resolve_execution_provider()`:

```python
target = os.getenv("AI_EXECUTION_PROVIDER", "auto").lower()
```

* **`auto` (Default)**:
  - If `QNNExecutionProvider` is in `onnxruntime.get_available_providers()`, activates `QNNExecutionProvider` on Hexagon NPU.
  - Otherwise, cleanly selects `CPUExecutionProvider` without raising errors.
* **`qnn`**:
  - Attempts to bind `QNNExecutionProvider`.
  - If QNN is missing (e.g. running on an x86 PC or QNN runtime DLLs not present), sets `fallback_occurred = True`, logs an audit message, and seamlessly falls back to `CPUExecutionProvider`.
* **`cpu`**:
  - Forces `CPUExecutionProvider` on host CPU threads.

---

## 4. Frontend Integration

AuraGuard's web interface continuously monitors the AI runtime via `/api/system/ai-runtime` and displays live hardware metrics on the Dashboard:

1. **Acceleration Status Pill**: Shows either `"NPU Accelerated"` (green) or `"CPU Execution (Fallback Active)"` (amber).
2. **Hardware Metric Cards**:
   - Host Processor & Architecture
   - Snapdragon Platform Target
   - Qualcomm Hexagon NPU State & QNN EP Availability
   - Active Execution Provider
   - Active Neural Models (Embeddings & LLM)
3. **Live Query Telemetry**: Every answer returned on the `/ask` view displays execution duration along with the active execution provider badge (e.g. `• CPUExecutionProvider`).
