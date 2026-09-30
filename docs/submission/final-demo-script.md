# AuraGuard: 3-Minute Competition Demo Script

**Total Target Duration**: 3 minutes (180 seconds)  
**Presenter**: Pair / Lead Engineer  
**Live UI**: AuraGuard Dashboard running at `http://localhost:5173`

---

### [0:00 - 0:20] 1. The Problem
> *"Modern AI features promise personal computing assistance, but they do it by streaming your private notes, work documents, and sensitive context to the cloud. Once your data leaves your device, you lose control over privacy, data retention, and security.*
>
> *Today we present **AuraGuard**: a truly private AI layer for personal computing that keeps your documents, your memory, and your AI 100% on your device."*

---

### [0:20 - 0:40] 2. AuraGuard Architecture & Dashboard
> *(Action: Display Dashboard at `http://localhost:5173`)*
>
> *"Here on the AuraGuard Dashboard, judges can immediately see our 4-quadrant system state:*
> 1. *Runtime: Local ONNX and PyTorch engines running on 127.0.0.1 with zero cloud telemetry.*
> 2. *Privacy: AES-256-GCM encryption with Windows DPAPI key protection.*
> 3. *Knowledge: Zero documents or memories populated out of the box—no fake data.*
> 4. *Performance: Live baseline measurements on this host."*

---

### [0:40 - 1:05] 3. Real Document Ingestion
> *(Action: Navigate to 'Documents' page. Upload a real sample PDF e.g. `medical_notes.pdf` or `financial_summary.pdf`)*
>
> *"Notice the empty state clearly communicates no documents are indexed. Now I will upload a real PDF.*
>
> *AuraGuard parses the PDF locally, extracts text with exact page numbers, runs our dynamic INT8 quantized embedding model, and builds a FAISS FlatL2 vector index. Notice the table updates in real time with filename, exact chunk count, and cryptographic index status."*

---

### [0:05 - 1:30] 4. Local RAG with Strict Grounding
> *(Action: Navigate to 'Ask' page. Submit query: 'What was the recommended dosage?' or relevant query)*
>
> *"When we ask a question, our local RAG pipeline queries FAISS, retrieves the top semantic chunks, and generates a grounded response using our local Qwen2.5-0.5B model.*
>
> *Look at the response card: it explicitly indicates 'Runtime: CPUExecutionProvider' on this Intel development machine. Every statement is strictly grounded with exact source and page citations. If a question is outside the document context, it refuses to hallucinate."*

---

### [1:30 - 1:55] 5. ReMind: User-Controlled Episodic Memory
> *(Action: Navigate to 'ReMind' page. Save a memory: 'User prefers technical documentation in concise bullet format.')*
>
> *"Unlike cloud assistants that silently record user habits into opaque profiles, AuraGuard introduces **ReMind**.*
>
> *Every candidate memory is inspected for privacy, requires explicit user consent, and is encrypted with AES-256-GCM before indexing. When deleted, it is purged synchronously from both SQLite and FAISS."*

---

### [1:55 - 2:15] 6. Privacy Protection in Action
> *(Action: Navigate to 'Privacy Center'. Enter in the Live Inspector: 'My AWS secret key is AKIAIOSFODNN7EXAMPLE')*
>
> *"What happens if a user accidentally inputs a secret or an adversarial prompt?*
>
> *Our pre-ingestion Privacy Engine intercepts the credential instantly. The decision is marked **BLOCKED**, classification shows **API Credential**, and the secret is prevented from ever reaching the vector store or prompt context. Note that the secret itself is never written to disk or logs."*

---

### [2:15 - 2:30] 7. Cryptographic Zero-Knowledge Storage
> *(Action: Show the Hardware/Security badges: 'AES-256-GCM' and 'Windows DPAPI')*
>
> *"All indexed chunks, metadata, and memory embeddings are encrypted with AES-256-GCM. The encryption key itself is protected by Windows DPAPI, binding security directly to the authenticated Windows user session. Even if an attacker copies the SQLite database file, the contents remain unreadable."*

---

### [2:30 - 2:45] 8. Hardware-Aware Runtime & Snapdragon Readiness
> *(Action: Highlight Hardware Status quadrant on Dashboard)*
>
> *"AuraGuard is hardware-aware. On this Intel Core i5 laptop, our hardware layer accurately detects the x86 architecture and runs on CPUExecutionProvider.*
>
> *For Snapdragon X Series HP PCs, AuraGuard provides an automated deployment path utilizing Qualcomm AI Hub and the ONNX Runtime QNN Execution Provider to harness the 45 TOPS Hexagon NPU. Our software architecture includes automated QNN fallback so execution remains reliable across devices."*

---

### [2:45 - 3:00] 9. Closing & Verifiable Deletion
> *(Action: Click 'Delete Document' on Documents page and 'Clear Workspace')*
>
> *"Finally, privacy means complete user ownership. With one click, we purge all documents and memories from disk, database, and FAISS. The system returns to zero footprint.*
>
> *AuraGuard delivers the future of personal computing: powerful, local, and genuinely private. Thank you."*
