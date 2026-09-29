# AuraGuard Phase 4 — Verified Limitations

This document explicitly catalogs verified technical limitations on the current host system and the operational constraints of the Qualcomm AI Hub / Snapdragon NPU integration.

---

## 1. Hardware Environment Limitations

- **Development Host**: 12th Gen Intel Core i5-1235U with ~7.65 GB RAM, running Windows 11 Enterprise (x86_64).
- **Snapdragon NPU Absent**: No physical Qualcomm Snapdragon processor, Hexagon NPU, or Qualcomm Compute Platform hardware is present on this development host.
- **QNN Execution Provider Unavailable**: `onnxruntime-qnn` and Qualcomm QNN SDK libraries are ARM64/Snapdragon specific and cannot initialize on an Intel x86_64 platform.
- **CPU Fallback Active**: All local neural operations gracefully and automatically fall back to `CPUExecutionProvider` on host CPU.

---

## 2. Model & Pipeline Limitations

- **LLM ONNX Graph Tracing on 8GB Host**:
  - Tracing a 494M parameter LLM graph with full attention heads and dynamic KV-cache requires >8 GB physical RAM during PyTorch symbolic trace unrolling.
  - On the 8GB development workstation, running local trace exceeds physical RAM and is cleanly prevented to avoid OS freeze.
  - The official and recommended Snapdragon path is Qualcomm AI Hub pre-compiled QNN context binaries (`qai_hub_models.models.qwen2_5_0_5b_instruct`), which compile directly for Hexagon NPU without requiring local host tracing.
- **Embedding INT8 Execution on x86 vs NPU**:
  - The embedding model has been successfully quantized to INT8 (`21.82 MB`, 74.7% size reduction).
  - On Intel Core i5-1235U without VNNI-optimized INT8 ONNX kernels, inference latency is approximately 10.7 ms (comparable to FP32's 9.87 ms).
  - Acceleration requires Qualcomm Hexagon NPU vector engines.

---

## 3. Cloud / Compilation Limitations

- **Qualcomm AI Hub Credentials**:
  - Qualcomm AI Hub compilation CLI requires a valid `QAI_HUB_API_TOKEN` and an active Qualcomm developer account.
  - In the absence of an API token, `ai_hub_compile.py` safely pauses at the authentication boundary without generating mock binaries or fabricating compilation status.

---

## 4. Encryption at Rest Status

- **Status**: Evaluated and documented in `docs/storage-encryption-evaluation.md`.
- **Reason for Deferral**: Native `sqlcipher3` C extension compilation has severe portability and build risks on Windows x86_64 and Windows ARM64. Field-level encryption via Python `cryptography` + Windows DPAPI is scheduled for Phase 5 to prevent risking user database corruption.
