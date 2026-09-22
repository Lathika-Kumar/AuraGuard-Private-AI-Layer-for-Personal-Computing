# SQLite Database Design

The initial SQLite schema stores the core documents, chunks, tasks, memories, and privacy event metadata needed for the MVP.

## Tables

- documents
- document_chunks
- memories
- tasks
- privacy_events

The database is created automatically when the backend starts. It should remain local to the device and not be shared with any remote service.
