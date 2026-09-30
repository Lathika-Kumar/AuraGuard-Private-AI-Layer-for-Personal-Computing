# AuraGuard — Competition Demo Script (3–5 Minutes)

**Target Audience:** Competition Judges & Technical Reviewers  
**Platform Demonstrated:** Windows 11 On-Device AI Stack  
**Target Accelerator:** Qualcomm Snapdragon X Elite (Hexagon NPU) with Verified CPU Fallback  

---

## ⏱️ Timeline & Walkthrough

### 0:00 – 0:30 | The Problem & Vision
* **Presenter:**
  > "Modern personal AI brings immense utility to our everyday computing, but today’s commercial solutions force users into an unacceptable trade-off: sending their most private personal thoughts, financial records, confidential PDFs, and credentials to third-party cloud servers.
  > 
  > AuraGuard solves this by providing a complete, sovereign, on-device AI layer for personal computing. With AuraGuard, your documents, memories, semantic vectors, and neural reasoning never leave your PC."

---

### 0:30 – 1:15 | Local Ingestion & Vector Indexing
* **Action:**
  1. Open AuraGuard dashboard (`http://localhost:5173`).
  2. Navigate to **Documents** tab.
  3. Upload a real personal PDF (e.g., `sample_project_brief.pdf`).
* **Visual Highlights:**
  * Client-side ingestion without cloud transit.
  * Real-time PDF parsing, text extraction, page-aware chunking.
  * On-device neural embeddings computed via `all-MiniLM-L6-v2` ONNX Runtime.
  * Encrypted storage: Document chunks encrypted via **AES-256-GCM** before SQLite persistence; FAISS vector index saved in an encrypted file envelope protected by **Windows DPAPI**.

---

### 1:15 – 2:00 | Grounded Local RAG & Source Attribution
* **Action:**
  1. Navigate to **Ask** tab.
  2. Submit query: *"What are the project deliverables and deadlines outlined in the brief?"*
* **Visual Highlights:**
  * **On-Device AI Pipeline Flow:** Watch the 8-stage interactive visualizer illuminate in real-time:
    `User Query → Privacy Check → Memory Retrieval → Document Retrieval → Context Filtering → Local AI → Output Guard → Answer`.
  * **Strict Source Transparency:** Point out the exact citation cards showing `Document: sample_project_brief.pdf`, `Page: 2`, `Chunk #4`.
  * **Zero Hallucination Guarantee:** The answer cites strictly verified local context.

---

### 2:00 – 2:45 | ReMind: User-Approved Personal Context
* **Action:**
  1. Navigate to **ReMind** tab.
  2. Click **+ Add Memory**. Enter: *"My preferred working style is dark mode with concise bulleted technical answers."*
  3. Notice the real-time privacy scanner inspects the draft.
  4. View the **Memory Storage Review & Approval** modal showing:
     * *Storage:* `AES-256-GCM + Windows DPAPI`
     * *Classification:* `PERSONAL`
     * *Importance:* `85%`
     * *Explicit Approval:* Check the confirmation box and click **Confirm & Store Memory**.
  5. Return to **Ask** tab and query: *"How should I organize the upcoming technical sprint?"*
  6. Point out that AuraGuard combines both Document context and ReMind preference context simultaneously.

---

### 2:45 – 3:30 | Privacy Engine: Three Checkpoint Defense
* **Action:**
  1. Navigate to **Privacy Center**.
  2. In the **Live Privacy Inspector**, enter a sample credential string:
     `"My administrative token is sk-proj-999999999999999999999999 and email is admin@company.com"`
  3. Click **Analyze Text**.
* **Visual Highlights:**
  * Checkpoint 1 flags the high-risk token: `API_KEY` detected.
  * Action displays: `BLOCK`.
  * Point to the live **Privacy Audit Log** showing timestamps, classifications, and sanitized actions with zero raw secret storage.

---

### 3:30 – 4:15 | Hardware Intelligence & CPU/QNN Architecture
* **Action:**
  1. Navigate to **Dashboard**.
  2. Direct the judges' attention to the **AI Hardware** and **Model Dashboard** cards:
     * **Host CPU:** Displays verified host processor brand and architecture.
     * **Execution Provider:** Dynamically set to `CPUExecutionProvider` on Intel workstation with seamless readiness for `QNNExecutionProvider` on Snapdragon X Elite.
     * **Snapdragon Detection:** Shows `Detected` or `Not detected` based on real silicon introspection (zero hardcoding).
     * **Encrypted Storage Counts:** Live telemetry of encrypted documents and memories.

---

### 4:15 – 5:00 | Competition Summary & Snapdragon Roadmap
* **Presenter:**
  > "AuraGuard provides a verified, production-quality Private AI layer with AES-256-GCM authenticated storage, Windows DPAPI key protection, a 3-checkpoint privacy engine, and neural RAG.
  > 
  > While our current development and benchmark environment runs on an Intel Core i5 with CPU fallback, the entire architecture is built and packaged for Qualcomm Snapdragon X Elite HP PCs. We have quantized our embedding models to INT8, verified ONNX graph integrity, prepared the QNN execution pipeline, and documented the physical deployment path.
  > 
  > AuraGuard proves that personal computing AI can be fast, private, and completely sovereign."
