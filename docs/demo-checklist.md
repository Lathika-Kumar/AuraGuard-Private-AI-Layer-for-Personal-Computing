# AuraGuard — Competition Demonstration Checklist

This checklist prepares the presenter for a flawless 3–5 minute competition presentation of AuraGuard.

---

## Pre-Flight Verification
* [ ] Run `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` to ensure all subsystems report `[PASS]`.
* [ ] Launch AuraGuard via `powershell -ExecutionPolicy Bypass -File scripts\start.ps1`.
* [ ] Open browser to `http://localhost:5173`.

---

## 11-Point Competition Demonstration Checklist

### 1. Hardware Dashboard
* [ ] Navigate to **Dashboard**.
* [ ] Point to **AI Hardware** card showing verified host CPU, architecture, RAM, and clean fallback status.
* [ ] Point to **Model Dashboard** showing INT8 embedding precision and on-device runtime.

### 2. Real Document Ingestion
* [ ] Navigate to **Documents** tab.
* [ ] Drag and drop a real PDF (e.g. project brief, technical document).
* [ ] Show that the upload happens strictly on `localhost` with zero external cloud round-trips.

### 3. Local Neural Indexing
* [ ] Point out real-time chunking (page-aware) and dense embedding generation via `all-MiniLM-L6-v2`.
* [ ] Note that chunks are stored with AES-256-GCM encryption in SQLite.

### 4. RAG Question Submission
* [ ] Navigate to **Ask** tab.
* [ ] Submit a question grounded in the uploaded document.

### 5. Source Transparency & Attribution
* [ ] Highlight the returned answer citation card.
* [ ] Point out the exact document filename and page number citation (e.g. `sample.pdf - Page 2`).

### 6. ReMind Memory Creation & Explicit Approval
* [ ] Navigate to **ReMind** tab.
* [ ] Click **+ Add Memory** and type a personal preference (e.g. *"I prefer concise technical answers with bullet points."*).
* [ ] Point to the **Memory Storage Review & Approval** modal showing privacy classification, importance score, storage encryption format, and explicit user confirmation checkbox.

### 7. Encrypted Storage Verification
* [ ] Navigate to **Privacy Center**.
* [ ] Point to the live **Security Dashboard** showing:
  * Storage Encryption: `AES-256-GCM`
  * Key Protection: `Windows DPAPI`
  * Local AI: `Enabled`
  * Cloud Inference: `Disabled`
  * Live encrypted document and memory counts.

### 8. Privacy Block Action
* [ ] In the **Live Privacy Inspector** on the Privacy Center page, paste a test credential string (e.g. `sk-proj-123456789012345678901234`).
* [ ] Click **Analyze Text**.
* [ ] Point out that Checkpoint 1 flags `API_KEY` and returns action `BLOCK`.

### 9. On-Device AI Pipeline Flow Visualization
* [ ] Return to **Ask** tab.
* [ ] Point out the interactive 8-stage visualizer:
  `User Query → Privacy Check → Memory Retrieval → Document Retrieval → Context Filtering → Local AI → Output Guard → Answer`.
* [ ] Highlight the live millisecond latency metrics on each stage.

### 10. Snapdragon & QNN Status Transparency
* [ ] Direct attention to the **Live NPU Status** badge on Dashboard.
* [ ] Highlight that the system honestly distinguishes the 5 runtime states (`NOT AVAILABLE`, `AVAILABLE`, `PROVIDER LOADED`, `MODEL LOADED`, `INFERENCE VERIFIED`) without marketing exaggerations.

### 11. Empirical Benchmark Dashboard
* [ ] View the **Empirical Benchmark Dashboard** on the Dashboard page.
* [ ] Show the comparative table with measured Intel baseline and unverified platforms honestly marked as *Not measured*.
