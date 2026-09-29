# AuraGuard ONNX Export & Validation Pipeline

This document records the technical architecture, execution results, and validation metrics for exporting AuraGuard's neural models to ONNX.

---

## 1. Architecture Overview

To support execution across standard x86_64 CPUs, ARM64 CPUs, and Qualcomm Hexagon NPUs via ONNX Runtime (`onnxruntime` / `onnxruntime-qnn`), models are exported from PyTorch to standard ONNX representations.

The pipeline comprises three reproducible scripts in `scripts/qualcomm/`:
1. `export_embedding_onnx.py`: Traces and exports `sentence-transformers/all-MiniLM-L6-v2` with dynamic axes.
2. `export_llm_onnx.py`: Prepares export configuration for `Qwen2.5-0.5B-Instruct`.
3. `validate_onnx.py`: Validates ONNX structure and verifies output numerical consistency.

---

## 2. Embedding Model Export Details

- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Architecture**: 6-layer BERT encoder with mean pooling and L2 normalization
- **Wrapper**: `EmbeddingWrapper` encapsulating Transformer backbone, attention masking, token type handling, mean pooling, and L2 normalization directly inside the ONNX compute graph.
- **Export Command**:
  ```bash
  python scripts/qualcomm/export_embedding_onnx.py
  ```
- **Export Results**:
  - File: `models/onnx/embedding_model.onnx`
  - File Size: **86.20 MB** (FP32)
  - Inputs:
    - `input_ids`: dynamic `[batch_size, sequence_length]`, int64
    - `attention_mask`: dynamic `[batch_size, sequence_length]`, int64
    - `token_type_ids`: dynamic `[batch_size, sequence_length]`, int64
  - Outputs:
    - `sentence_embedding`: dynamic `[batch_size, 384]`, float32
  - Opset Version: **17**

---

## 3. ONNX Model Validation & Numerical Correctness

The validation script [validate_onnx.py](file:///e:/Auraguard/scripts/qualcomm/validate_onnx.py) tests structural integrity and compares ONNX Runtime outputs directly against PyTorch reference outputs across 4 distinct test sentences:

```text
1. "AuraGuard is a privacy-first AI layer for personal computing."
2. "Snapdragon X Elite features a dedicated Hexagon NPU for local AI inference."
3. "All personal documents and memory items remain encrypted and local."
4. "Defending against prompt injections and memory poisoning attacks."
```

### Validation Results

| Test Sentence | PyTorch Norm | ONNX Norm | Max Abs Difference | Cosine Similarity |
| :--- | :--- | :--- | :--- | :--- |
| Sentence 1 | 1.000000 | 1.000000 | 1.19e-07 | **1.000000** |
| Sentence 2 | 1.000000 | 1.000000 | 1.19e-07 | **1.000000** |
| Sentence 3 | 1.000000 | 1.000000 | 1.19e-07 | **1.000000** |
| Sentence 4 | 1.000000 | 1.000000 | 1.19e-07 | **1.000000** |

- **Structural Check (`onnx.checker.check_model`)**: PASSED
- **Cosine Similarity**: **1.000000** across all test vectors.
- **Acceptance Criterion**: Cosine similarity $\ge 0.9990$ (MET with 1.000000).

---

## 4. Generative LLM Export Analysis

- **Model**: `Qwen/Qwen2.5-0.5B-Instruct` (494 Million parameters)
- **Host Execution Observation**:
  - Full ONNX graph tracing with dynamic KV-cache requires loading model weights and tracing multi-headed attention graphs simultaneously in PyTorch memory. On an 8GB host machine with Windows system overhead, running full graph unrolling triggers high memory allocation pressure.
  - Export script [export_llm_onnx.py](file:///e:/Auraguard/scripts/qualcomm/export_llm_onnx.py) handles host memory limits cleanly without crashing, logging diagnostic requirements:
    ```text
    Status: PREPARED
    Requirement: 16GB+ RAM dedicated export workstation OR Qualcomm AI Hub Cloud CLI
    ```
  - For Snapdragon deployment, the recommended and supported path is using Qualcomm AI Hub's pre-compiled package (`qai_hub_models.models.qwen2_5_0_5b_instruct`), which compiles directly on cloud Snapdragon testbeds into a QNN context binary.
