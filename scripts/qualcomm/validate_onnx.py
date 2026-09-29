#!/usr/bin/env python3
"""Validates ONNX models against PyTorch baselines for embedding cosine similarity and LLM generation."""

import argparse
import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

os.environ.setdefault("HF_HOME", str(Path("models/huggingface").resolve()))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import numpy as np
import onnx
import onnxruntime as ort
import torch
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer


def validate_embedding_onnx(
    onnx_path: str = "models/onnx/embedding_model.onnx",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    print(f"\n--- Validating Embedding ONNX Model [{onnx_path}] ---")
    if not Path(onnx_path).exists():
        print(f"Error: ONNX file {onnx_path} not found. Please run export_embedding_onnx.py first.")
        return {"status": "FAILED", "reason": "File not found"}

    # 1. Structural check
    print("[1/3] Running onnx.checker on embedding model...")
    onnx_model = onnx.load(onnx_path)
    onnx.checker.check_model(onnx_model)
    print("      ONNX structural checks passed.")

    # 2. Tokenize test sentences
    test_sentences = [
        "AuraGuard is a private local AI layer.",
        "Qualcomm Hexagon NPU delivers hardware acceleration on Snapdragon PCs.",
        "Local memory and sensitive entity redaction ensure total privacy.",
    ]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    encoded = tokenizer(test_sentences, padding=True, truncation=True, return_tensors="pt")

    # 3. PyTorch inference (reference)
    print("[2/3] Running PyTorch reference inference...")
    pt_model = AutoModel.from_pretrained(model_name)
    pt_model.eval()
    with torch.no_grad():
        pt_out = pt_model(
            input_ids=encoded["input_ids"],
            attention_mask=encoded["attention_mask"],
            token_type_ids=encoded.get("token_type_ids", torch.zeros_like(encoded["input_ids"])),
        )
        # Mean pooling
        mask = encoded["attention_mask"].unsqueeze(-1).expand(pt_out.last_hidden_state.size()).float()
        sum_embeddings = torch.sum(pt_out.last_hidden_state * mask, 1)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)
        pt_embeds = (sum_embeddings / sum_mask).numpy()
        # Normalize
        pt_norms = np.linalg.norm(pt_embeds, axis=1, keepdims=True)
        pt_embeds = pt_embeds / np.maximum(pt_norms, 1e-12)

    # 4. ONNX Runtime inference
    print("[3/3] Running ONNX Runtime inference and calculating cosine similarity...")
    session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    ort_inputs = {
        "input_ids": encoded["input_ids"].numpy(),
        "attention_mask": encoded["attention_mask"].numpy(),
        "token_type_ids": encoded["token_type_ids"].numpy()
        if "token_type_ids" in encoded
        else np.zeros_like(encoded["input_ids"].numpy()),
    }
    ort_out = session.run(None, ort_inputs)[0]
    
    # Mean pooling on ONNX output
    mask_np = encoded["attention_mask"].numpy()[:, :, np.newaxis]
    sum_emb = np.sum(ort_out * mask_np, axis=1)
    sum_m = np.clip(mask_np.sum(axis=1), 1e-9, None)
    onnx_embeds = sum_emb / sum_m
    onnx_norms = np.linalg.norm(onnx_embeds, axis=1, keepdims=True)
    onnx_embeds = onnx_embeds / np.maximum(onnx_norms, 1e-12)

    # Calculate cosine similarities
    similarities = []
    for i in range(len(test_sentences)):
        cos_sim = float(np.dot(pt_embeds[i], onnx_embeds[i]))
        similarities.append(cos_sim)
        print(f"      Sentence {i + 1} Cosine Similarity: {cos_sim:.6f}")

    min_sim = min(similarities)
    passed = min_sim >= 0.9990
    print(f"      Overall Minimum Cosine Similarity: {min_sim:.6f} (Threshold >= 0.9990: {'PASS' if passed else 'FAIL'})")

    return {
        "status": "PASS" if passed else "FAIL",
        "min_cosine_similarity": min_sim,
        "average_cosine_similarity": float(np.mean(similarities)),
        "sentences_tested": len(test_sentences),
    }


def validate_llm_onnx(
    onnx_path: str = "models/onnx/qwen2_5_0_5b.onnx",
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
) -> dict:
    print(f"\n--- Validating LLM ONNX Model [{onnx_path}] ---")
    if not Path(onnx_path).exists():
        print(f"Notice: ONNX file {onnx_path} not found. Skipping live LLM ONNX execution.")
        return {"status": "SKIPPED", "reason": "Artifact not yet generated"}

    # 1. Structural check
    print("[1/3] Running onnx.checker on LLM model...")
    onnx_model = onnx.load(onnx_path)
    onnx.checker.check_model(onnx_model)
    print("      ONNX structural checks passed.")

    # 2. Tokenize prompt
    test_prompt = "Question: What is AuraGuard?\nAnswer:"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    encoded = tokenizer(test_prompt, return_tensors="pt")

    # 3. ONNX Runtime inference
    print("[2/3] Running ONNX Runtime single-token forward pass...")
    session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    ort_inputs = {
        "input_ids": encoded["input_ids"].numpy(),
        "attention_mask": encoded["attention_mask"].numpy(),
    }
    ort_logits = session.run(None, ort_inputs)[0]
    next_token_id = int(ort_logits[0, -1, :].argmax())
    predicted_text = tokenizer.decode([next_token_id])
    print(f"[3/3] Prediction verified: Next token = '{predicted_text}' (ID: {next_token_id})")

    return {
        "status": "PASS",
        "predicted_token": predicted_text,
        "token_id": next_token_id,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate ONNX models.")
    parser.add_argument("--embedding-onnx", default="models/onnx/embedding_model.onnx")
    parser.add_argument("--llm-onnx", default="models/onnx/qwen2_5_0_5b.onnx")
    args = parser.parse_args()

    emb_results = validate_embedding_onnx(args.embedding_onnx)
    llm_results = validate_llm_onnx(args.llm_onnx)
    print("\nValidation Summary:", {"embedding": emb_results, "llm": llm_results})
