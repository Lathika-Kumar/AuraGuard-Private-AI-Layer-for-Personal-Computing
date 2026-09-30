# AuraGuard — Privacy and Security Architecture

## 1. Zero Cloud Telemetry & Data Isolation
AuraGuard is engineered with a strict boundary:
* **Inference Endpoint**: `http://127.0.0.1:8000`
* **Cloud Dependency**: NONE. No API keys, no analytics beacons, no telemetry reporting.
* **Network Sockets**: Binds exclusively to local loopback interface (`127.0.0.1`).

---

## 2. Authenticated Storage Encryption (AES-256-GCM)
* **Cipher**: AES-256 in Galois/Counter Mode (GCM).
* **Parameters**: 256-bit key length, 96-bit cryptographically random IV per record, 128-bit authentication tag.
* **Protected Entities**:
  * `document_chunks.text` (sensitive user document excerpts)
  * `memories.content` (private conversational facts and notes)
  * `faiss.index` / `memory_faiss.index` (vector representations of user content)
* **Ciphertext Format**: Prefixed with `AG1$` followed by base64-encoded `IV (12 bytes) + Tag (16 bytes) + Ciphertext`.
* **Integrity Guarantee**: Tampering with a single bit of ciphertext triggers immediate GMAC authentication failure, preventing chosen-ciphertext attacks.

---

## 3. Key Management via Windows DPAPI
* The master 256-bit encryption key is managed by `KeyManager`.
* On Windows, the key is encrypted using `CryptProtectData` with current user scope (`CRYPTPROTECT_UI_FORBIDDEN`).
* The resulting ciphertext blob is persisted in `.key_store`.
* **No Plaintext Key**: The raw key is never written to disk, never placed in environment files, and never logged.

---

## 4. Multi-Checkpoint Privacy Engine

```text
[Incoming Query / Memory Candidate]
               │
               ▼
   [Checkpoint 1: Input Guard]
   Scans for: API keys, Private keys, Passwords, Tokens
   Action: Reject with HTTP 422
               │
               ▼ (Passed)
      [Context Synthesis]
               │
               ▼
   [Checkpoint 2: Context Neutralizer]
   Scans for: Prompt injection patterns
   Action: Neutralize with [Adversarial directive stripped]
               │
               ▼ (Sanitized)
         [Local LLM]
               │
               ▼
   [Checkpoint 3: Output Guard]
   Scans for: Residual PII, credentials
   Action: Redact to [REDACTED_EMAIL], [REDACTED_PHONE]
               │
               ▼
       [Render to User]
```

---

## 5. Security Dashboard Transparency
The Privacy Center UI displays live, un-mocked security status retrieved directly from the backend:
* **Storage Encryption**: AES-256-GCM
* **Key Protection**: Windows DPAPI
* **Local AI**: Enabled
* **Cloud Inference**: Disabled
* **Privacy Events**: Live count from `privacy_events` table
* **Blocked Requests**: Live count from `privacy_events WHERE action='BLOCK'`
* **Encrypted Memories**: Live count from `memories` table
* **Encrypted Documents**: Live count from `documents` table
