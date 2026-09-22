# AI Models and Local Inference

AuraGuard uses an abstraction layer for both AI generation and embeddings so the backend can later adopt Snapdragon-optimized or ONNX-based models without forcing a redesign.

## Current abstraction

- AIProvider.generate(prompt, context)
- EmbeddingProvider.embed(texts)

## Future model strategy

The project is intentionally structured so the implementation can later validate Qualcomm AI Hub models, Windows on Snapdragon support, ONNX Runtime, and NPU-accelerated models only after actual benchmark evidence is collected.

## Important constraint

No model should be selected based on assumption. It must be validated against the device and runtime in the environment before claiming Snapdragon optimization or NPU execution.
