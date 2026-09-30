# AuraGuard: Qualcomm Snapdragon & Host Benchmark Automation Suite
# Executes all reproducible benchmarks and generates docs/snapdragon-benchmark-final.md

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AuraGuard: Full Subsystem & Accelerator Benchmark Suite" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Hardware & Platform Introspection
Write-Host "`n[1/6] Hardware Detection & QNN Verification..." -ForegroundColor Yellow
& $Python -c "
import sys; sys.path.insert(0, 'backend')
from app.services.hardware_service import HardwareService
hw = HardwareService.get_hardware_info()
qnn = HardwareService.verify_qnn_runtime()
print(f'Host CPU:     {hw[\"cpu\"][\"brand\"]} ({hw[\"cpu\"][\"architecture\"]})')
print(f'Snapdragon:   {\"DETECTED\" if hw[\"snapdragon\"][\"is_snapdragon\"] else \"NOT DETECTED\"}')
print(f'QNN Provider: {\"AVAILABLE\" if qnn[\"qnn_available\"] else \"NOT AVAILABLE\"}')
print(f'Active Fallback: {qnn[\"active_fallback\"]}')
"

# 2. Validate Artifacts
Write-Host "`n[2/6] Validating Model Artifacts..." -ForegroundColor Yellow
& $Python (Join-Path $Root "scripts\qualcomm\validate_artifacts.py")

# 3. Run Microbenchmarks
Write-Host "`n[3/6] Running Encryption Benchmark..." -ForegroundColor Yellow
& $Python (Join-Path $Root "scripts\benchmark\benchmark_encryption.py")

Write-Host "`n[4/6] Running Embedding Benchmark..." -ForegroundColor Yellow
& $Python (Join-Path $Root "scripts\benchmark\benchmark_embedding.py")

Write-Host "`n[5/6] Running ReMind Memory Benchmark..." -ForegroundColor Yellow
& $Python (Join-Path $Root "scripts\benchmark\benchmark_memory.py")

Write-Host "`n[6/6] Running LLM & RAG End-to-End Benchmarks..." -ForegroundColor Yellow
& $Python (Join-Path $Root "scripts\benchmark\benchmark_llm.py")
& $Python (Join-Path $Root "scripts\benchmark\benchmark_rag.py")

# 4. Generate Final Comparative Markdown Report
Write-Host "`nGenerating Final Benchmark Summary: docs/snapdragon-benchmark-final.md..." -ForegroundColor Green
& $Python (Join-Path $Root "scripts\qualcomm\generate_final_report.py")

Write-Host "`nAll benchmarks completed successfully." -ForegroundColor Cyan
