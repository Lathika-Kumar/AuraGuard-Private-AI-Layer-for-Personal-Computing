# AuraGuard Architecture

AuraGuard is designed as a local-first personal AI layer for personal computing. The application intentionally keeps the data plane on the user’s machine and does not rely on any external AI or cloud APIs for the MVP.

## Core architectural decisions

### Local-first processing

The application processes uploads locally, stores metadata in SQLite, indexes vectors locally, and answers user questions using local retrieval rather than remote services. This keeps sensitive personal documents under user control.

### SQLite for local metadata

SQLite is used to store document metadata, chunk metadata, tasks, privacy events, and future memory records because it is lightweight, durable, and sufficient for the MVP’s local desktop use case.

### Vector retrieval

Vector search enables semantic retrieval from previously uploaded documents. The abstraction is still modular so the project can later swap FAISS for another local library if required.

### Snapdragon-aware design

The project is intentionally shaped for Windows on Snapdragon hardware. Model selection and benchmarking will happen only after real hardware validation.
