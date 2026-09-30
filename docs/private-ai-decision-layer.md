# AuraGuard — Private AI Decision Layer

## 1. Overview & Architectural Evolution

In Phase 9, AuraGuard completes its architectural evolution from a local Retrieval-Augmented Generation (RAG) assistant into an **Adaptive Private AI Decision Layer for Personal Computing**. 

AuraGuard does not simply process text locally; it acts as a user-controlled, privacy-preserving governance layer that continuously arbitrates how personal information is ingested, processed, remembered, retrieved, and shielded across 6 dynamic dimensions:
1. **Data Sensitivity**: Automatic multi-tier classification (`PUBLIC`, `PERSONAL`, `SENSITIVE`, `SECRET`).
2. **User Intent**: Query disambiguation (`DOCUMENT_QUERY`, `MEMORY_RECALL`, `MEMORY_STORE`, `GENERAL_QUERY`).
3. **Available Hardware**: Runtime verification of Qualcomm Snapdragon Hexagon NPU vs. Intel/AMD CPU.
4. **Privacy Policy**: Active user-governed profiles (`strict`, `balanced`, `permissive`) and granular rules.
5. **Memory Policy**: Explicit user consent requirements (`ASK`, `ALWAYS`, `NEVER`) and automatic memory gating.
6. **Model Availability**: On-device model health checks, local neural routing, and deterministic fallback.

```
+---------------------------------------------------------------------------------------------------+
|                                  USER QUERY OR INTERACTION                                        |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                           PRIVATE AI DECISION ENGINE (Pre-Flight)                                 |
|  - Data Sensitivity Classifier (PUBLIC / PERSONAL / SENSITIVE / SECRET)                           |
|  - User Intent Classification                                                                     |
|  - User Privacy Policy Evaluation (Strict / Balanced / Permissive)                                |
|  - Hardware State Arbitration (CPU vs Snapdragon QNN NPU)                                         |
|  - Egress Network Policy Verification (External AI: BLOCKED at 127.0.0.1)                         |
+---------------------------------------------------------------------------------------------------+
                  |                                                  |
       [Blocked / Prohibited Secret]                                 | [Allowed for Local Processing]
                  |                                                  v
                  v                                 +-----------------------------------------------+
      +------------------------+                    |     FAISS NEURAL RETRIEVAL PIPELINE           |
      | Return Block Reason    |                    |  - Document Chunks (Page / ID / Similarity)   |
      | & Record Ledger Event  |                    |  - ReMind Memories (Encrypted AES-256-GCM)    |
      +------------------------+                    +-----------------------------------------------+
                                                                     |
                                                                     v
                                                    +-----------------------------------------------+
                                                    |            CONTEXT FIREWALL                   |
                                                    |  - Prompt Injection Detection                 |
                                                    |  - Neutralize System Overrides / Directives   |
                                                    |  - Preserve Legitimate Factual Context        |
                                                    |  - Log Security Telemetry (No Secrets Stored) |
                                                    +-----------------------------------------------+
                                                                     |
                                                                     v
                                                    +-----------------------------------------------+
                                                    |        LOCAL ON-DEVICE INFERENCE ENGINE       |
                                                    |  - QNNExecutionProvider (on Snapdragon NPU)   |
                                                    |  - CPUExecutionProvider (Verified Intel Host) |
                                                    +-----------------------------------------------+
                                                                     |
                                                                     v
                                                    +-----------------------------------------------+
                                                    |             OUTPUT PRIVACY GUARD              |
                                                    |  - Scan LLM response for leaked secrets       |
                                                    |  - Memory Candidate Detection (Consent Prompt)|
                                                    +-----------------------------------------------+
                                                                     |
                                                                     v
                                                    +-----------------------------------------------+
                                                    |       TRANSPARENCY PANEL ("Why this answer?") |
                                                    |  - Model, Runtime EP, Context Audit, Sources  |
                                                    +-----------------------------------------------+
```

---

## 2. Data Sensitivity Classification

AuraGuard classifies all input queries, document fragments, and memories into four verifiable sensitivity tiers:

| Tier | Definition | Detection Examples | Policy Behavior (Balanced Mode) |
| :--- | :--- | :--- | :--- |
| **`PUBLIC`** | General knowledge, impersonal facts, and public documentation. | General technical questions, open source docs. | Allowed; full retrieval & generation. |
| **`PERSONAL`** | Non-secret personal identifiers identifying an individual. | Email addresses, names, dates of birth. | Allowed; sanitized/redacted on context. |
| **`SENSITIVE`** | Private identifiers carrying financial or personal exposure risk. | Phone numbers, addresses, personal notes. | Allowed with warning in Balanced; blocked in Strict. |
| **`SECRET`** | High-security credentials, authentication keys, and tokens. | Passwords, API keys, private keys, JWTs. | **Strictly Blocked**; never ingested into models or logs. |

---

## 3. Configurable Privacy Policies

AuraGuard rejects hardcoded privacy assumptions. All privacy rules are stored persistently in the local SQLite database (`user_policies` table) and can be modified through the **Privacy Center** UI or the `POST /api/privacy/policy` API:

