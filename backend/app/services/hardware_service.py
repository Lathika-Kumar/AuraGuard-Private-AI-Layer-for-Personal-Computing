from __future__ import annotations

import os
import platform
import subprocess
from typing import Any
import psutil

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from app.core.config import settings


class HardwareService:
    """Intelligent hardware and AI runtime detection service.
    
    Identifies host architecture, CPU, GPU, memory, Snapdragon processor presence,
    Qualcomm Hexagon NPU availability, and available ONNX Runtime execution providers.
    Provides automatic fallback to CPU when NPU/QNN is unavailable.
    """

    _cached_cpu_name: str | None = None
    _cached_gpu_name: str | None = None

    @classmethod
    def get_cpu_brand(cls) -> str:
        """Retrieves human-readable CPU brand name."""
        if cls._cached_cpu_name is not None:
            return cls._cached_cpu_name

        cpu_name = platform.processor() or "Unknown CPU"
        if platform.system() == "Windows":
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0 and res.stdout.strip():
                    cpu_name = res.stdout.strip().splitlines()[0]
            except Exception:
                pass
        cls._cached_cpu_name = cpu_name
        return cpu_name

    @classmethod
    def get_gpu_brand(cls) -> str:
        """Retrieves human-readable GPU name."""
        if cls._cached_gpu_name is not None:
            return cls._cached_gpu_name

        gpu_name = "Not Detected / Integrated"
        if platform.system() == "Windows":
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0 and res.stdout.strip():
                    gpu_name = ", ".join([line.strip() for line in res.stdout.strip().splitlines() if line.strip()])
            except Exception:
                pass
        cls._cached_gpu_name = gpu_name
        return gpu_name

    @classmethod
    def is_snapdragon(cls) -> bool:
        """Checks if the current system is running on a Qualcomm Snapdragon processor."""
        machine = platform.machine().lower()
        cpu_name = cls.get_cpu_brand().lower()
        
        # Check architecture and processor branding
        is_arm = machine in ("arm64", "aarch64")
        has_snapdragon_brand = any(
            token in cpu_name for token in ["snapdragon", "qualcomm", "sc8380xp", "x elite", "x plus"]
        )
        return is_arm and has_snapdragon_brand

    @classmethod
    def is_npu_available(cls) -> bool:
        """Checks if a Qualcomm Hexagon NPU or hardware NPU is actively available."""
        # Check if QNN Execution Provider is registered in ONNX Runtime
        providers = cls.get_available_execution_providers()
        if "QNNExecutionProvider" in providers:
            return True

        # Check Windows PNP / CIM instances for Hexagon NPU if on Windows
        if platform.system() == "Windows":
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-PnpDevice -Class 'ComputeAccelerator' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FriendlyName"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0 and "Hexagon" in res.stdout:
                    return True
            except Exception:
                pass

        return False

    @classmethod
    def get_available_execution_providers(cls) -> list[str]:
        """Returns the list of execution providers available in ONNX Runtime."""
        if ort is not None:
            try:
                return ort.get_available_providers()
            except Exception:
                return ["CPUExecutionProvider"]
        return ["CPUExecutionProvider"]

    @classmethod
    def resolve_execution_provider(cls, preferred: str | None = None) -> tuple[str, str, bool]:
        """Resolves active execution provider with automatic CPU fallback.
        
        Returns:
            (active_provider, status_reason, fallback_occurred)
        """
        target = (preferred or getattr(settings, "ai_execution_provider", "auto")).lower()
        available = cls.get_available_execution_providers()

        if target == "qnn":
            if "QNNExecutionProvider" in available:
                return "QNNExecutionProvider", "Qualcomm QNN Execution Provider active.", False
            else:
                return (
                    "CPUExecutionProvider",
                    "QNN requested but QNNExecutionProvider is unavailable on this hardware. Fallback to CPUExecutionProvider.",
                    True,
                )
        elif target == "auto":
            if "QNNExecutionProvider" in available:
                return "QNNExecutionProvider", "Snapdragon QNN hardware acceleration detected and active.", False
            else:
                return (
                    "CPUExecutionProvider",
                    "Snapdragon NPU/QNN not detected. Defaulting to optimized CPUExecutionProvider.",
                    False,
                )
        else:
            return "CPUExecutionProvider", "CPU execution explicitly configured.", False

    @classmethod
    def get_hardware_info(cls) -> dict[str, Any]:
        """Collects complete host system hardware specifications."""
        vm = psutil.virtual_memory()
        cpu_brand = cls.get_cpu_brand()
        is_sd = cls.is_snapdragon()
        is_npu = cls.is_npu_available()

        return {
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "platform": platform.platform(),
            },
            "cpu": {
                "brand": cpu_brand,
                "architecture": platform.machine(),
                "physical_cores": psutil.cpu_count(logical=False) or 1,
                "logical_cores": psutil.cpu_count(logical=True) or 1,
            },
            "gpu": {
                "name": cls.get_gpu_brand(),
            },
            "memory": {
                "total_bytes": vm.total,
                "total_gb": round(vm.total / (1024 ** 3), 2),
                "available_bytes": vm.available,
                "available_gb": round(vm.available / (1024 ** 3), 2),
                "percent_used": vm.percent,
            },
            "snapdragon": {
                "is_snapdragon": is_sd,
                "processor_detected": cpu_brand if is_sd else None,
                "target_device": "Snapdragon X Elite / HP OmniBook X" if is_sd else "Intel/AMD x86_64 Host",
            },
            "npu": {
                "npu_available": is_npu,
                "npu_type": "Qualcomm Hexagon NPU" if is_npu else "None",
                "acceleration_active": is_npu,
            },
        }

    @classmethod
    def get_ai_runtime_info(cls) -> dict[str, Any]:
        """Provides AI runtime status, models, execution providers, and fallback state."""
        hw = cls.get_hardware_info()
        available_providers = cls.get_available_execution_providers()
        active_provider, status_reason, fallback_occurred = cls.resolve_execution_provider()

        return {
            "runtime_status": "ready",
            "active_execution_provider": active_provider,
            "configured_execution_provider": getattr(settings, "ai_execution_provider", "auto"),
            "fallback_occurred": fallback_occurred,
            "status_reason": status_reason,
            "available_execution_providers": available_providers,
            "qnn_available": "QNNExecutionProvider" in available_providers,
            "snapdragon_hardware": hw["snapdragon"]["is_snapdragon"],
            "npu_available": hw["npu"]["npu_available"],
            "models": {
                "embedding": {
                    "model_name": settings.embedding_model,
                    "runtime": "onnxruntime",
                    "execution_provider": active_provider,
                    "dimension": 384,
                    "precision": "float32",
                    "device": settings.embedding_device,
                },
                "llm": {
                    "model_id": settings.llm_model,
                    "runtime": "pytorch",
                    "execution_provider": "CPU" if active_provider == "CPUExecutionProvider" else active_provider,
                    "device": settings.llm_device,
                    "precision": "float32",
                    "max_new_tokens": settings.llm_max_new_tokens,
                },
            },
            "qualcomm_ai_hub": {
                "target_architecture": "Qualcomm Hexagon NPU / Snapdragon X Elite",
                "toolchain": "Qualcomm AI Hub SDK / QNN SDK",
                "compilation_targets": ["snapdragon_x_elite", "snapdragon_x_plus"],
                "status": "ready_for_export",
            },
        }

    @classmethod
    def get_models_info(cls) -> dict[str, Any]:
        """Provides model metadata for GET /api/system/models directly from runtime configuration."""
        active_provider, _, _ = cls.resolve_execution_provider()
        emb_prec = getattr(settings, "embedding_precision", "auto")
        if emb_prec == "auto":
            emb_prec = "float32"
        llm_prec = getattr(settings, "llm_precision", "auto")
        if llm_prec == "auto":
            llm_prec = "float32"

        return {
            "embedding": {
                "name": settings.embedding_model,
                "runtime": "onnxruntime",
                "precision": emb_prec,
                "provider": active_provider,
            },
            "llm": {
                "name": settings.llm_model,
                "runtime": "pytorch",
                "precision": llm_prec,
                "provider": "CPU" if active_provider == "CPUExecutionProvider" else active_provider,
            },
        }
