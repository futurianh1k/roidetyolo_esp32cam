# ESP-IDF Build Environment Check Script
# Usage: .\check_build_env.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "ESP-IDF Build Environment Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0

# 1. Check ESP-IDF path
Write-Host "[1] ESP-IDF Path Check" -ForegroundColor Yellow
$idfPath = $env:IDF_PATH
if ($idfPath) {
    Write-Host "   OK: IDF_PATH: $idfPath" -ForegroundColor Green
    if (-not (Test-Path $idfPath)) {
        Write-Host "   ERROR: Path does not exist" -ForegroundColor Red
        $errors++
    }
} else {
    Write-Host "   ERROR: IDF_PATH environment variable not set" -ForegroundColor Red
    Write-Host "   TIP: Run ESP-IDF export script" -ForegroundColor Yellow
    $errors++
}

# 2. Check Python
Write-Host ""
Write-Host "[2] Python Check" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   OK: $pythonVersion" -ForegroundColor Green
    
    # Check Python version (3.8+ required)
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-Host "   WARNING: Python 3.8+ required (current: $major.$minor)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ERROR: Python not found" -ForegroundColor Red
    $errors++
}

# 3. Check idf.py
Write-Host ""
Write-Host "[3] idf.py Check" -ForegroundColor Yellow
try {
    $idfVersion = idf.py --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK: ESP-IDF Version:" -ForegroundColor Green
        Write-Host "      $idfVersion" -ForegroundColor Cyan
    } else {
        Write-Host "   ERROR: Cannot run idf.py" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   ERROR: idf.py not found" -ForegroundColor Red
    Write-Host "   TIP: Run ESP-IDF export script" -ForegroundColor Yellow
    $errors++
}

# 4. Check project files
Write-Host ""
Write-Host "[4] Project Files Check" -ForegroundColor Yellow
$requiredFiles = @(
    "CMakeLists.txt",
    "main\CMakeLists.txt",
    "main\main.cc",
    "main\application.cc",
    "main\application.h"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   OK: $file" -ForegroundColor Green
    } else {
        Write-Host "   ERROR: $file (missing)" -ForegroundColor Red
        $errors++
    }
}

# 5. Check components
Write-Host ""
Write-Host "[5] Components Check" -ForegroundColor Yellow
$componentFiles = @(
    "main\idf_component.yml",
    "main\audio\audio_codec.h",
    "main\audio\audio_service.h",
    "main\camera\camera_service.h",
    "main\network\wifi_manager.h",
    "main\network\mqtt_client.h"
)

foreach ($file in $componentFiles) {
    if (Test-Path $file) {
        Write-Host "   OK: $file" -ForegroundColor Green
    } else {
        Write-Host "   WARNING: $file (optional)" -ForegroundColor Yellow
    }
}

# Result
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "OK: Build environment ready" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Build: .\build.ps1" -ForegroundColor Cyan
    Write-Host "2. Flash: .\build.ps1 -Flash -Port COM3" -ForegroundColor Cyan
    Write-Host "3. Monitor: .\build.ps1 -Monitor -Port COM3" -ForegroundColor Cyan
} else {
    Write-Host "ERROR: Build environment has issues ($errors errors)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solutions:" -ForegroundColor Yellow
    Write-Host "1. Check ESP-IDF installation" -ForegroundColor Cyan
    Write-Host "2. Run ESP-IDF export script:" -ForegroundColor Cyan
    Write-Host "   C:\Espressif\frameworks\esp-idf-v5.4\export.ps1" -ForegroundColor Gray
    Write-Host "3. Check missing files" -ForegroundColor Cyan
}
Write-Host "============================================================" -ForegroundColor Cyan

exit $errors