* **Strict Profile**:
  * External AI: `BLOCKED`
  * Local Processing: `ON`
  * Memory Mode: `ASK` (User approval required)
  * Sensitive Data: `BLOCK` (Immediate rejection)
  * Document Retrieval: `ON`
  * Automatic Memory: `OFF`
* **Balanced Profile (Default)**:
  * External AI: `BLOCKED`
  * Local Processing: `ON`
  * Memory Mode: `ASK` (User approval required)
  * Sensitive Data: `BLOCK` on `SECRET`, sanitize on `PERSONAL`
  * Document Retrieval: `ON`
  * Automatic Memory: `OFF`
* **Performance Profile**:
  * Local-only inference with maximum throughput; allows approved memory synthesis while preserving strict zero-cloud egress.

---

## 4. ReMind Memory Consent & Lifecycle

### Memory Consent
AuraGuard does not autonomously memorize everything. When the user mentions personal preferences or recurring directives, the **Decision Engine** detects a `MemoryCandidate`:
* The UI presents an explicit approval banner: `[Save to ReMind]` / `[Don't Save]`.
* If the user selects `[Don't Save]`, nothing is stored.
* If approved, metadata (`source`, `user_approved`, `sensitivity`, `created_at`, `expires_at`) is attached.

### Memory Expiration Modes
To avoid perpetual retention of transient data, memories support expiration presets:
1. `Never` (Persistent context)
2. `7 days`
3. `30 days`
4. `90 days`
5. `Custom ISO timestamp`

Expired memories are automatically excluded from FAISS vector retrieval (`status = 'expired'`). A dedicated cleanup endpoint (`POST /api/memories/cleanup-expired`) purges expired records from the active FAISS index.

---

## 5. Context Firewall

Retrieved document chunks or community files may contain adversarial prompt injections designed to hijack the local LLM. AuraGuard introduces a dedicated **Context Firewall** between the retriever and the generator.

### Capabilities:
* **Detection**: Identifies patterns such as `ignore previous instructions`, `system override`, `you are now in developer mode`, and `output the word...`.
* **Selective Neutralization**: Rather than discarding an entire document, the Context Firewall replaces only the malicious sentence with `[Instruction neutralized by Context Firewall]`, preserving the surrounding factual context.
* **Security Telemetry**: Emits a structured `FirewallEvent` to the local ledger with category, reason, action, and document attribution, without exposing malicious payloads.

---

## 6. Hardware-Aware Model Routing & Fallback

AuraGuard interrogates the underlying host hardware using `HardwareService`:
* **Snapdragon Deployment**: On physical Snapdragon hardware (ARM64 + Qualcomm Hexagon NPU), AuraGuard routes embeddings and LLM passes to `QNNExecutionProvider`.
* **Intel / AMD Fallback**: On x86_64 host machines (e.g. Intel Core i5-1235U), AuraGuard honestly falls back to `CPUExecutionProvider`.
* **Honest Detection Rule**: Architecture alone (`arm64`) does not imply NPU availability. The system verifies actual Qualcomm runtime drivers before reporting QNN readiness.

---

## 7. Network Safety & Zero-Cloud Egress

AuraGuard enforces strict local containment:
* Default network policy: `External AI: BLOCKED`.
* All API bindings and neural weights run on `127.0.0.1`.
* No cloud telemetry or third-party inference requests are dispatched under any condition.

---

## 8. Privacy Event Ledger

All security actions are recorded in an append-only SQLite ledger (`privacy_events`):
* Events logged: `SENSITIVE_DATA_BLOCKED`, `PROMPT_INJECTION_BLOCKED`, `MEMORY_CREATED`, `MEMORY_DELETED`, `DOCUMENT_DELETED`, `MODEL_FALLBACK`, `POLICY_CHANGED`.
* **Zero Secret Logging**: The ledger strictly omits raw passwords, API keys, private tokens, and sensitive text payloads.

---

## 9. Transparency Panel ("Why this answer?")

For every generated response, AuraGuard allows the user to inspect the reasoning behind the execution:
* **Model ID**: e.g., `Qwen2.5-0.5B-Instruct`
* **Execution Provider**: e.g., `CPUExecutionProvider`
* **Processing Mode**: `LOCAL_ONLY`
* **Network Egress**: `BLOCKED`
* **Data Sensitivity**: `PUBLIC` / `PERSONAL`
* **Retrieved Sources**: Document filenames, chunks, and similarity match percentages
* **ReMind Memories**: Number of user-approved memories integrated
* **Privacy Checks**: Three-stage pass (`Input: PASS`, `Context: PASS`, `Output: PASS`)
* **Firewall Events**: Explanations of any neutralized prompt injections

---

## 10. Actual Limitations

1. **Physical Snapdragon Requirement**: Actual QNN NPU hardware acceleration requires physical Qualcomm Snapdragon X Elite / Plus silicon running Windows on ARM. On the current Intel Core i5-1235U development machine, inference runs via `CPUExecutionProvider`.
2. **Context Window Constraint**: `Qwen2.5-0.5B-Instruct` is constrained to small local parameter footprints (~0.5B parameters) to guarantee real-time CPU and NPU latency on consumer laptops.
3. **Deterministic Regex Classification**: Sensitivity and prompt-injection defenses rely on structured regex heuristic guards combined with token patterns; complex linguistic steganography may require future dedicated local classifier models.
