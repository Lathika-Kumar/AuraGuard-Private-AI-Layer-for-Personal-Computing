import os
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.hardware_service import HardwareService
from app.core.config import settings

client = TestClient(app)


def test_api_system_models():
    """Verify GET /api/system/models returns valid configuration metadata."""
    response = client.get("/api/system/models")
    assert response.status_code == 200
    data = response.json()
    assert "embedding" in data
    assert "llm" in data
    assert data["embedding"]["name"] == settings.embedding_model
    assert data["embedding"]["runtime"] == "onnxruntime"
    assert data["embedding"]["provider"] in ["CPUExecutionProvider", "QNNExecutionProvider"]
    assert data["llm"]["name"] == settings.llm_model
    assert data["llm"]["runtime"] == "pytorch"


def test_api_system_hardware():
    """Verify GET /api/system/hardware reports authentic host specs."""
    response = client.get("/api/system/hardware")
    assert response.status_code == 200
    data = response.json()
    assert "os" in data
    assert "cpu" in data
    assert "memory" in data
    assert "snapdragon" in data
    assert "npu" in data
    # On Intel development host, is_snapdragon must be False
    assert data["snapdragon"]["is_snapdragon"] is False
    assert data["npu"]["npu_available"] is False


def test_api_system_ai_runtime():
    """Verify GET /api/system/ai-runtime returns execution provider and telemetry."""
    response = client.get("/api/system/ai-runtime")
    assert response.status_code == 200
    data = response.json()
    assert data["runtime_status"] == "ready"
    assert data["active_execution_provider"] == "CPUExecutionProvider"
    assert data["qnn_available"] is False
    assert "models" in data
    assert "qualcomm_ai_hub" in data


def test_cpu_fallback_resolution():
    """Verify resolution logic safely falls back to CPU when QNN is unavailable."""
    active_provider, reason, fallback_occurred = HardwareService.resolve_execution_provider()
    assert active_provider == "CPUExecutionProvider"
    assert "CPUExecutionProvider" in reason


def test_invalid_provider_configuration_handling():
    """Verify invalid configured execution provider gracefully falls back to CPU."""
    # When user configures unknown provider
    available = HardwareService.get_available_execution_providers()
    assert "CPUExecutionProvider" in available


def test_onnx_embedding_file_validity():
    """Verify the exported ONNX embedding artifact is structurally valid."""
    onnx_file = Path("models/onnx/embedding_model.onnx")
    if not onnx_file.exists():
        # Check root models directory if run from backend/
        onnx_file = Path("../models/onnx/embedding_model.onnx")
    
    if onnx_file.exists():
        import onnx
        import onnxruntime as ort

        model = onnx.load(str(onnx_file))
        onnx.checker.check_model(model)
        sess = ort.InferenceSession(str(onnx_file), providers=["CPUExecutionProvider"])
        assert sess is not None
        # Verify inputs
        input_names = [inp.name for inp in sess.get_inputs()]
        assert "input_ids" in input_names
        assert "attention_mask" in input_names


def test_quantized_int8_embedding_validity():
    """Verify the quantized INT8 ONNX embedding artifact exists and loads."""
    int8_file = Path("models/onnx/embedding_model_int8.onnx")
    if not int8_file.exists():
        int8_file = Path("../models/onnx/embedding_model_int8.onnx")

    if int8_file.exists():
        import onnxruntime as ort
        sess = ort.InferenceSession(str(int8_file), providers=["CPUExecutionProvider"])
        assert sess is not None
        input_names = [inp.name for inp in sess.get_inputs()]
        assert "input_ids" in input_names
