# AuraGuard Model Deployment Matrix

This document tracks the deployment and compilation status of all AI models utilized in the AuraGuard Private AI Layer across host architectures, ONNX pipelines, Qualcomm AI Hub, and Qualcomm Hexagon NPU (Snapdragon X Elite).

---

## Deployment Matrix

| Model | Current Runtime | Current Precision | ONNX Export | AI Hub Support | QNN Support | Snapdragon Target | Quantization | Status | Blocking Issue |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **all-MiniLM-L6-v2** *(Embedding)* | FastEmbed / ONNX Runtime | FP32 | Supported | Supported | Supported | Snapdragon X Elite (Compute Unit: NPU) | INT8 (W8A8 / Dynamic) | **PREPARATION COMPLETE** | Target Hardware Required for QNN EP execution |
| **Qwen2.5-0.5B-Instruct** *(LLM)* | PyTorch Transformers | FP32 | Supported / Prepared | Supported | Supported | Snapdragon X Elite (Compute Unit: NPU) | INT4 (W4A16) / INT8 (W8A16) | **PREPARATION COMPLETE** | Target Hardware Required for QNN EP execution |
| **Llama-3.2-1B-Instruct** *(Alternative LLM)* | Evaluated | FP16 | Supported | Supported | Supported | Snapdragon X Elite | INT4 | **EVALUATED ALTERNATIVE** | Memory footprint higher on 8GB host |
| **Phi-3.5-mini-instruct** *(Alternative LLM)* | Evaluated | FP16 | Supported | Supported | Supported | Snapdragon X Elite | INT4 | **EVALUATED ALTERNATIVE** | 3.8B parameters exceeds target low-RAM budget |

---

## Status Definitions

- **SUPPORTED**: Model is tested and fully operational on the active platform.
- **PREPARATION COMPLETE**: Model conversion, export pipeline, quantization experiments, and Qualcomm AI Hub submission scripts are implemented and verified; waiting on target physical hardware.
- **EXPERIMENTAL**: Work in progress, partial functionality, or early prototyping.
- **EVALUATED ALTERNATIVE**: Model analyzed as a candidate alternative; specifications cataloged.
- **TARGET HARDWARE REQUIRED**: Compilation artifact or runtime requires physical Qualcomm Snapdragon / Hexagon NPU hardware.

---

## Qualcomm AI Hub Model Profiles

### 1. Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- **Architecture**: 6-layer Transformer, 384 hidden dimension, 12 attention heads.
- **Input Tensors**:
  - `input_ids`: `int64[batch_size, sequence_length]`
  - `attention_mask`: `int64[batch_size, sequence_length]`
  - `token_type_ids`: `int64[batch_size, sequence_length]`
- **Output Tensors**:
  - `sentence_embedding`: `float32[batch_size, 384]` (normalized)
- **Quantization Strategy**:
  - Dynamic INT8 quantization (`onnxruntime.quantization.quantize_dynamic`)
  - Target: Qualcomm AI Hub INT8 QNN context binary.

### 2. Generative LLM: `Qwen/Qwen2.5-0.5B-Instruct`
- **Architecture**: 24-layer Decoder-only Transformer, 896 hidden dimension, 14 query heads, 2 key-value heads (GQA), tie word embeddings.
- **Input Tensors**:
  - `input_ids`: `int64[1, sequence_length]`
  - `attention_mask`: `int64[1, total_sequence_length]`
  - `past_key_values`: KV-cache per layer `float32[1, num_heads, kv_length, head_dim]`
- **Output Tensors**:
  - `logits`: `float32[1, vocab_size]`
  - `present_key_values`: updated KV-cache
- **Quantization Strategy**:
  - Qualcomm AI Hub W4A16 / INT4 block-wise quantization for Hexagon NPU.
  - Reduces parameter size from ~1.98 GB (FP32) to ~350 MB (INT4), ideal for devices with 8 GB to 16 GB shared system memory.
