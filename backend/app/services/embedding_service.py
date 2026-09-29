from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, List
import numpy as np

from app.core.config import settings
from app.services.hardware_service import HardwareService
from fastembed import TextEmbedding


class EmbeddingProvider:
    """Real on-device neural embedding provider using ONNX Runtime via FastEmbed.
    
    Supports intelligent execution provider resolution (auto / cpu / qnn) with
    automatic, graceful CPU fallback if Qualcomm QNN / NPU is unavailable.
    """
    _instance: TextEmbedding | None = None
    _loaded_model_name: str | None = None
    _active_provider: str = "CPUExecutionProvider"
    _fallback_occurred: bool = False
    _status_reason: str = ""

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
            
            provider, reason, fallback = HardwareService.resolve_execution_provider()
            EmbeddingProvider._active_provider = provider
            EmbeddingProvider._status_reason = reason
            EmbeddingProvider._fallback_occurred = fallback

            requested_providers = [provider]
            if provider != "CPUExecutionProvider":
                requested_providers.append("CPUExecutionProvider")

            EmbeddingProvider._instance = TextEmbedding(
                model_name=self.model_name,
                cache_dir=str(self.cache_dir),
                providers=requested_providers,
            )
            EmbeddingProvider._loaded_model_name = self.model_name
        self._model = EmbeddingProvider._instance

    @property
    def dimension(self) -> int:
        return 384

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "runtime": "onnxruntime",
            "active_provider": self._active_provider,
            "configured_provider": getattr(settings, "ai_execution_provider", "auto"),
            "fallback_occurred": self._fallback_occurred,
            "status_reason": self._status_reason,
            "dimension": self.dimension,
            "device": self.device,
            "precision": "float32",
        }

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
