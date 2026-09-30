# AuraGuard Evidence: Hardware Verification

## 1. Verified Development Host Environment
* **Date of Verification**: 2026-09-30
* **Host Processor**: 12th Gen Intel(R) Core(TM) i5-1235U (10 cores, 12 threads)
* **Architecture**: `x86_64` (`AMD64`)
* **Operating System**: Windows 11 Home (Build 10.0.26100)
* **Active Execution Provider**: `CPUExecutionProvider`
* **Qualcomm Snapdragon Silicon**: **NOT DETECTED** (Intel host verified via CPUID and WMI)
* **Qualcomm Hexagon NPU**: **NOT AVAILABLE**

---

## 2. Hardware Detection Methodology
AuraGuard executes deep multi-attribute hardware introspection via `HardwareService` (`backend/app/services/hardware_service.py`):
1. **Registry Introspection**: Queries `HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0\ProcessorNameString` for genuine Qualcomm Snapdragon branding (`Snapdragon`, `Sc8380`, `X Elite`).
2. **Architecture Check**: Identifies Windows ARM64 vs generic x86_64/AMD64.
3. **WMI Provider Query**: Queries Win32_Processor to verify device hardware ID.
4. **Execution Provider Inspection**: Dynamically calls `ort.get_available_providers()` to identify registered ONNX execution providers.

---

## 3. Strict Anti-Hallucination Policy
* AuraGuard does NOT simulate Snapdragon silicon.
* AuraGuard does NOT misclassify ARM64 Windows as Snapdragon automatically.
* When executing on Intel x86 machines, AuraGuard accurately reports `Snapdragon: Not detected` and falls back cleanly to `CPUExecutionProvider`.
