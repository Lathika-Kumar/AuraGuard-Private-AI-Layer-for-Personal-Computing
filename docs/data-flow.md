# Data Flow

## Upload flow

1. User uploads a PDF file through the React dashboard.
2. The backend validates the file extension and size.
3. The server computes a SHA-256 hash and stores the file locally.
4. The document metadata is recorded in SQLite.
5. The document is ready for future local processing steps.

## Retrieval flow

1. User asks a question in the UI.
2. The backend embeds the question.
3. The system performs a local vector search over indexed chunks.
4. Relevant document chunks are assembled into context.
5. A local AI provider answers only from that context.
6. Source references are returned to the frontend.

## Privacy guarantees

No user content is uploaded to external services in the MVP. The backend performs all processing locally and does not log document contents or PII.
