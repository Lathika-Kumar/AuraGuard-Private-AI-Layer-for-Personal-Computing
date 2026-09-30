# AuraGuard — Phase 9 Architecture: Private AI Decision Layer

## 1. Executive Overview

Phase 9 evolves AuraGuard from a standalone local Retrieval-Augmented Generation (RAG) system into an **Adaptive Private AI Decision Layer** for personal computing.

Rather than blindly processing prompts, the Private AI Decision Layer acts as an intelligent, user-controlled runtime governor that dynamically decides **how personal information should be processed, remembered, retrieved, and protected** across six dimensions:
1. **Data Sensitivity**: Classifying input and contextual information into `PUBLIC`, `PERSONAL`, `SENSITIVE`, and `SECRET`.
2. **User Intent**: Discerning between factual document inquiries, personal memory requests, operational commands, and configuration changes.
3. **Available Hardware**: Dynamically routing between Qualcomm Hexagon NPU (`QNNExecutionProvider`) on verified Snapdragon Copilot+ hardware and CPU fallback (`CPUExecutionProvider`) on x86/Intel hosts.
4. **User Privacy Policy**: Enforcing user-configured policy modes (`Strict`, `Balanced`, `Performance`) with granular controls for external network egress, sensitive entity handling, and document retrieval.
5. **Memory Policy**: Safeguarding episodic memory through user-controlled consent (Ask vs. Auto), explicit lifecycle management, and deterministic expiration policies (`Never`, `7 days`, `30 days`, `90 days`, `Custom`).
6. **Model Availability & Fallback**: Selecting local models safely, maintaining local-only execution without ever silently delegating to third-party cloud APIs.

---

## 2. End-to-End System Topology

```text
                           [ User Query / Document Input ]
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │      PrivateAIDecisionService         │
                      │  - Reads User Privacy Policy          │
                      │  - Classifies Data Sensitivity        │
                      │  - Resolves Hardware & Execution EP   │
                      │  - Determines Memory & Retrieval Mode │
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │       Input Privacy Guard             │
                      │  - Scans for SECRET / High Entropy    │
                      │  - Decision: ALLOW / BLOCK / WARN     │
                      │  - Logs event to Privacy Ledger       │
                      └───────────────────┬───────────────────┘
                                          │ (If Allowed)
                         ┌────────────────┴────────────────┐
                         ▼                                 ▼
            ┌─────────────────────────┐       ┌─────────────────────────┐
            │   Document Retrieval    │       │     ReMind Retrieval    │
            │   - FAISS Semantic Search│      │   - Active, Unexpired   │
            │   - Sensitivity Tagging │       │   - User Approved Only  │
            └────────────┬────────────┘       └────────────┬────────────┘
                         │                                 │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │            Context Firewall           │
                      │  - Detects Prompt Injections          │
                      │  - Neutralizes Malicious Directives   │
                      │  - Preserves Valid Factual Content    │
                      │  - Records Explanations & Sources     │
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    Hardware-Aware Model Executor      │
                      │  - Primary: QNNExecutionProvider      │
                      │    (Qualcomm Hexagon NPU)             │
                      │  - Fallback: CPUExecutionProvider     │
                      │    (Intel / AMD x86_64 host)          │
                      │  - Zero Cloud Egress Guard            │
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │       Output Privacy Guard            │
                      │  - Scans Generated Text               │
                      │  - Verifies Grounding & Citations     │
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │          Attributed Answer            │
                      │  + "Why this answer?" Transparency    │
                      │    (Model, EP, Sources, Memory,       │
                      │     Privacy checks, Processing mode)  │
                      └───────────────────────────────────────┘
```

---

## 3. Core Subsystems & Components

### 3.1 PrivateAIDecisionService (`backend/app/services/decision_service.py`)
- Central orchestration component evaluating incoming requests prior to any neural embedding or vector indexing.
- Inputs: `query`, `user_policy`, `hardware_status`, `memory_status`.
- Output: `DecisionResult`:
  ```json
  {
    "processing_mode": "LOCAL_ONLY",
    "privacy_mode": "balanced",
    "sensitivity": "PERSONAL",
    "memory_allowed": true,
    "retrieval_allowed": true,
    "sensitive_data_detected": false,
    "execution_provider": "CPUExecutionProvider",
    "fallback_active": false,
    "network_policy": "BLOCKED",
    "reason": "Local processing policy selected; CPUExecutionProvider active."
  }
  ```

### 3.2 Data Sensitivity Classification
- **`PUBLIC`**: Generic educational or publicly known information with zero personal identifiers.
- **`PERSONAL`**: Everyday personal notes, schedule reminders, work tasks, and non-confidential preferences.
- **`SENSITIVE`**: Personally Identifiable Information (PII) including phone numbers, personal email addresses, home addresses, dates of birth, and SSNs.
- **`SECRET`**: High-entropy API keys, private cryptographic keys, passwords, bank account details, and payment cards.

### 3.3 User Privacy Policy (`user_policies` SQLite Table)
Stores user-configurable security controls:
- `local_processing`: `"ON"` (Always local execution)
- `external_ai`: `"BLOCKED"` (Strict prohibition of third-party cloud routing)
- `memory_mode`: `"ASK"` | `"AUTO"` | `"OFF"`
- `sensitive_data_action`: `"BLOCK"` | `"WARN"` | `"ALLOW"`
- `document_retrieval`: `"ON"` | `"OFF"`
- `privacy_mode`: `"strict"` | `"balanced"` | `"performance"`

### 3.4 Context Firewall (`backend/app/services/context_firewall.py`)
- Operates on the concatenated text of retrieved document chunks and memories *before* prompt delivery to the LLM.
- Analyzes candidate text for adversarial patterns (`ignore previous instructions`, `system override`, `you are now in developer mode`).
- Neutralizes prompt injections at the sentence/chunk level without discarding the entire document corpus.
- Generates transparent security explanations: Reason, Action Taken, and Source Attribution.

### 3.5 ReMind Memory Lifecycle & Expiration
- Explicit consent model: Candidate memories require user confirmation unless explicitly configured otherwise.
- Expiration tracking: Supports `never`, `7_days`, `30_days`, `90_days`, or custom ISO timestamps.
- Synchronous cleanup: `cleanup_expired_memories()` marks expired rows and updates FAISS indices so expired items are strictly excluded from semantic search.

### 3.6 Hardware Routing & Transparency Engine
- Probes `HardwareService` for real hardware capabilities:
  - If Qualcomm NPU driver + QNN EP are verified: select `QNNExecutionProvider`.
  - Otherwise: gracefully fall back to `CPUExecutionProvider` and explain why.
- Returns comprehensive "Why this answer?" telemetry for every generated response.
