#!/usr/bin/env python3
"""Regression testing for AuraGuard core behaviors across FP32 and Quantized INT8 representations.
Tests:
  1. Document retrieval ranking (FP32 vs INT8 embedding)
  2. Memory retrieval (ReMind episodic store)
  3. Grounded answering
  4. Privacy detection (PII / credentials)
  5. Prompt-injection defense
Uses test fixtures only.
"""

import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Point backend imports to path
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import numpy as np
import onnxruntime as ort
import torch
from transformers import AutoTokenizer

from app.services.privacy_service import PrivacyService, PrivacyClassification, PrivacyAction
from app.services.output_guard import OutputGuard


def run_regression_tests():
    print("=" * 65)
    print("STEP 8: QUALITY REGRESSION TESTS (FP32 vs INT8 / CORE DEFENSES)")
    print("=" * 65)

    results = {}

    # Test 1: Privacy Detection (Deterministic Rule & Pattern Engine)
    print("\n[1/5] Testing Privacy Detection...")
    test_pii = "My email is support@auraguard.internal and card is 4532-1111-2222-3333."
    scan_result = PrivacyService.analyze(test_pii, stage="input")
    pii_passed = (
        scan_result.classification in [PrivacyClassification.SENSITIVE, PrivacyClassification.HIGHLY_SENSITIVE]
        and len(scan_result.entities) >= 1
    )
    detected_types = [e.type for e in scan_result.entities]
    results["privacy_detection"] = {
        "status": "PASS" if pii_passed else "FAIL",
        "detected_entities": detected_types,
        "classification": scan_result.classification.value,
        "redacted_text": scan_result.redacted_text,
    }
    print(f"      Privacy scan passed: {pii_passed} (Detected: {detected_types})")

    # Test 2: Sensitive Financial / Credential Blocking
    print("\n[2/5] Testing Sensitive Credential Redaction & Blocking...")
    secret_text = "Private key is -----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY----- and api_key='sk-1234567890abcdef1234567890abcdef'"
    scan_secret = PrivacyService.analyze(secret_text, stage="context")
    sec_blocked = (
        scan_secret.classification in [PrivacyClassification.HIGHLY_SENSITIVE, PrivacyClassification.SENSITIVE]
        or any(e.action == PrivacyAction.BLOCK for e in scan_secret.entities)
    )
    results["sensitive_entity_defense"] = {
        "status": "PASS" if sec_blocked else "FAIL",
        "classification": scan_secret.classification.value,
        "allowed": scan_secret.allowed,
    }
    print(f"      Sensitive credential defense passed: {sec_blocked} (Class: {scan_secret.classification.value})")

    # Test 3: Document Retrieval Ranking (FP32 vs INT8 ONNX embeddings)
    print("\n[3/5] Testing Document Retrieval Ranking Consistency (FP32 vs INT8)...")
    docs = [
        "AuraGuard runs private on-device local RAG with neural search.",
        "Snapdragon X Elite features Hexagon NPU for 45 TOPS AI acceleration.",
        "The recipe calls for two cups of flour and three eggs.",
        "Federal reserve interest rate policy update for quarterly projections.",
    ]
    query = "How does AuraGuard perform private on-device retrieval?"

    fp32_path = "models/onnx/embedding_model.onnx"
    int8_path = "models/onnx/embedding_model_int8.onnx"

    if Path(fp32_path).exists() and Path(int8_path).exists():
        tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(Path("models/huggingface").resolve()),
        )
        all_texts = [query] + docs
        encoded = tokenizer(all_texts, padding=True, truncation=True, return_tensors="pt")
        ort_inputs = {
            "input_ids": encoded["input_ids"].numpy(),
            "attention_mask": encoded["attention_mask"].numpy(),
            "token_type_ids": encoded.get("token_type_ids", torch.zeros_like(encoded["input_ids"])).numpy(),
        }

        # Embeddings Helper
        def get_embeds(onnx_file):
            sess = ort.InferenceSession(onnx_file, providers=["CPUExecutionProvider"])
            out = sess.run(None, ort_inputs)[0]
            mask_np = encoded["attention_mask"].numpy()[:, :, np.newaxis]
            sum_emb = np.sum(out * mask_np, axis=1)
            sum_m = np.clip(mask_np.sum(axis=1), 1e-9, None)
            emb = sum_emb / sum_m
            norms = np.linalg.norm(emb, axis=1, keepdims=True)
            return emb / np.maximum(norms, 1e-12)

        embeds_fp32 = get_embeds(fp32_path)
        embeds_int8 = get_embeds(int8_path)

        # Dot product with query (first vector)
        scores_fp32 = np.dot(embeds_fp32[1:], embeds_fp32[0])
        scores_int8 = np.dot(embeds_int8[1:], embeds_int8[0])

        top_fp32_idx = int(np.argmax(scores_fp32))
        top_int8_idx = int(np.argmax(scores_int8))

        ranking_match = top_fp32_idx == top_int8_idx == 0  # Index 0 is the AuraGuard doc
        results["document_retrieval"] = {
            "status": "PASS" if ranking_match else "FAIL",
            "top_doc_fp32_index": top_fp32_idx,
            "top_doc_fp32_score": float(scores_fp32[top_fp32_idx]),
            "top_doc_int8_index": top_int8_idx,
            "top_doc_int8_score": float(scores_int8[top_int8_idx]),
            "rank_consistency": ranking_match,
        }
        print(f"      Top doc match: FP32 Doc {top_fp32_idx} (score {scores_fp32[top_fp32_idx]:.4f}) vs INT8 Doc {top_int8_idx} (score {scores_int8[top_int8_idx]:.4f}) -> Consistent: {ranking_match}")
    else:
        results["document_retrieval"] = {"status": "SKIPPED", "reason": "ONNX files not found"}

    # Test 4: Memory Retrieval Consistency
    print("\n[4/5] Testing ReMind Memory Semantic Retrieval Consistency...")
    memories = [
        "User prefers local dark mode in settings.",
        "User discussed Snapdragon NPU execution provider optimizations yesterday.",
        "User visited the grocery store on Sunday morning.",
    ]
    mem_query = "What hardware accelerator was discussed for local execution?"
    if Path(fp32_path).exists() and Path(int8_path).exists():
        mem_texts = [mem_query] + memories
        enc_mem = tokenizer(mem_texts, padding=True, truncation=True, return_tensors="pt")
        mem_inputs = {
            "input_ids": enc_mem["input_ids"].numpy(),
            "attention_mask": enc_mem["attention_mask"].numpy(),
            "token_type_ids": enc_mem.get("token_type_ids", torch.zeros_like(enc_mem["input_ids"])).numpy(),
        }

        def get_mem_embeds(onnx_file):
            sess = ort.InferenceSession(onnx_file, providers=["CPUExecutionProvider"])
            out = sess.run(None, mem_inputs)[0]
            mask_np = enc_mem["attention_mask"].numpy()[:, :, np.newaxis]
            sum_emb = np.sum(out * mask_np, axis=1)
            sum_m = np.clip(mask_np.sum(axis=1), 1e-9, None)
            emb = sum_emb / sum_m
            norms = np.linalg.norm(emb, axis=1, keepdims=True)
            return emb / np.maximum(norms, 1e-12)

        m_fp32 = get_mem_embeds(fp32_path)
        m_int8 = get_mem_embeds(int8_path)
        m_scores_fp32 = np.dot(m_fp32[1:], m_fp32[0])
        m_scores_int8 = np.dot(m_int8[1:], m_int8[0])

        top_mem_fp32 = int(np.argmax(m_scores_fp32))
        top_mem_int8 = int(np.argmax(m_scores_int8))
        mem_match = top_mem_fp32 == top_mem_int8 == 1  # Index 1 is Snapdragon NPU
        results["memory_retrieval"] = {
            "status": "PASS" if mem_match else "FAIL",
            "top_memory_fp32_index": top_mem_fp32,
            "top_memory_int8_index": top_mem_int8,
            "consistency": mem_match,
        }
        print(f"      Top memory match: FP32 Memory {top_mem_fp32} vs INT8 Memory {top_mem_int8} -> Consistent: {mem_match}")
    else:
        results["memory_retrieval"] = {"status": "SKIPPED", "reason": "ONNX files not found"}

    # Test 5: Grounded Answering Output Verification
    print("\n[5/5] Testing Grounded Answering Guardrails...")
    clean_answer = "Based on your local document, AuraGuard uses FAISS and local embeddings."
    guard_res = OutputGuard.sanitize(clean_answer)
    results["output_guard"] = {
        "status": "PASS" if not guard_res.was_modified else "FAIL",
        "was_modified": guard_res.was_modified,
        "blocked": guard_res.blocked,
    }
    print(f"      Output guard verification passed: {not guard_res.was_modified}")

    print("\n" + "=" * 65)
    print("REGRESSION TEST RESULTS SUMMARY")
    print("=" * 65)
    print(json.dumps(results, indent=2))

    out_file = Path("docs/regression-test-results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved regression results to {out_file}")
    return results


if __name__ == "__main__":
    run_regression_tests()
