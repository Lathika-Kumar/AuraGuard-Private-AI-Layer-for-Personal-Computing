# AuraGuard — Automated Local Process Startup Script
# Target: Windows (PowerShell)

[CmdletBinding()]
param (
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $WorkspaceRoot

$VenvPython = Join-Path $WorkspaceRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found. Please run scripts\setup.ps1 first."
    exit 1
}

# 1. Empirically query detected hardware & runtime
Write-Host "Detecting local hardware and runtime provider..." -ForegroundColor Gray
$DetectorCode = @"
import json
from app.services.hardware_service import HardwareService
hw = HardwareService.get_hardware_info()
runtime = HardwareService.get_ai_runtime_info()
print(json.dumps({
    'cpu_brand': hw['cpu']['brand'],
    'is_snapdragon': hw['snapdragon']['is_snapdragon'],
    'npu_available': hw['npu']['npu_available'],
    'qnn_available': runtime['qnn_available'],
    'provider': runtime['active_execution_provider']
}))
"@

Push-Location (Join-Path $WorkspaceRoot "backend")
$RuntimeRaw = & $VenvPython -c $DetectorCode
Pop-Location

try {
    $Runtime = $RuntimeRaw | ConvertFrom-Json
    $HardwareDisplay = if ($Runtime.is_snapdragon) { "Snapdragon X Elite ($($Runtime.cpu_brand))" } else { "$($Runtime.cpu_brand)" }
    $ProviderDisplay = $Runtime.provider
} catch {
    $HardwareDisplay = "Detected Local CPU"
    $ProviderDisplay = "CPUExecutionProvider"
}

# 2. Launch FastAPI Backend
Write-Host "`nStarting FastAPI backend server on port $BackendPort..." -ForegroundColor Cyan
$BackendProcess = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort" `
    -WorkingDirectory (Join-Path $WorkspaceRoot "backend") `
    -PassThru

# 3. Launch React Frontend
Write-Host "Starting React frontend on port $FrontendPort..." -ForegroundColor Cyan
$FrontendProcess = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev -- --port $FrontendPort" `
    -WorkingDirectory (Join-Path $WorkspaceRoot "frontend") `
    -PassThru

Start-Sleep -Seconds 2

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  AuraGuard started" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nBackend:     http://127.0.0.1:$BackendPort" -ForegroundColor White
Write-Host "Frontend:    http://127.0.0.1:$FrontendPort" -ForegroundColor White
Write-Host "`nHardware:`n$HardwareDisplay" -ForegroundColor Yellow
Write-Host "`nAI Provider:`n$ProviderDisplay" -ForegroundColor Yellow
Write-Host "`nBackend PID:  $($BackendProcess.Id)" -ForegroundColor Gray
Write-Host "Frontend PID: $($FrontendProcess.Id)" -ForegroundColor Gray
Write-Host "`nPress Ctrl+C to terminate processes when finished." -ForegroundColor Gray
