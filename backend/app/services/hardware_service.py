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
    _cached_npu_available: bool | None = None

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
        """Checks if the current system is running on a Qualcomm Snapdragon processor.
        
        Requires ARM64 architecture AND explicit Qualcomm / Snapdragon processor indicators,
        distinguishing real Snapdragon hardware from generic ARM64 or Apple Silicon virtual machines.
        """
        machine = platform.machine().lower()
        is_arm = machine in ("arm64", "aarch64")
        if not is_arm:
            return False

        cpu_name = cls.get_cpu_brand().lower()
        snapdragon_tokens = ["snapdragon", "qualcomm", "sc8380xp", "x elite", "x plus", "oryon", "kryo"]
        has_snapdragon_brand = any(token in cpu_name for token in snapdragon_tokens)
        if has_snapdragon_brand:
            return True

        # Secondary registry check on Windows ARM64
        if platform.system() == "Windows":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                    proc_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                    vendor, _ = winreg.QueryValueEx(key, "VendorIdentifier")
                    combined = f"{proc_name} {vendor}".lower()
                    if any(t in combined for t in snapdragon_tokens):
                        # Explicitly exclude Apple Silicon or generic QEMU VMs
                        if not any(non_sd in combined for non_sd in ["apple", "virtualapple", "qemu", "kvm"]):
                            return True
            except Exception:
                pass

        return False

    @classmethod
    def is_npu_available(cls) -> bool:
        """Checks if a Qualcomm Hexagon NPU or hardware NPU is actively available."""
        if cls._cached_npu_available is not None:
            return cls._cached_npu_available

        # Check if QNN Execution Provider is registered in ONNX Runtime
        providers = cls.get_available_execution_providers()
        if "QNNExecutionProvider" in providers:
            cls._cached_npu_available = True
            return True

        # Check Windows PNP / CIM instances for Hexagon NPU only on Snapdragon / ARM64 Windows
        if platform.system() == "Windows" and cls.is_snapdragon():
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-PnpDevice -Class 'ComputeAccelerator' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FriendlyName"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0 and "Hexagon" in res.stdout:
                    cls._cached_npu_available = True
                    return True
            except Exception:
                pass

        cls._cached_npu_available = False
        return False

    @classmethod
    def verify_qnn_runtime(cls) -> dict[str, Any]:
        """Dedicated runtime verification for Qualcomm QNN and Snapdragon NPU execution.

        Performs actual check sequence:
        1. hardware_detected: true if host is verified Snapdragon SoC
        2. qnn_available: true if QNNExecutionProvider is present in ONNX Runtime
        3. provider_loaded: true if InferenceSession can be initialized with QNN
        4. model_loaded: true if ONNX model binary can be loaded into QNN session
        5. inference_verified: true if an actual tensor inference pass succeeds
        """
        import numpy as np
        hw_detected = cls.is_snapdragon()
        providers = cls.get_available_execution_providers()
        qnn_available = "QNNExecutionProvider" in providers

        # Check if QNN package or binaries are installed
        qnn_installed = False
        try:
            import importlib.util
            qnn_installed = (
                importlib.util.find_spec("onnxruntime_qnn") is not None
                or qnn_available
                or os.path.exists("C:\\Qualcomm\\AIStack")
                or bool(os.environ.get("QNN_SDK_ROOT"))
            )
        except Exception:
            qnn_installed = qnn_available

        provider_loaded = False
        model_loaded = False
        inference_verified = False
        error_reason = None

        if qnn_available and ort is not None:
            try:
                model_path = str(settings.model_cache_dir / "onnx" / "embedding_model_int8.onnx")
                if not os.path.exists(model_path):
                    model_path = str(settings.model_cache_dir / "onnx" / "embedding_model.onnx")

                if os.path.exists(model_path):
                    session_options = ort.SessionOptions()
                    session = ort.InferenceSession(model_path, session_options, providers=["QNNExecutionProvider"])
                    provider_loaded = True
                    model_loaded = True

                    # Run dummy inference pass
                    inputs = {session.get_inputs()[0].name: np.array([[101, 2054, 2003, 1037, 3231, 102]], dtype=np.int64)}
                    if len(session.get_inputs()) > 1:
                        inputs[session.get_inputs()[1].name] = np.array([[1, 1, 1, 1, 1, 1]], dtype=np.int64)
                    session.run(None, inputs)
                    inference_verified = True
            except Exception as ex:
                error_reason = str(ex)

        return {
            "hardware_detected": hw_detected,
            "qnn_installed": qnn_installed,
            "qnn_available": qnn_available,
            "provider_loaded": provider_loaded,
            "model_loaded": model_loaded,
            "inference_verified": inference_verified,
            "active_fallback": "CPUExecutionProvider" if not inference_verified else None,
            "error_reason": error_reason,
        }

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
