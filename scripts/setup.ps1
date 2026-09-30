# AuraGuard — Automated Local Environment Setup Script
# Target: Windows (PowerShell)

[CmdletBinding()]
param (
    [switch]$SkipDeps = $false
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AuraGuard: Private AI Layer — System Setup" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $WorkspaceRoot

# 1. Verify Python
Write-Host "`n[1/8] Verifying Python installation..." -ForegroundColor Yellow
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Error "Python 3.10+ was not found on PATH. Please install Python and try again."
    exit 1
}
$PyVersion = python --version 2>&1
Write-Host "  Found: $PyVersion ($($PythonCmd.Source))" -ForegroundColor Green

# 2. Verify Node.js & npm
Write-Host "`n[2/8] Verifying Node.js & npm..." -ForegroundColor Yellow
$NodeCmd = Get-Command node -ErrorAction SilentlyContinue
$NpmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $NodeCmd -or -not $NpmCmd) {
    Write-Error "Node.js or npm was not found on PATH. Please install Node.js 18+ and try again."
    exit 1
}
$NodeVersion = node --version
$NpmVersion = npm --version
Write-Host "  Found Node: $NodeVersion, npm: $NpmVersion" -ForegroundColor Green

# 3. Create backend virtual environment if absent
Write-Host "`n[3/8] Checking backend virtual environment..." -ForegroundColor Yellow
$VenvDir = Join-Path $WorkspaceRoot "backend\.venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "  Creating virtual environment at backend\.venv..." -ForegroundColor Cyan
    python -m venv (Join-Path $WorkspaceRoot "backend\.venv")
    if (-not (Test-Path $VenvPython)) {
        Write-Error "Failed to initialize virtual environment."
        exit 1
    }
    Write-Host "  Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "  Virtual environment already exists at backend\.venv." -ForegroundColor Green
}

# 4. Install backend dependencies
if (-not $SkipDeps) {
    Write-Host "`n[4/8] Installing backend dependencies..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip --quiet
    $ReqFile = Join-Path $WorkspaceRoot "backend\requirements.txt"
    & $VenvPython -m pip install -r $ReqFile --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Backend dependency installation failed."
        exit 1
    }
    Write-Host "  Backend dependencies verified." -ForegroundColor Green
} else {
    Write-Host "`n[4/8] Skipping backend dependencies installation (-SkipDeps specified)." -ForegroundColor Gray
}

# 5. Install frontend dependencies
if (-not $SkipDeps) {
    Write-Host "`n[5/8] Installing frontend npm dependencies..." -ForegroundColor Yellow
    Push-Location (Join-Path $WorkspaceRoot "frontend")
    npm install --silent
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Error "Frontend npm install failed."
        exit 1
    }
    Pop-Location
    Write-Host "  Frontend dependencies installed." -ForegroundColor Green
} else {
    Write-Host "`n[5/8] Skipping frontend dependencies installation (-SkipDeps specified)." -ForegroundColor Gray
}

# 6. Validate required directories
Write-Host "`n[6/8] Validating storage & data directories..." -ForegroundColor Yellow
$Dirs = @(
    "data",
    "data\documents",
    "data\index",
    "models",
    "models\onnx",
    "benchmarks\results"
)
foreach ($d in $Dirs) {
    $p = Join-Path $WorkspaceRoot $d
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
        Write-Host "  Created directory: $d" -ForegroundColor Cyan
    }
}
Write-Host "  Data and directory structure verified." -ForegroundColor Green

# 7. Create .env from .env.example if absent
Write-Host "`n[7/8] Verifying configuration files..." -ForegroundColor Yellow
$EnvFile = Join-Path $WorkspaceRoot ".env"
$EnvExample = Join-Path $WorkspaceRoot ".env.example"
if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "  Created .env from .env.example." -ForegroundColor Cyan
} else {
    Write-Host "  Configuration file .env present." -ForegroundColor Green
}

# 8. Validate model availability
Write-Host "`n[8/8] Validating local neural model files..." -ForegroundColor Yellow
$OnnxInt8 = Join-Path $WorkspaceRoot "models\onnx\embedding_model_int8.onnx"
$OnnxFp32 = Join-Path $WorkspaceRoot "models\onnx\embedding_model.onnx"

if (Test-Path $OnnxInt8) {
    Write-Host "  [FOUND] Quantized INT8 Embedding Model: models\onnx\embedding_model_int8.onnx" -ForegroundColor Green
} elseif (Test-Path $OnnxFp32) {
    Write-Host "  [FOUND] FP32 Embedding Model: models\onnx\embedding_model.onnx" -ForegroundColor Green
} else {
    Write-Host "  [NOTICE] Local ONNX model files will load from cache or fallback on first startup." -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nNext steps to launch AuraGuard:"
Write-Host "  1. Run verification script:  powershell -ExecutionPolicy Bypass -File scripts\verify.ps1" -ForegroundColor White
Write-Host "  2. Start local stack:        powershell -ExecutionPolicy Bypass -File scripts\start.ps1" -ForegroundColor White
Write-Host "  3. Open browser:             http://localhost:5173" -ForegroundColor White
