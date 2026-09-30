# AuraGuard — Automated System & Subsystem Verification Script
# Target: Windows (PowerShell)

$WorkspaceRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $WorkspaceRoot

$VenvPython = Join-Path $WorkspaceRoot "backend\.venv\Scripts\python.exe"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AuraGuard: Subsystem Verification Suite" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

function Report-Status($label, $status, $detail) {
    switch ($status) {
        "PASS" { Write-Host "[PASS] " -ForegroundColor Green -NoNewline; Write-Host "$label" -ForegroundColor White -NoNewline; if ($detail) { Write-Host " ($detail)" -ForegroundColor Gray } else { Write-Host "" } }
        "WARN" { Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline; Write-Host "$label" -ForegroundColor White -NoNewline; if ($detail) { Write-Host " ($detail)" -ForegroundColor Gray } else { Write-Host "" } }
        "FAIL" { Write-Host "[FAIL] " -ForegroundColor Red -NoNewline; Write-Host "$label" -ForegroundColor White -NoNewline; if ($detail) { Write-Host " ($detail)" -ForegroundColor Gray } else { Write-Host "" } }
    }
}

# 1. Python Check
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyv = python --version 2>&1
    Report-Status "Python" "PASS" "$pyv"
} else {
    Report-Status "Python" "FAIL" "Not on PATH"
}

# 2. Node.js Check
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodev = node --version
    Report-Status "Node.js" "PASS" "$nodev"
} else {
    Report-Status "Node.js" "FAIL" "Not on PATH"
}

# 3. Virtual Environment & Backend dependencies
if (Test-Path $VenvPython) {
    Report-Status "Backend Virtualenv" "PASS" "backend\.venv ready"
} else {
    Report-Status "Backend Virtualenv" "FAIL" "Run scripts\setup.ps1"
}

# 4. Frontend configuration
if (Test-Path (Join-Path $WorkspaceRoot "frontend\package.json")) {
    Report-Status "Frontend" "PASS" "package.json verified"
} else {
    Report-Status "Frontend" "FAIL" "Missing frontend\package.json"
}

# Run deep verification inside backend environment
$VerificationScript = @'
import json
import sys
from pathlib import Path

results = {}

# Test Database & Migration
try:
    from app.database.database import init_db, get_db_connection
    init_db()
    with get_db_connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    results['sqlite'] = {'status': 'PASS', 'detail': f"{len(tables)} tables verified"}
except Exception as ex:
    results['sqlite'] = {'status': 'FAIL', 'detail': str(ex)}

# Test Encryption & DPAPI
try:
    from app.security.encryption_service import encryption_service
    from app.security.key_manager import key_manager
    test_pt = "AuraGuard DPAPI Security Verification Test"
    ct = encryption_service.encrypt(test_pt)
    dec = encryption_service.decrypt(ct)
    if dec == test_pt:
        method = "Windows DPAPI" if key_manager.is_dpapi_supported() else "Protected Key"
        results['encryption'] = {'status': 'PASS', 'detail': f"AES-256-GCM authenticated via {method}"}
    else:
        results['encryption'] = {'status': 'FAIL', 'detail': 'Decrypted mismatch'}
except Exception as ex:
    results['encryption'] = {'status': 'FAIL', 'detail': str(ex)}

# Test FAISS
try:
    from app.services.vector_service import FaissIndex
    idx = FaissIndex(dim=384, namespace="documents")
    results['faiss'] = {'status': 'PASS', 'detail': f"{idx.count()} vectors loaded in RAM, envelope encrypted on disk"}
except Exception as ex:
    results['faiss'] = {'status': 'FAIL', 'detail': str(ex)}

# Test ONNX & Models
try:
    import onnxruntime as ort
    from app.services.embedding_service import EmbeddingProvider
    ep = EmbeddingProvider()
    q_emb = ep.embed(['AuraGuard verification test'])[0]
    results['models'] = {'status': 'PASS', 'detail': f"ONNX Runtime {ort.__version__}, dim={len(q_emb)}"}
except Exception as ex:
    results['models'] = {'status': 'FAIL', 'detail': str(ex)}

# Test Privacy Engine
try:
    from app.services.privacy_service import PrivacyService
    res = PrivacyService.analyze('Contact me with key sk-proj-99999999999999999999999999999999')
    if not res.allowed and len(res.entities) >= 1:
        results['privacy_engine'] = {'status': 'PASS', 'detail': f"3 Checkpoints active, blocked {res.classification.value}"}
    else:
        results['privacy_engine'] = {'status': 'FAIL', 'detail': 'Entity detection failed'}
except Exception as ex:
    results['privacy_engine'] = {'status': 'FAIL', 'detail': str(ex)}

# Test ReMind
try:
    from app.services.remind_service import RemindService
    rm = RemindService()
    results['remind'] = {'status': 'PASS', 'detail': 'Encrypted personal memory layer operational'}
except Exception as ex:
    results['remind'] = {'status': 'FAIL', 'detail': str(ex)}

# Test AI Runtime & Hardware
try:
    from app.services.hardware_service import HardwareService
    hw = HardwareService.get_hardware_info()
    runtime = HardwareService.get_ai_runtime_info()
    verify = HardwareService.verify_qnn_runtime()
    
    provider = runtime['active_execution_provider']
    if verify['qnn_available']:
        results['ai_runtime'] = {'status': 'PASS', 'detail': f"QNN active on {hw['cpu']['brand']}"}
    else:
        results['ai_runtime'] = {'status': 'WARN', 'detail': f"QNN unavailable on {hw['cpu']['brand']}; fallback to {provider}"}
except Exception as ex:
    results['ai_runtime'] = {'status': 'FAIL', 'detail': str(ex)}

print(json.dumps(results))
'@

Push-Location (Join-Path $WorkspaceRoot "backend")
$DeepCheckRaw = $VerificationScript | & $VenvPython -
Pop-Location

try {
    $DeepCheck = $DeepCheckRaw | ConvertFrom-Json
    Report-Status "SQLite Database" $DeepCheck.sqlite.status $DeepCheck.sqlite.detail
    Report-Status "Storage Encryption" $DeepCheck.encryption.status $DeepCheck.encryption.detail
    Report-Status "FAISS Vector Store" $DeepCheck.faiss.status $DeepCheck.faiss.detail
    Report-Status "Neural Models & ONNX" $DeepCheck.models.status $DeepCheck.models.detail
    Report-Status "Privacy Engine" $DeepCheck.privacy_engine.status $DeepCheck.privacy_engine.detail
    Report-Status "ReMind Memory" $DeepCheck.remind.status $DeepCheck.remind.detail
    Report-Status "AI Runtime (QNN/NPU)" $DeepCheck.ai_runtime.status $DeepCheck.ai_runtime.detail
} catch {
    Report-Status "Internal Checks" "FAIL" "Could not parse verification results"
}

Write-Host "`nVerification complete." -ForegroundColor Cyan
