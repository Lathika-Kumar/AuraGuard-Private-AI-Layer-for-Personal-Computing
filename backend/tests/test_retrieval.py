import numpy as np
import pytest
from app.services.retrieval_service import RetrievalService
from app.services.vector_service import FaissIndex
from app.core.config import settings


def test_faiss_index_metadata() -> None:
    index = FaissIndex(dim=384)
    meta = index.get_metadata()
    assert meta["embedding_dimension"] == 384
    assert meta["embedding_model"] == settings.embedding_model
    assert "created_at" in meta


def test_retrieval_service_initialization() -> None:
    retriever = RetrievalService()
    assert retriever.embedder.dimension == 384
    assert retriever.index.dim == 384


def test_rebuild_index_on_empty_db() -> None:
    retriever = RetrievalService()
    res = retriever.rebuild_index()
    assert res["status"] == "ok"
    assert "embedding_model" in res
