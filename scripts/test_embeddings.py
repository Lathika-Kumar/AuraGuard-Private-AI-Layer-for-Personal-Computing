"""Verification script for real on-device neural embeddings."""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

# Ensure backend directory is in path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.embedding_service import EmbeddingProvider


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def main() -> None:
    print("Loading real neural embedding model...")
    provider = EmbeddingProvider()
    print(f"Model: {provider.model_name}")
    print(f"Dimension: {provider.dimension}")

    sentence_a = "The internship application deadline is Friday."
    sentence_b = "The deadline for submitting the internship application is Friday."
    sentence_c = "The weather is sunny today."

    print("\nTest Sentences:")
    print(f"  Sentence A: \"{sentence_a}\"")
    print(f"  Sentence B: \"{sentence_b}\"")
    print(f"  Sentence C: \"{sentence_c}\"")

    vectors = provider.embed([sentence_a, sentence_b, sentence_c])
    vec_a, vec_b, vec_c = vectors[0], vectors[1], vectors[2]

    sim_ab = cosine_similarity(vec_a, vec_b)
    sim_ac = cosine_similarity(vec_a, vec_c)
    sim_bc = cosine_similarity(vec_b, vec_c)

    print("\nCalculated Cosine Similarities (Real Neural Embeddings):")
    print(f"  Similarity(A, B) [Semantically Equivalent]: {sim_ab:.4f}")
    print(f"  Similarity(A, C) [Semantically Unrelated] : {sim_ac:.4f}")
    print(f"  Similarity(B, C) [Semantically Unrelated] : {sim_bc:.4f}")

    assert sim_ab > sim_ac, f"Expected sim(A, B) > sim(A, C), got {sim_ab} <= {sim_ac}"
    print("\nVerification PASSED: Real neural embedding semantic separation confirmed.")


if __name__ == "__main__":
    main()
