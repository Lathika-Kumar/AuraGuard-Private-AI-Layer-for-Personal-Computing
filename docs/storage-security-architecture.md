# AuraGuard Storage Security Architecture (Phase 5)

This document details the local data storage flow, sensitive data categories, and the cryptographic architecture implemented in AuraGuard Phase 5 to provide authenticated encryption at rest without cloud dependencies or external key servers.

---

## 1. Storage Inventory & Data Flow

AuraGuard operates as an entirely local AI layer for personal computing. Prior to Phase 5, all local persistence was unencrypted at rest:

```text
User PDF Uploads ─────> data/documents/ (PDF files)
                             │
                             ▼
Text Extraction ──────> Page-aware chunking
                             │
                             ├───> Text Chunks ─────> SQLite (data/auraguard.db)
                             │                            [document_chunks.text]
                             ▼
Neural Embedder ──────> 384-d float32 vectors ───> FAISS Index (data/index/faiss.index)
                                                ───> SQLite [document_chunks.embedding]

User / ReMind ────────> Memories ───────────────> SQLite (data/auraguard.db)
                                                      [memories.content]
                                                ───> Memory FAISS (data/index/memory_faiss.index)
```

### Sensitive Data Classification

| Data Category | Storage Location | Sensitivity | Threat Addressed | Phase 5 Protection |
| :--- | :--- | :--- | :--- | :--- |
| **ReMind Memory Content** | SQLite `memories.content` | **CRITICAL** | Personal facts, preferences, credentials, private notes exposed if device or disk is stolen. | **AES-256-GCM** authenticated encryption at rest. |
| **Document Chunk Text** | SQLite `document_chunks.text` | **CRITICAL** | Confidential PDF extracts, financial/medical data exposed in plaintext DB. | **AES-256-GCM** authenticated encryption at rest. |
| **FAISS Vector Index** | `data/index/faiss.index` | **HIGH** | Dense vectors can be inverted or probed for semantic similarity even if text is encrypted. | **AES-256-GCM** envelope encryption at rest. |
| **Privacy Audit Logs** | SQLite `privacy_events` | **MEDIUM** | Event metadata may reveal user activity patterns or entity types. | Local access restrictions; sensitive entities scrubbed. |
| **Document Metadata** | SQLite `documents` | **LOW** | Filename, hash, mime type, page count. | Plaintext preserved for filesystem matching & indexing speed. |

---

## 2. Key Management Architecture

AuraGuard uses a two-tier key management architecture rooted in the local operating system:

```text
┌────────────────────────────────────────────────────────┐
│                   Operating System                     │
│               Windows DPAPI (CryptProtectData)         │
│          (Tied to local Windows user credentials)      │
└──────────────────────────┬─────────────────────────────┘
                           │
                 Protects / Unprotects
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               Master Encryption Key                    │
│                  (256-bit AES Key)                     │
│       Persisted encrypted at: data/.master_key.dpapi   │
│         NEVER stored or logged in plaintext            │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             EncryptionService (AES-256-GCM)            │
│       - 96-bit random IV / nonce per encryption        │
│       - 128-bit authentication tag                     │
│       - Ciphertext format: "AG1$<nonce_b64>$<ct_b64>"   │
└────────────────────────────────────────────────────────┘
```

### Key Security Guarantees
1. **No Cloud Keys**: Keys are generated locally using cryptographic randomness (`os.urandom(32)`).
2. **Hardware/User Tied**: On Windows, Windows DPAPI (`CryptProtectData`) encrypts the master key using keys derived from the user's Windows login credentials and system-level secrets. An attacker who copies the disk or database cannot decrypt the key from another user account or machine.
3. **Fail-Safe Integrity**: AES-256-GCM includes a 16-byte authentication tag. Any tampering, truncation, or bit-flip in ciphertext causes instant decryption failure.

---

## 3. Data Protection Lifecycle

### A. Document Ingestion
1. PDF is extracted and chunked.
2. Embedding vector is computed from plaintext chunk text.
3. Vector is stored in the FAISS index.
4. **Before database write**, `EncryptionService.encrypt(chunk_text)` transforms plaintext into authenticated ciphertext (`AG1$...`).
5. Only ciphertext is written to `document_chunks.text`.

### B. Retrieval & Grounding
1. User query is embedded into a vector.
2. FAISS index returns nearest `vector_id`s.
3. SQLite is queried for chunk records by `chunk_id`.
4. `EncryptionService.decrypt(row["text"])` decrypts the chunk in memory.
5. Plaintext is verified, formatted, and passed to LLM context assembly.
6. Ciphertext is never exposed to the LLM or frontend.

### C. ReMind Memory Storage & Search
1. When a memory is created, it is embedded for vector search.
2. Plaintext `content` is encrypted with AES-256-GCM before writing to the `memories` table.
3. During search, memory records are decrypted on-the-fly and passed through the Privacy Engine.

---

## 4. FAISS Index Protection: Trade-off Evaluation

We evaluated two architectural approaches for FAISS index protection:

* **Approach A: File-at-Rest Envelope Encryption** (Selected):
  - When saving the index to disk, the entire index binary is encrypted with AES-256-GCM and written to disk.
  - Upon startup or index reload, the encrypted binary is authenticated and decrypted in-memory before loading into FAISS.
  - *Advantage*: Preserves sub-millisecond C++ SIMD search performance while preventing cold-disk semantic extraction. Zero architectural changes to FAISS search algorithms.
* **Approach B: Per-Vector Encryption**:
  - Encrypting individual vector floats prevents FAISS L2/InnerProduct distance calculations without homomorphic encryption, which adds 1,000x latency overhead.
  - *Conclusion*: Unviable for real-time edge computing.

---

## 5. Non-Destructive Database Migration

To preserve data for existing users who already have unencrypted databases:
- AuraGuard inspects existing `document_chunks` and `memories` records during `init_db()`.
- Plaintext records (which lack the `AG1$` prefix) are read, encrypted in a single transaction, verified with round-trip decryption, and committed.
- If any record fails verification, the transaction rolls back cleanly with zero data loss.
