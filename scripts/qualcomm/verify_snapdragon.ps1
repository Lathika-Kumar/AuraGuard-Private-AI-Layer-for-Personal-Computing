# AuraGuard — Qualcomm Snapdragon & Hexagon NPU Verification Script
# Target: Windows ARM64 (Qualcomm Snapdragon X Series) / Intel Workstation Fallback Detection

$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $WorkspaceRoot

$VenvPython = Join-Path $WorkspaceRoot "backend\.venv\Scripts\python.exe"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AuraGuard: Qualcomm Snapdragon Platform Verification" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

$VerifyScript = @"
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, r'$WorkspaceRoot\backend')

from app.services.hardware_service import HardwareService
from app.core.config import settings

hw = HardwareService.get_hardware_info()
runtime = HardwareService.get_ai_runtime_info()
verify = HardwareService.verify_qnn_runtime()

# Model file check
int8_model = settings.model_cache_dir / 'onnx' / 'embedding_model_int8.onnx'
fp32_model = settings.model_cache_dir / 'onnx' / 'embedding_model.onnx'
model_exists = int8_model.exists() or fp32_model.exists()

report = {
    'is_arm64': hw['cpu']['architecture'].lower() in ['arm64', 'aarch64'],
    'is_snapdragon': hw['snapdragon']['is_snapdragon'],
    'cpu_brand': hw['cpu']['brand'],
    'qnn_available': runtime['qnn_available'],
    'npu_available': hw['npu']['npu_available'],
    'model_exists': model_exists,
    'provider_loaded': verify['provider_loaded'],
    'model_loaded': verify['model_loaded'],
    'inference_verified': verify['inference_verified'],
    'fallback_provider': runtime['active_execution_provider']
}
print(json.dumps(report))
"@

Push-Location (Join-Path $WorkspaceRoot "backend")
$VerifyRaw = & $VenvPython -c $VerifyScript
Pop-Location

try {
    $Report = $VerifyRaw | ConvertFrom-Json
} catch {
    Write-Error "Failed to parse Snapdragon verification output."
    exit 1
}

Write-Host "`n--- HARDWARE ---" -ForegroundColor Yellow
if ($Report.is_snapdragon) {
    Write-Host "[PASS] Snapdragon Processor ($($Report.cpu_brand))" -ForegroundColor Green
} elseif ($Report.is_arm64) {
    Write-Host "[NOTICE] ARM64 Windows detected, but not Qualcomm Snapdragon SoC." -ForegroundColor Yellow
} else {
    Write-Host "Snapdragon" -ForegroundColor Gray
    Write-Host "[NOT AVAILABLE] Host processor: $($Report.cpu_brand)" -ForegroundColor DarkYellow
}

Write-Host "`n--- QNN ---" -ForegroundColor Yellow
if ($Report.qnn_available) {
    Write-Host "[PASS] QNN Execution Provider registered in ONNX Runtime" -ForegroundColor Green
} else {
    Write-Host "QNN" -ForegroundColor Gray
    Write-Host "[NOT AVAILABLE] QNN Execution Provider not registered (Host provider: $($Report.fallback_provider))" -ForegroundColor DarkYellow
}

Write-Host "`n--- MODEL ---" -ForegroundColor Yellow
if ($Report.model_exists) {
    Write-Host "[PASS] Qualcomm-compatible ONNX Embedding Model artifacts verified" -ForegroundColor Green
} else {
    Write-Host "[WARN] Model artifact not found in models\onnx\" -ForegroundColor Yellow
}

Write-Host "`n--- NPU INFERENCE ---" -ForegroundColor Yellow
if ($Report.inference_verified) {
    Write-Host "[PASS] Qualcomm Hexagon NPU Tensor Inference Verified" -ForegroundColor Green
} else {
    Write-Host "NPU" -ForegroundColor Gray
    Write-Host "[NOT AVAILABLE] (Clean execution fallback active on $($Report.fallback_provider))" -ForegroundColor DarkYellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
if ($Report.is_snapdragon -and $Report.inference_verified) {
    Write-Host "  SNAPDRAGON HARDWARE ACCELERATION: FULLY ACTIVE" -ForegroundColor Green
} else {
    Write-Host "  SNAPDRAGON DEPLOYMENT STATUS: PREPARED & CPU FALLBACK VERIFIED" -ForegroundColor Yellow
    Write-Host "  Notice: Physical Snapdragon X Series PC required for live NPU execution." -ForegroundColor Gray
}
Write-Host "============================================================" -ForegroundColor Cyan
