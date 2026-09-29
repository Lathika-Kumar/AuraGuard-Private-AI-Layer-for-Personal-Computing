# Storage Encryption at Rest Evaluation (Phase 4 / Phase 5 Roadmapping)

This document investigates the Phase 3 recommendation for encrypted local storage for AuraGuard's SQLite databases, FAISS vector indices, and document chunks.

---

## 1. Threat Model & Current Storage Security

### Current Storage Architecture
- **SQLite Database** (`auraguard.db`): Stores document metadata, chunk text, ReMind memories, and privacy audit logs in standard SQLite format.
- **FAISS Vector Index** (`faiss_index.bin`): Stores 384-dimensional dense vectors representing chunk embeddings.
- **File System Permissions**: Constrained to the user's local application data directory.
- **Network Boundaries**: 100% localhost-bound; no cloud syncing, telemetry, or external database connections.

### Threat Model
- **Threat 1: Unauthorized local account access**: A secondary user on a shared OS workstation browsing the filesystem could read the plaintext `.db` or FAISS vector files.
- **Threat 2: Offline disk theft**: An adversary stealing a physical laptop disk could inspect document chunks and memories if full-disk encryption (BitLocker / LUKS) is disabled.
- **Out of Scope**: Compromise of the active running process memory (RAM scraping with admin privileges) cannot be prevented by at-rest encryption alone.

---

## 2. Technical Evaluation of SQLCipher & Alternatives

### A. SQLCipher
- **Mechanism**: Page-level 256-bit AES encryption of the SQLite database.
- **Python Integration**: `pysqlcipher3` or `sqlcipher3`.
- **Evaluation on Current Development Host**:
  1. `sqlcipher3` and `pysqlcipher3` require compiling against OpenSSL C libraries or bundling pre-built C DLLs.
  2. On Windows x86_64, pip install often fails unless Visual C++ build tools and OpenSSL development headers are installed.
  3. On Windows ARM64 (Snapdragon X Elite), pre-compiled binary wheels for `sqlcipher3` are scarce, risking packaging failures during deployment on Snapdragon laptops.
- **Risk Assessment**: High risk of runtime installation breakage and migration failure on Windows platforms.

### B. Application-Layer Symmetric Encryption (Recommended Path)
- **Mechanism**: AES-256-GCM / ChaCha20-Poly1305 via Python's standard `cryptography` library (`Fernet` or `AESGCM`).
- **Target Fields**: Only sensitive plaintext payload columns (`chunk_text`, `memory_content`, `original_value` in audit logs) are encrypted before insertion into SQLite; index metadata remains queryable.
- **Key Management**: Encryption key derived from Windows DPAPI (`CryptProtectData`) or system keychain, ensuring the key is hardware-tied and never stored in plaintext on disk.
- **FAISS Vectors**: Vectors themselves are non-reversible mathematical representations, but can be encrypted when persisted to disk via standard symmetric envelope.
- **Evaluation**: 100% portable across Windows x86_64, Windows ARM64 (Snapdragon), Linux, and macOS without native C compiler dependencies.

---

## 3. Migration Strategy & Recommendation

1. **Phase 4 Status**: **NOT IMPLEMENTED IN PHASE 4 TO PREVENT DATA CORRUPTION**.
2. **Phase 5 Milestone**: Implement Application-Layer Encryption using `cryptography` + Windows DPAPI:
   - Step 1: Add automated migration script to read existing SQLite tables and re-encrypt sensitive columns.
   - Step 2: Implement transparent field-level encryption getters/setters in SQLAlchemy models.
   - Step 3: Implement DPAPI key provider on Windows with fallback to secure user passphrase.
