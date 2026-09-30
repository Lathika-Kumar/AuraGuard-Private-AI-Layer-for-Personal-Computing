from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app
from app.services.hardware_service import HardwareService
from app.services.embedding_service import EmbeddingProvider
from app.services.ai_service import AIProvider


def test_hardware_detection() -> None:
    hw = HardwareService.get_hardware_info()
    assert "os" in hw
    assert "cpu" in hw
    assert "gpu" in hw
    assert "memory" in hw
    assert "snapdragon" in hw
    assert "npu" in hw

    assert isinstance(hw["snapdragon"]["is_snapdragon"], bool)
    assert isinstance(hw["npu"]["npu_available"], bool)
    assert hw["memory"]["total_gb"] > 0


def test_ai_runtime_detection() -> None:
    runtime = HardwareService.get_ai_runtime_info()
    assert runtime["runtime_status"] == "ready"
    assert "active_execution_provider" in runtime
    assert "available_execution_providers" in runtime
    assert "models" in runtime
    assert "embedding" in runtime["models"]
    assert "llm" in runtime["models"]
    assert "qualcomm_ai_hub" in runtime


def test_provider_resolution_explicit_cpu() -> None:
    provider, reason, fallback = HardwareService.resolve_execution_provider(preferred="cpu")
    assert provider == "CPUExecutionProvider"
    assert fallback is False


def test_provider_resolution_qnn_fallback_or_active() -> None:
    provider, reason, fallback = HardwareService.resolve_execution_provider(preferred="qnn")
    available = HardwareService.get_available_execution_providers()
    if "QNNExecutionProvider" in available:
        assert provider == "QNNExecutionProvider"
        assert fallback is False
    else:
        assert provider == "CPUExecutionProvider"
        assert fallback is True
        assert "QNN requested but QNNExecutionProvider is unavailable" in reason


def test_provider_resolution_auto() -> None:
    provider, reason, fallback = HardwareService.resolve_execution_provider(preferred="auto")
    available = HardwareService.get_available_execution_providers()
    if "QNNExecutionProvider" in available:
        assert provider == "QNNExecutionProvider"
    else:
        assert provider == "CPUExecutionProvider"
    assert fallback is False


def test_system_hardware_api_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/system/hardware")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "snapdragon" in data
    assert "npu" in data


def test_system_ai_runtime_api_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/system/ai-runtime")
    assert response.status_code == 200
    data = response.json()
    assert data["runtime_status"] == "ready"
    assert "active_execution_provider" in data
    assert "models" in data


def test_system_ai_runtime_verify_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/system/ai-runtime/verify")
    assert response.status_code == 200
    data = response.json()
    assert "hardware_detected" in data
    assert "qnn_available" in data
    assert "provider_loaded" in data
    assert "model_loaded" in data
    assert "inference_verified" in data
    # On Intel dev environment, qnn_available is False, so inference_verified must be False
    if not data["qnn_available"]:
        assert data["inference_verified"] is False
        assert data["provider_loaded"] is False


def test_embedding_metadata_property() -> None:
    provider = EmbeddingProvider()
    meta = provider.metadata
    assert meta["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert meta["dimension"] == 384
    assert meta["runtime"] == "onnxruntime"
    assert "active_provider" in meta


def test_llm_metadata_property() -> None:
    llm = AIProvider()
    meta = llm.metadata
    assert "Qwen" in meta["model_id"]
    assert meta["runtime"] == "pytorch"
    assert "active_provider" in meta
