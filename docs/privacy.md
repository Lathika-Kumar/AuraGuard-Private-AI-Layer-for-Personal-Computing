# Privacy Architecture

AuraGuard is designed around a strict local-first default. The user controls which files are imported and the application does not automatically scan the entire machine.

## Design principles

- Local file storage only
- Local embeddings and retrieval
- Local metadata in SQLite
- No cloud upload by default
- No analytics or telemetry by default
- Explicit user choice for file imports

## Sensitive content handling

The system is designed so future privacy and ReMind features can classify sensitive patterns while keeping the user in control of confirmation and deletion.
