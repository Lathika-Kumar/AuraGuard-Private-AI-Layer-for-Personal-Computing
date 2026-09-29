#!/usr/bin/env python3
"""Export sentence-transformers/all-MiniLM-L6-v2 to ONNX format for Qualcomm AI Hub / QNN deployment."""

import argparse
import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
import onnx
import onnxruntime as ort
import torch
from transformers import AutoModel, AutoTokenizer


def export_embedding_to_onnx(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    output_dir: str = "models/onnx",
    opset: int = 17,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    onnx_file = out_path / "embedding_model.onnx"

    print(f"[1/4] Loading PyTorch model and tokenizer: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    # Create dummy input for tracing
    sample_text = "AuraGuard provides private local on-device neural context."
    dummy_inputs = tokenizer(
        sample_text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=128,
    )

    input_names = ["input_ids", "attention_mask", "token_type_ids"]
    output_names = ["last_hidden_state"]

    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "token_type_ids": {0: "batch_size", 1: "sequence_length"},
        "last_hidden_state": {0: "batch_size", 1: "sequence_length"},
    }

    inputs_tuple = (
        dummy_inputs["input_ids"],
        dummy_inputs["attention_mask"],
        dummy_inputs.get("token_type_ids", torch.zeros_like(dummy_inputs["input_ids"])),
    )

    class EmbeddingWrapper(torch.nn.Module):
        def __init__(self, inner_model):
            super().__init__()
            self.inner_model = inner_model

        def forward(self, input_ids, attention_mask, token_type_ids):
            out = self.inner_model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids,
                return_dict=True,
            )
            return out.last_hidden_state

    wrapper = EmbeddingWrapper(model)
    wrapper.eval()

    print(f"[2/4] Exporting PyTorch model to ONNX at {onnx_file} (opset {opset})...")
    torch.onnx.export(
        wrapper,
        inputs_tuple,
        str(onnx_file),
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
        opset_version=opset,
        do_constant_folding=True,
        dynamo=False,
    )

    print("[3/4] Validating ONNX structure with onnx.checker...")
    onnx_model = onnx.load(str(onnx_file))
    onnx.checker.check_model(onnx_model)
    file_size_mb = onnx_file.stat().st_size / (1024 * 1024)
    print(f"      Valid ONNX model successfully generated: {file_size_mb:.2f} MB")

    print("[4/4] Verifying execution with ONNX Runtime...")
    session = ort.InferenceSession(str(onnx_file), providers=["CPUExecutionProvider"])
    ort_inputs = {
        "input_ids": dummy_inputs["input_ids"].numpy(),
        "attention_mask": dummy_inputs["attention_mask"].numpy(),
        "token_type_ids": dummy_inputs["token_type_ids"].numpy()
        if "token_type_ids" in dummy_inputs
        else np.zeros_like(dummy_inputs["input_ids"].numpy()),
    }
    ort_outputs = session.run(None, ort_inputs)
    assert ort_outputs[0].shape[-1] == 384, f"Unexpected hidden size: {ort_outputs[0].shape}"
    print(f"      ONNX Runtime verification passed! Output shape: {ort_outputs[0].shape}")

    return onnx_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Embedding model to ONNX.")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--output-dir", default="models/onnx")
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()

    export_embedding_to_onnx(model_name=args.model, output_dir=args.output_dir, opset=args.opset)
