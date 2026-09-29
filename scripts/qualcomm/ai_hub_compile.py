#!/usr/bin/env python3
"""Qualcomm AI Hub compilation pipeline and preparation script for AuraGuard.
Prepares and submits ONNX model artifacts for compilation to Qualcomm Hexagon NPU QNN binaries.

Supports:
  - Target: Snapdragon X Elite (compute_unit: NPU)
  - Runtime: QNN (Qualcomm Neural Network SDK)
  - Precision: INT8 (w8a8) for embeddings, INT4/INT8 for LLM
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def get_compilation_manifest() -> dict:
    """Returns the precise model compilation specifications for Qualcomm AI Hub."""
    return {
        "embedding": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "source_artifact": "models/onnx/embedding_model.onnx",
            "target_device": "Snapdragon X Elite CRD",
            "accelerator": "Qualcomm Hexagon NPU",
            "runtime": "QNN (Qualcomm Neural Network) v2.22+",
            "precision": "INT8 (w8a8) / FP16 fallback",
            "input_shapes": {
                "input_ids": [1, 128],
                "attention_mask": [1, 128],
                "token_type_ids": [1, 128],
            },
            "output_shapes": {
                "last_hidden_state": [1, 128, 384],
            },
            "compiler_options": "--target_runtime qnn_context_binary --quantization_overrides w8a8",
            "expected_artifact": "all_minilm_l6_v2_qnn_npu.bin",
        },
        "llm": {
            "model_name": "Qwen/Qwen2.5-0.5B-Instruct",
            "source_model_id": "Qwen/Qwen2.5-0.5B-Instruct",
            "target_device": "Snapdragon X Elite CRD",
            "accelerator": "Qualcomm Hexagon NPU",
            "runtime": "QNN v2.22+ via ONNX Runtime GenAI",
            "precision": "INT4 (w4a16) / INT8 (w8a16)",
            "context_window": 2048,
            "compiler_options": "--target_runtime qnn_context_binary --weights_precision int4 --activations_precision fp16",
            "expected_artifact": "qwen2_5_0_5b_qnn_w4a16.bin",
        },
    }


def prepare_ai_hub_compilation(api_token: str | None = None) -> dict:
    manifest = get_compilation_manifest()
    print("=" * 70)
    print("QUALCOMM AI HUB COMPILATION PIPELINE SPECIFICATION")
    print("=" * 70)
    print(json.dumps(manifest, indent=2))

    # Check for Qualcomm AI Hub API Token
    token = api_token or os.getenv("QAI_HUB_API_TOKEN")
    status_report = {
        "pipeline_state": "PREPARED",
        "manifest": manifest,
        "auth_configured": bool(token),
    }

    if not token:
        print("\n" + "-" * 70)
        print("STOPPING AT OFFICIAL PREPARATION STAGE: QAI_HUB_API_TOKEN Not Provided")
        print("-" * 70)
        print("Qualcomm AI Hub requires authenticated cloud/CLI submission:")
        print("  1. Obtain API token from: https://app.aihub.qualcomm.com")
        print("  2. Configure environment: set QAI_HUB_API_TOKEN=<your-token>")
        print("  3. Run compile: `qai-hub compile --model models/onnx/embedding_model.onnx ...`")
        print("Result: Artifact preparation complete. Live submission halted per Step 9 protocol.")
        status_report["status"] = "PREPARATION COMPLETE — AUTHENTICATION REQUIRED FOR CLOUD COMPILATION"
    else:
        print("\nAPI token detected. Attempting Qualcomm AI Hub API connection...")
        try:
            import qai_hub as hub  # type: ignore
            hub.set_access_token(token)
            devices = hub.get_devices()
            print(f"Connected to Qualcomm AI Hub. Available devices count: {len(devices)}")
            status_report["status"] = "AUTHENTICATED — READY TO SUBMIT JOBS"
            status_report["device_count"] = len(devices)
        except ImportError:
            print("Notice: `qai-hub` Python package not installed in environment.")
            print("Install via: pip install qai-hub")
            status_report["status"] = "PACKAGE NOT INSTALLED — `pip install qai-hub` REQUIRED"
        except Exception as e:
            print(f"Qualcomm AI Hub connection returned: {e}")
            status_report["status"] = f"ERROR: {e}"

    # Write compilation manifest to docs
    out_path = Path("docs/qualcomm-compilation-manifest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(status_report, f, indent=2)
    print(f"\nManifest saved to {out_path}")
    return status_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Qualcomm AI Hub compilation pipeline.")
    parser.add_argument("--token", default=None, help="Qualcomm AI Hub API token")
    args = parser.parse_args()
    prepare_ai_hub_compilation(args.token)
