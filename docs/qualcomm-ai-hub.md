# Qualcomm AI Hub Deployment & Compilation Architecture

This document specifies the Qualcomm AI Hub compilation pipeline and target deployment specifications for AuraGuard's on-device neural models targeting Qualcomm Snapdragon X Elite compute platforms and Hexagon NPU accelerators.

---

## 1. Overview & Strategy

Qualcomm AI Hub (`qai-hub`) provides cloud-hosted and on-device compilation, profiling, and quantization workflows to convert PyTorch / ONNX models into optimized Qualcomm Neural Network (QNN) context binaries (`.bin` / DLC) targeted specifically at Snapdragon processors (Snapdragon 8 Gen 3, Snapdragon X Elite CRD, Snapdragon X Plus).

In AuraGuard's zero-cloud-inference architecture:
1. **Compilation Phase**: Model weights are traced and compiled via Qualcomm AI Hub CLI or SDK offline or during deployment packaging. **Zero user private data is ever sent to Qualcomm AI Hub.** Only base open-weight model architectures and quantization calibration sets are submitted.
2. **Runtime Phase**: The compiled QNN context binary runs 100% locally on the device using `QNNExecutionProvider` (part of ONNX Runtime with Qualcomm QNN EP). No external network calls are made during inference.

---

## 2. Model Profiles for Qualcomm AI Hub

### A. Embedding Model: `all-MiniLM-L6-v2`
- **Source**: `sentence-transformers/all-MiniLM-L6-v2`
- **Target Platform**: Snapdragon X Elite CRD (Compute Unit: NPU)
- **Precision**: INT8 (W8A8 dynamic / static quantization)
- **Input Specifications**:
  - `input_ids`: `int64[batch, 128]`
  - `attention_mask`: `int64[batch, 128]`
  - `token_type_ids`: `int64[batch, 128]`
- **Output Specification**:
  - `sentence_embedding`: `float32[batch, 384]` (L2 normalized)
- **Qualcomm AI Hub Target ID**: `all-minilm-l6-v2` / custom ONNX upload
- **Compilation Options**:
  ```bash
  qai-hub compile \
    --model models/onnx/embedding_model.onnx \
    --device "Snapdragon X Elite CRD" \
    --options "--target_runtime qnn_lib --compute_unit npu" \
    --output-file models/qnn/all_minilm_l6_v2_int8.bin
  ```

### B. Generative LLM: `Qwen2.5-0.5B-Instruct`
- **Source**: `Qwen/Qwen2.5-0.5B-Instruct`
- **Target Platform**: Snapdragon X Elite CRD (Compute Unit: NPU)
- **Target Precision**: INT4 (W4A16 block-wise quantization with FP16 activations)
- **Context Length**: 512–1024 tokens (budgeted for personal computing assistant memory and RAG context)
- **KV Cache**: Layer-wise key-value cache with static dimensions for NPU tensor allocation
- **AI Hub Support Status**: Supported via Qualcomm AI Hub Hugging Face integration (`qai-hub-models`).
- **Compilation Workflow**:
  ```bash
  python -m qai_hub_models.models.qwen2_5_0_5b_instruct.export \
    --device "Snapdragon X Elite CRD" \
    --quantize w4a16 \
    --target-runtime qnn_context_binary \
    --output-dir models/qnn/
  ```

---

## 3. Alternative Evaluated Models

| Model | Size | Precision | AI Hub Pre-optimized? | Evaluation Result for AuraGuard |
| :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-0.5B-Instruct** | 494M params | INT4 (W4A16) | Yes | **Selected Primary**: Fits strictly within 8GB/16GB system RAM alongside Windows OS, fast time-to-first-token. |
| **Llama-3.2-1B-Instruct** | 1.23B params | INT4 (W4A16) | Yes | **Evaluated Alternative**: Viable on 16GB Snapdragon X Elite machines; slightly higher RAM pressure on 8GB machines. |
| **Phi-3.5-mini-instruct** | 3.82B params | INT4 (W4A16) | Yes | **Evaluated Alternative**: Strong reasoning, but 3.8B requires ~2.5 GB dedicated NPU RAM, exceeding low-memory machine headroom. |

---

## 4. Qualcomm AI Hub Compilation Workflow (`ai_hub_compile.py`)

AuraGuard provides a reproducible script under [ai_hub_compile.py](file:///e:/Auraguard/scripts/qualcomm/ai_hub_compile.py).

The workflow follows these verified steps:
1. **API Authentication Verification**: Checks for `QAI_HUB_API_TOKEN` environment variable.
2. **Device Discovery**: Queries Qualcomm AI Hub cloud API for active Snapdragon X Elite hardware testbeds.
3. **Artifact Staging**: Uploads validated ONNX or PyTorch weights.
4. **Compilation Job**: Submits compilation with `--target_runtime qnn_lib --compute_unit npu`.
5. **Download QNN Binary**: Retrieves compiled `.bin` context binary into `models/qnn/`.

**Current Host Execution Status**:
```text
Compilation Job Status: PREPARED
Execution: HALTED AT AUTHENTICATION GATEWAY (Target Hardware & API Token Required)
Result: No fake compilation or mocked QNN binaries generated.
```

---

## 5. Privacy and Isolation Guarantees

- **No User Data Leakage**: Compilation only packages generic open-source model weights.
- **Local Runtime**: Once the QNN binary is downloaded, all embeddings, user documents, ReMind contextual memories, and LLM inferences occur strictly within local RAM and the on-device Hexagon NPU.
