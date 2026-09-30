# AuraGuard Evidence: Qualcomm QNN Provider & Runtime Verification

## 1. Runtime State Differentiation
AuraGuard's verification service (`GET /api/system/ai-runtime/verify`) rigorously differentiates 5 sequential runtime states rather than collapsing them into a binary flag:

1. **Hardware Detected**: Verified Qualcomm Snapdragon silicon presence.
2. **QNN Installed**: Qualcomm QNN SDK or `onnxruntime-qnn` library present on the machine.
3. **QNN Available**: `QNNExecutionProvider` enumerated by `ort.get_available_providers()`.
4. **Provider & Model Loaded**: `ort.InferenceSession` successfully initialized with `providers=["QNNExecutionProvider"]` and model graph loaded.
5. **Inference Verified**: Actual tensor execution pass completed through the Qualcomm NPU.

---

## 2. Empirical Verification on Development Workstation
* **Command Executed**: `powershell -ExecutionPolicy Bypass -File scripts\qualcomm\verify_snapdragon.ps1`
* **API Result**: `GET /api/system/ai-runtime/verify`
```json
{
  "hardware_detected": false,
  "qnn_installed": false,
  "qnn_available": false,
  "provider_loaded": false,
  "model_loaded": false,
  "inference_verified": false,
  "active_fallback": "CPUExecutionProvider",
  "error_reason": null
}
```

---

## 3. Physical Snapdragon Deployment Procedure
When deploying AuraGuard on a Snapdragon Copilot+ PC (e.g. HP OmniBook X):
1. Install Qualcomm QNN SDK 2.22+ and `onnxruntime-qnn` for Windows ARM64.
2. Run `scripts\qualcomm\verify_snapdragon.ps1`.
3. The script verifies the full pipeline and activates `QNNExecutionProvider` on the Qualcomm Hexagon NPU.
