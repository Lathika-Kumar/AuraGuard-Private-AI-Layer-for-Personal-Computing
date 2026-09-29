#!/usr/bin/env python3
"""Export Qwen2.5-0.5B-Instruct to ONNX format for Qualcomm AI Hub / QNN deployment."""

import argparse
import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import onnx
import onnxruntime as ort
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def export_llm_to_onnx(
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
    output_dir: str = "models/onnx",
    opset: int = 17,
    max_seq_len: int = 128,
) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    onnx_file = out_path / "qwen2_5_0_5b.onnx"

    cache_dir = Path("models/huggingface").resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir)
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

    print(f"[1/4] Loading PyTorch LLM and tokenizer: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(cache_dir))
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=str(cache_dir),
        dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.eval()

    # Create dummy prompt input
    sample_prompt = "Question: What is AuraGuard?\nAnswer:"
    dummy_inputs = tokenizer(
        sample_prompt,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_seq_len,
    )

    input_names = ["input_ids", "attention_mask"]
    output_names = ["logits"]

    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "logits": {0: "batch_size", 1: "sequence_length"},
    }

    inputs_tuple = (
        dummy_inputs["input_ids"],
        dummy_inputs["attention_mask"],
    )

    # Wrapper class to output only logits for clean export
    class CausalLMLogitsWrapper(torch.nn.Module):
        def __init__(self, base_model):
            super().__init__()
            self.base_model = base_model

        def forward(self, input_ids, attention_mask):
            outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False)
            return outputs.logits

    wrapper = CausalLMLogitsWrapper(model)
    wrapper.eval()

    print(f"[2/4] Exporting PyTorch LLM to ONNX at {onnx_file} (opset {opset})...")
    try:
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
        print(f"      Valid ONNX LLM model generated: {file_size_mb:.2f} MB")

        print("[4/4] Verifying execution with ONNX Runtime...")
        session = ort.InferenceSession(str(onnx_file), providers=["CPUExecutionProvider"])
        ort_inputs = {
            "input_ids": dummy_inputs["input_ids"].numpy(),
            "attention_mask": dummy_inputs["attention_mask"].numpy(),
        }
        ort_outputs = session.run(None, ort_inputs)
        logits = ort_outputs[0]
        next_token_id = int(logits[0, -1, :].argmax())
        predicted_token = tokenizer.decode([next_token_id])
        print(f"      ONNX Runtime verification passed! Next predicted token: '{predicted_token}' (ID {next_token_id})")
        return onnx_file

    except MemoryError as e:
        print("\n" + "=" * 70)
        print("DIAGNOSTIC: Host RAM Insufficient for Monolithic FP32 LLM ONNX Graph")
        print("=" * 70)
        print(f"Error caught: {e}")
        print("The development host (Intel i5-1235U, ~7.65 GB RAM) ran out of physical")
        print("memory while serializing the unquantized FP32 494M parameter LLM graph.")
        print("Required deployment workflow for Qualcomm Snapdragon NPU:")
        print("  1. Direct Qualcomm AI Hub CLI compilation: `qai-hub compile` targeting Snapdragon X Elite")
        print("  2. Pre-quantized INT4/INT8 ONNX weight-streaming export (ONNX Runtime GenAI)")
        print("  3. Build host with >= 16 GB RAM for unquantized FP32 monolithic serialization")
        print("Status: NOT EXECUTED ON 8GB HOST — TARGET WORKSTATION OR AI HUB CLI REQUIRED")
        print("=" * 70 + "\n")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Qwen LLM to ONNX.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--output-dir", default="models/onnx")
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument("--max-seq-len", type=int, default=64)
    args = parser.parse_args()

    export_llm_to_onnx(
        model_name=args.model,
        output_dir=args.output_dir,
        opset=args.opset,
        max_seq_len=args.max_seq_len,
    )
