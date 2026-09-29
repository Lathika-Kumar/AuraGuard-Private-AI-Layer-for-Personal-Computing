from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List
import numpy as np

from app.core.config import settings
from fastembed import TextEmbedding


class EmbeddingProvider:
    """Real on-device neural embedding provider using ONNX Runtime via FastEmbed.
    
    Loads once, caches locally, and performs batch embedding with normalized vectors.
    """
    _instance: TextEmbedding | None = None
    _loaded_model_name: str | None = None

    def __init__(
        self,
        model_name: str | None = None,
        cache_dir: Path | None = None,
        device: str | None = None,
    ):
        self.model_name = model_name or settings.embedding_model
        self.cache_dir = cache_dir or (settings.model_cache_dir / "fastembed")
        self.device = device or settings.embedding_device
        self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        if EmbeddingProvider._instance is None or EmbeddingProvider._loaded_model_name != self.model_name:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            EmbeddingProvider._instance = TextEmbedding(
                model_name=self.model_name,
                cache_dir=str(self.cache_dir),
            )
            EmbeddingProvider._loaded_model_name = self.model_name
        self._model = EmbeddingProvider._instance

    @property
    def dimension(self) -> int:
        return 384

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch embed a list of strings returning float lists."""
        if not texts:
            return []
        embeddings = list(self._model.embed(texts))
        return [vec.tolist() for vec in embeddings]

    def embed(self, texts: Iterable[str]) -> List[np.ndarray]:
        """Batch embed texts returning float32 numpy arrays for FAISS indexing."""
        text_list = list(texts)
        if not text_list:
            return []
        embeddings = list(self._model.embed(text_list))
        return [np.asarray(vec, dtype="float32") for vec in embeddings]
