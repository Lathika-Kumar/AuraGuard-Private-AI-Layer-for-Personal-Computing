import numpy as np
import pytest
from app.services.embedding_service import EmbeddingProvider


def test_embedding_provider_initialization() -> None:
    provider = EmbeddingProvider()
    assert provider.model_name is not None
    assert provider.dimension == 384


def test_embedding_dimension_and_batch() -> None:
    provider = EmbeddingProvider()
    texts = [
        "AuraGuard is a privacy-first local computing layer.",
        "On-device AI protects personal data by avoiding cloud transfers.",
    ]
    vecs = provider.embed(texts)
    assert len(vecs) == 2
    assert isinstance(vecs[0], np.ndarray)
    assert vecs[0].shape == (384,)
    assert vecs[1].shape == (384,)


def test_embed_texts_returns_floats() -> None:
    provider = EmbeddingProvider()
    texts = ["Test sentence for float list embedding."]
    result = provider.embed_texts(texts)
    assert len(result) == 1
    assert len(result[0]) == 384
    assert isinstance(result[0][0], float)


def test_empty_input_handling() -> None:
    provider = EmbeddingProvider()
    assert provider.embed([]) == []
    assert provider.embed_texts([]) == []


def test_similarity_calculation() -> None:
    provider = EmbeddingProvider()
    vecs = provider.embed([
        "The internship application deadline is Friday.",
        "The deadline for submitting the internship application is Friday.",
        "The weather is sunny today.",
    ])
    def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_similar = cosine_sim(vecs[0], vecs[1])
    sim_unrelated = cosine_sim(vecs[0], vecs[2])
    assert sim_similar > 0.85
    assert sim_unrelated < 0.35
    assert sim_similar > sim_unrelated
