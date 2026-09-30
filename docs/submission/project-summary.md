# AuraGuard — Project Summary

## Executive Summary

**AuraGuard** is an on-device, privacy-first personal AI computing layer designed for Snapdragon-powered Copilot+ PCs and Windows 11 systems. It unifies local neural retrieval-augmented generation (RAG), user-controlled long-term memory intelligence (ReMind), real-time multi-stage privacy filtering, authenticated local encryption (AES-256-GCM + Windows DPAPI), and hardware-aware AI execution into a single, cohesive personal computing layer.

With AuraGuard, personal computing users can index sensitive personal documents (PDFs, notes, financial statements), retain private context across sessions, and obtain intelligent grounded answers with complete data sovereignty. **Zero bytes of personal data ever leave the local machine.**

---

## The Core Problem

Personal computing is rapidly integrating AI, but contemporary commercial AI solutions require sending sensitive user context—including proprietary documents, confidential emails, financial summaries, and personal notes—to external third-party cloud servers. This introduces:
1. **Loss of Data Sovereignty**: Personal and enterprise confidential information resides on remote servers beyond the user's control.
2. **Privacy and Compliance Vulnerabilities**: Exposure to corporate telemetry, model training on user interactions, and external data breaches.
3. **Adversarial Insecurity**: Direct and indirect prompt injection attacks hidden inside web content or retrieved documents can hijack cloud agents.
4. **Cloud and Network Dependency**: AI tools become unusable offline or in air-gapped secure environments.

---

## The AuraGuard Solution

AuraGuard resolves this conflict by shifting the entire AI lifecycle directly onto the user's personal PC:

* **Documents → Local Neural Retrieval**: Real PDF ingestion, page-aware chunking, dense vector embeddings (`all-MiniLM-L6-v2`), and local FAISS vector search.
* **ReMind → User-Approved Context**: Persistent personal memory with explicit user approval gating, semantic search, and verifiable cryptographic deletion.
* **Privacy Engine → Multi-Stage Guard**: Checkpoint 1 input secret scanning, Checkpoint 2 prompt injection neutralization, and Checkpoint 3 output PII redaction.
* **Local LLM → Private Generative Reasoning**: `Qwen2.5-0.5B-Instruct` executing on-device with source citation transparency.
* **Storage Security → AES-256-GCM + Windows DPAPI**: All stored document text, personal memories, and FAISS indices are encrypted at rest with hardware/OS-backed key management.
* **Qualcomm Snapdragon NPU Path**: Hardware detection, INT8 quantized embeddings, and QNN Execution Provider integration ready for Qualcomm Hexagon NPUs.

---

## Current Verification Status

* **Host Environment Verified**: 12th Gen Intel Core i5-1235U, Windows 11 x86_64, `CPUExecutionProvider` active with 100% automated test coverage.
* **Snapdragon Acceleration Status**: Snapdragon deployment path implemented; physical NPU validation pending access to compatible physical Snapdragon hardware. Automated validation tooling (`scripts/qualcomm/verify_snapdragon.ps1` and `scripts/qualcomm/validate_artifacts.py`) and runtime verification endpoint (`GET /api/system/ai-runtime/verify`) are verified and production-ready.
