# AuraGuard Evidence: Privacy Verification & Zero Cloud Leakage

## 1. Zero Cloud Leakage Guarantee
AuraGuard's on-device privacy guarantee is verified through architectural isolation and runtime inspection:
* **Loopback Binding**: The FastAPI backend server binds strictly to `127.0.0.1:8000` (localhost).
* **Zero External Inference APIs**: The codebase contains zero HTTP client requests to OpenAI, Anthropic, HuggingFace Inference API, or any third-party AI provider.
* **Air-Gap Capability**: AuraGuard functions with 100% feature parity with network interfaces completely disconnected.

---

## 2. Multi-Checkpoint Defense Integrity
The privacy engine operates as a non-bypassable wrapper around model execution:

```text
              User Input
                  │
                  ▼
         [Checkpoint 1: Input Guard]
         Scans for: API keys, Private keys, Passwords, SSNs
         Action: Reject with HTTP 422
                  │
                  ▼
         [Context Synthesis]
                  │
                  ▼
         [Checkpoint 2: Context Neutralizer]
         Scans for: Prompt injection patterns
         Action: Scrub & neutralize before prompt construction
                  │
                  ▼
       ┌──────────┴──────────┐
       │                     │
   CPU Execution         QNN / NPU
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
         [Checkpoint 3: Output Guard]
         Scans for: Inadvertent PII / credential leakage
         Action: Redact before rendering to client
                  │
                  ▼
             Final Answer
```

*Crucial Architecture Invariant:* **The Qualcomm QNN / Hexagon NPU is strictly an internal tensor calculation backend.** It cannot bypass Checkpoint 1, Checkpoint 2, Checkpoint 3, or ReMind encrypted storage gating.
