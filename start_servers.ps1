# Start Backend and Frontend Servers
# Usage: .\start_servers.ps1

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Core S3 Management System - Server Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot

# Start Backend
if (-not $FrontendOnly) {
    Write-Host ""
    Write-Host "[Backend] Starting..." -ForegroundColor Yellow
    
    $backendDir = Join-Path $projectRoot "backend"
    $backendVenv = Join-Path $backendDir "venv\Scripts\Activate.ps1"
    
    if (Test-Path $backendVenv) {
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "cd '$backendDir'; & '$backendVenv'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        )
        Write-Host "[Backend] Started at http://localhost:8000" -ForegroundColor Green
    } else {
        Write-Host "[Backend] Virtual environment not found at $backendVenv" -ForegroundColor Red
        Write-Host "         Run: cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
    }
}

# Start Frontend
if (-not $BackendOnly) {
    Write-Host ""
    Write-Host "[Frontend] Starting..." -ForegroundColor Yellow
    
    $frontendDir = Join-Path $projectRoot "frontend"
    
    if (Test-Path (Join-Path $frontendDir "node_modules")) {
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "cd '$frontendDir'; npm run dev"
        )
        Write-Host "[Frontend] Started at http://localhost:3000" -ForegroundColor Green
    } else {
        Write-Host "[Frontend] node_modules not found" -ForegroundColor Red
        Write-Host "         Run: cd frontend; npm install" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Servers starting in new windows..." -ForegroundColor Cyan
Write-Host ""
Write-Host "To run integration tests:" -ForegroundColor Yellow
Write-Host "  python tests\integration_test.py" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
