# AuraGuard Context Architecture

## Overview

AuraGuard integrates **Documents**, **ReMind Local Context**, and the **Privacy Engine** into a unified, on-device intelligence pipeline:

```text
                         AURAGUARD
                             │
             ┌───────────────┼───────────────┐
             │               │               │
             ▼               ▼               ▼
        Documents         ReMind          Privacy
             │               │             Engine
             │               │               │
             ▼               ▼               ▼
          RAG         Local Context     Sensitive Data
             │         & Memory          Detection
             └───────────────┬───────────────┘
                             ▼
                    Private AI Layer
                             │
                             ▼
                     Local AI Runtime
                             │
                     CPU / QNN-ready
```

---

## Namespaces & Vector Store Separation

To prevent collisions and enable clean lifecycle guarantees, AuraGuard maintains **logically isolated FAISS namespaces**:

1. **Document Namespace**:
   - Index: `data/index/faiss.index`
   - Metadata: `data/index/index_meta.json`
   - Mapping Table: `faiss_mappings (vector_id -> chunk_id)`
2. **ReMind Memory Namespace**:
   - Index: `data/index/memory_faiss.index`
   - Metadata: `data/index/memory_index_meta.json`
   - Mapping Table: `memory_faiss_mappings (vector_id -> memory_id)`

Rebuilding or clearing document vectors has zero impact on user memories, and deleting memories has zero impact on indexed documents.

---

## Context Merging & Provenance Attribution

When a query is received:
1. `RetrievalService` retrieves the top-$k$ relevant document chunks based on neural embeddings and minimum score threshold.
2. `RemindService` retrieves the top-$k$ relevant active user memories based on neural embeddings and importance weighting.
3. The **Context Merger** constructs a partitioned prompt:
   - `--- LOCAL DOCUMENTS CONTEXT ---` (Labeled with filename and page number)
   - `--- REMIND LOCAL MEMORY CONTEXT ---` (Labeled with memory type and importance score)
4. The **Privacy Engine** scrubs the merged context of any personal/sensitive identifiers per policy mode.
5. The **Local Language Model** generates a grounded answer.
6. The final API response attributes evidence to its precise provenance:
   - `sources`: Document chunks with page numbers.
   - `memories_used`: ReMind entries with memory types and importance.
   - `source_types`: `["document"]`, `["memory"]`, or `["document", "memory"]`.

---

## AI Runtime & Hardware Layer Abstraction

All vector embedding and generative reasoning execute through the modular hardware provider abstraction:
- **Embeddings**: FastEmbed ONNX Runtime running `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional).
- **LLM**: Local Transformers running `Qwen2.5-0.5B-Instruct` (FP32).
- **Execution Provider**: Auto-detects Qualcomm Hexagon NPU / QNN Execution Provider on Snapdragon platforms with automatic, graceful CPU fallback.
