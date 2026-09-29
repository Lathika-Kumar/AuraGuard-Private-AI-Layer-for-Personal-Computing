# AuraGuard Privacy Engine

## Overview

The **AuraGuard Privacy Engine** is an on-device, local-first inspection and policy enforcement layer designed to detect, classify, sanitize, and guard sensitive personal data before, during, and after AI reasoning.

Operating strictly within the user's personal computing environment, the Privacy Engine ensures that **no user documents, queries, context chunks, or personal identifiers are ever transmitted to third-party cloud services or telemetry pipelines**.

---

## Architecture & Data Flow

The Privacy Engine introduces **three non-negotiable checkpoints** across the AI workflow:

```text
       User Query
           │
     [Checkpoint 1] ───► Input Privacy Scan ───► Policy Decision (Allow / Warn / Block)
           │
     Embedding & Retrieval (FAISS Documents + ReMind Memories)
           │
     [Checkpoint 2] ───► Context Privacy Filter ───► Redact sensitive entities / Filter secrets
           │
     Local On-Device LLM (Untrusted context directive)
           │
     [Checkpoint 3] ───► Output Privacy Guard ───► Scan generated text ───► Redact / Block leaks
           │
      Verified Answer
```

---

## Entity Categories & Detection

The engine inspects input text and retrieved text for 12 primary categories:

| Entity Category | Classification | Default Action (Balanced) | Detection Mechanism |
| :--- | :--- | :--- | :--- |
| **PRIVATE KEY** | HIGHLY_SENSITIVE | **BLOCK** | PEM block header/footer markers (`RSA`, `EC`, `DSA`, `OPENSSH`) |
| **PASSWORD** | HIGHLY_SENSITIVE | **BLOCK** | Labeled password strings (`password:`, `passwd =`, `pwd:`) |
| **API KEY** | HIGHLY_SENSITIVE | **BLOCK** | Prefixed keys (`sk-`, `AKIA`, `ghp_`, `AIza`) and labeled tokens |
| **AUTH TOKEN** | HIGHLY_SENSITIVE | **BLOCK** | JWT (`eyJ...`) and Bearer authentication tokens |
| **CREDIT/DEBIT CARD** | HIGHLY_SENSITIVE | **BLOCK** | 13-19 digit card patterns with **Luhn algorithm** checksum validation |
| **BANK ACCOUNT** | HIGHLY_SENSITIVE | **BLOCK** | International IBAN strings and domestic account/routing numbers |
| **IDENTIFICATION NUMBER** | SENSITIVE | **REDACT** | Social Security Numbers (`SSN`), Passports, National IDs |
| **DATE OF BIRTH** | SENSITIVE | **REDACT** | Labeled DOB patterns (`born on`, `DOB:`) and formatted date structures |
| **ADDRESS** | SENSITIVE | **REDACT** | Physical street addresses (`Street`, `Ave`, `Blvd`, `Road`) & PO Boxes |
| **EMAIL** | PERSONAL | **WARN / REDACT** | RFC 5322 compliant email regex matching |
| **PHONE** | PERSONAL | **WARN / REDACT** | International (E.164) and domestic telephone number patterns |
| **PERSONAL NAME** | PERSONAL | **WARN / REDACT** | Honorific titles (`Mr.`, `Dr.`, `Prof.`) and labeled person names |

---

## Classification Levels

1. **PUBLIC**: General non-identifying facts, public specifications, standard domain text.
2. **PERSONAL**: Basic contact and direct personal identifiers (`EMAIL`, `PHONE`, `PERSONAL NAME`).
3. **SENSITIVE**: High-confidentiality identifiers and demographic anchors (`ADDRESS`, `DATE OF BIRTH`, `IDENTIFICATION NUMBER`).
4. **HIGHLY_SENSITIVE**: Secrets, credentials, private cryptographic keys, authentication tokens, and financial instruments (`PASSWORD`, `API KEY`, `PRIVATE KEY`, `AUTH TOKEN`, `CREDIT CARD`, `BANK ACCOUNT`).

---

## Policy Engine Modes

The system policy is configurable via `PRIVACY_MODE` (`strict`, `balanced`, `permissive`):

- **Strict**:
  - `HIGHLY_SENSITIVE` $\rightarrow$ **BLOCK**
  - `SENSITIVE` $\rightarrow$ **REDACT**
  - `PERSONAL` $\rightarrow$ **REDACT**
  - Designed for strict enterprise compliance or public workstations.
- **Balanced (Default)**:
  - `HIGHLY_SENSITIVE` $\rightarrow$ **BLOCK**
  - `SENSITIVE` $\rightarrow$ **REDACT**
  - `PERSONAL` $\rightarrow$ **WARN** on query input; **REDACT** in LLM context and outputs.
  - Balances frictionless personal search with strong credential containment.
- **Permissive**:
  - `HIGHLY_SENSITIVE` $\rightarrow$ **REDACT** in outputs / **WARN** on input.
  - `SENSITIVE` $\rightarrow$ **WARN**
  - `PERSONAL` $\rightarrow$ **ALLOW**
  - Designed for local development and debugging.

---

## Privacy Audit Ledger

Whenever an entity is redacted or a request is blocked, a record is entered into the local SQLite `privacy_events` table:

```json
{
  "event_type": "INPUT_REDACTED",
  "entity_type": "EMAIL",
  "severity": "MEDIUM",
  "source": "ask_input",
  "action": "REDACT",
  "timestamp": "2026-09-29T14:27:00Z"
}
```

> **Strict Non-Storage Rule:** AuraGuard NEVER logs raw secrets, passwords, full card numbers, or cryptographic keys in audit logs or database tables.
