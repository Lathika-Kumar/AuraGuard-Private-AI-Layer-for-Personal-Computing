# AuraGuard: Evidence Index & Claim Verification Matrix

This index maps every technical claim made in the AuraGuard codebase, documentation, and submission materials to its verifiable empirical test, code location, or recorded artifact.

---

| Technical Claim | Implementation & Architecture | Verification Evidence | Current Status |
| :--- | :--- | :--- | :--- |
| **Zero Cloud Egress / 100% Local RAG** | `backend/app/rag/pipeline.py`<br>`backend/app/embeddings/service.py` | `backend/tests/test_rag.py`<br>`backend/tests/test_documents.py`<br>Local socket binding (127.0.0.1) | **VERIFIED** on host |
| **Page-Aware PDF Ingestion & Attribution** | `backend/app/rag/chunking.py`<br>`backend/app/api/routes/documents.py` | `backend/tests/test_chunking.py`<br>`backend/tests/test_documents.py` | **VERIFIED** on host |
| **FAISS Vector Indexing & Search** | `backend/app/rag/retrieval.py` | `backend/tests/test_retrieval.py` (FlatL2 384-d) | **VERIFIED** on host |
| **Dynamic INT8 Embedding Quantization** | `models/embeddings/model_quantized.onnx`<br>`scripts/qualcomm/quantize_embeddings.py` | 74.7% model size reduction (86.2MB → 21.8MB)<br>Cosine similarity: 0.952862 avg<br>100% Top-3 retrieval overlap | **VERIFIED** on host |
| **Local LLM Synthesis** | `backend/app/llm/service.py`<br>Qwen2.5-0.5B-Instruct | `backend/tests/test_llm.py` | **VERIFIED** on host (CPU) |
| **ReMind Episodic Memory Store** | `backend/app/memory/service.py`<br>`backend/app/api/routes/memories.py` | `backend/tests/test_remind.py`<br>Explicit approval requirement verified | **VERIFIED** on host |
| **3-Stage Privacy Guard Engine** | `backend/app/privacy/engine.py`<br>`backend/app/privacy/injection.py` | `backend/tests/test_privacy_engine.py`<br>`backend/tests/test_prompt_injection.py` | **VERIFIED** on host |
| **Prompt Injection & Memory Poisoning Defense** | Regex + entropy detection on queries and candidate memories | `backend/tests/test_prompt_injection.py`<br>`backend/tests/test_privacy_engine.py` | **VERIFIED** on host |
| **AES-256-GCM Storage Encryption** | `backend/app/security/encryption_service.py`<br>Per-record nonces & tag auth | `backend/tests/test_encryption.py`<br>Decryption failure on tampering verified | **VERIFIED** on host |
| **Windows DPAPI Key Protection** | `backend/app/security/key_manager.py`<br>`CryptProtectData` Win32 API | `backend/tests/test_key_manager.py` | **VERIFIED** on host (Windows 11) |
| **Verifiable Data & Memory Deletion** | Synchronous cascade delete in SQLite + FAISS | `backend/tests/test_documents.py`<br>`backend/tests/test_remind.py` | **VERIFIED** on host |
| **Hardware Detection Architecture** | `backend/app/hardware/detection.py` | `backend/tests/test_hardware_detection.py` | **VERIFIED** on host (Intel detected) |
| **QNN Fallback & CPU Execution Provider** | `backend/app/hardware/detection.py`<br>`backend/app/embeddings/service.py` | `backend/tests/test_qualcomm_onnx.py`<br>Simulated QNN missing falls to CPU | **VERIFIED** on host |
| **Measured Intel Baseline Benchmarks** | `scripts/qualcomm/run_full_benchmark.ps1` | `benchmark_results/intel_baseline.json`<br>Embed: 38.32ms, LLM TTFT: 14.2s, RSS: 992MB | **VERIFIED** on host |
| **Snapdragon X Series NPU Acceleration** | Qualcomm AI Hub QNN HTP workflow<br>`scripts/qualcomm/compile_qnn_artifacts.py` | Pending Snapdragon ARM64 hardware | **READY FOR HARDWARE TEST** (Not claimed on Intel) |
| **Qualcomm NPU Physical Inference** | Hexagon HTP execution provider | `scripts/qualcomm/verify_snapdragon.ps1` | **PENDING HARDWARE VALIDATION** |

---

### Integrity Statement
No benchmark numbers have been fabricated or simulated. Snapdragon NPU metrics will only be recorded once physical testing is performed on Qualcomm Snapdragon X Elite or X Plus hardware.
