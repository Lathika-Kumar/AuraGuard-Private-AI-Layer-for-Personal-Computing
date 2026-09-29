# ReMind — Private Local Context & Memory Engine

## What is ReMind?

**ReMind** is AuraGuard's on-device personal context and memory engine. It allows AuraGuard to maintain persistent, user-approved contextual memory locally without sending any data over external networks.

ReMind is explicitly **NOT a surveillance system**:
- It does **NOT** capture continuous desktop screen recordings.
- It does **NOT** log keystrokes or background application windows.
- It does **NOT** continuously record microphone or ambient audio.
- It does **NOT** harvest user activity without explicit consent.

ReMind stores information **only when explicitly approved or supplied by the user**.

---

## Memory Types

ReMind organizes local context into six typed categories:

1. **FACT**: Verified personal or environmental facts (e.g., project tech stack, device architecture).
2. **PREFERENCE**: User instructions regarding output style, reasoning length, or formatting preferences (e.g., "Prefer concise explanations with bullet points").
3. **TASK**: Active objectives or actionable todos (e.g., "Prepare benchmark suite for testing").
4. **GOAL**: High-level strategic targets or project milestones (e.g., "Ready AuraGuard for Snapdragon challenge").
5. **NOTE**: Unstructured observations, research findings, or notes.
6. **CONTEXT**: System environment configuration and working assumptions.

---

## Architecture & Lifecycle

```text
User Interaction
       │
Candidate Memory Content
       │
[Privacy Check] ───► Credentials or Secrets? ──► REJECT / BLOCK
       │
User Approval
       │
Embedding (On-Device all-MiniLM-L6-v2)
       │
SQLite + Memory FAISS Index (Isolated Namespace)
       │
Semantic Retrieval during Question Answering
```

### Supported Lifecycle Stages
- **Create**: Scans content with Privacy Engine. Rejects credentials/secrets. Computes neural embedding and indexes into FAISS memory index.
- **Read**: Lists or fetches memories with filters for type, status, and search keywords. Automatically detects expired items.
- **Update**: Modifies content or metadata. Automatically recalculates embeddings and rebuilds the vector index when content changes.
- **Archive**: Sets memory status to `archived`. Preserves memory locally while excluding it from active RAG retrieval.
- **Expire**: Supports optional `expires_at` ISO-8601 timestamps. Past memories are automatically marked `expired` and excluded from retrieval.
- **Delete Guarantee**: Permanently removes memory from SQLite and refreshes the FAISS index so that deleted memories cannot be retrieved.

---

## Semantic Retrieval & RAG Context Merger

During question answering, ReMind executes semantic retrieval alongside document search:

```text
User Query
    │
    ├── Document Retrieval (FAISS document namespace)
    │
    └── Memory Retrieval (FAISS memory namespace)
             │
             ▼
       Context Merger
             │
    [Context Provenance]
    • Document: spec.pdf (Page 2)
    • ReMind: PREFERENCE (Importance: 90%)
             │
             ▼
      Privacy Filtering
             │
          Local LLM
```

Answers explicitly indicate whether the grounded evidence came from **Documents**, **Memories**, or **Both**.
