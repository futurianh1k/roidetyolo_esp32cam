# ESP-IDF Build Script
# Usage: 
#   .\build.ps1                              # Build OTA version (default)
#   .\build.ps1 -BuildType ota               # Build OTA version
#   .\build.ps1 -BuildType single            # Build Single App version (no OTA)
#   .\build.ps1 -Flash -Port COM5            # Build and flash
#   .\build.ps1 -Flash -Monitor -Port COM5   # Build, flash and monitor
#   .\build.ps1 -Clean -Flash -Port COM5     # Clean build and flash
#   .\build.ps1 -CleanComponents -Clean      # Clean managed_components and rebuild

param(
    [string]$IdfPath = "",
    [ValidateSet("esp32", "esp32s2", "esp32s3", "esp32c3", "esp32c6")]
    [string]$Target = "esp32s3",
    [string]$Port = "",
    [ValidateSet("ota", "single")]
    [string]$BuildType = "ota",
    [switch]$Flash = $false,
    [switch]$Monitor = $false,
    [switch]$Clean = $false,
    [switch]$CleanComponents = $false
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "ESP-IDF Build Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Display build type
if ($BuildType -eq "ota") {
    Write-Host "[BUILD TYPE] OTA Version (Dual partition, 4MB each)" -ForegroundColor Green
}
else {
    Write-Host "[BUILD TYPE] Single App Version (6MB app partition, no OTA)" -ForegroundColor Yellow
}
Write-Host ""

# ESP-IDF path finding
if ([string]::IsNullOrEmpty($IdfPath)) {
    if ($env:IDF_PATH -and (Test-Path $env:IDF_PATH)) {
        $IdfPath = $env:IDF_PATH
        Write-Host "[INFO] Using IDF_PATH: $IdfPath" -ForegroundColor Cyan
    }
    elseif (Test-Path "E:\esp32\Espressif\frameworks\esp-idf-v5.5.1") {
        $IdfPath = "E:\esp32\Espressif\frameworks\esp-idf-v5.5.1"
    }
    elseif (Test-Path "E:\esp32\Espressif\frameworks\esp-idf-v5.5") {
        $IdfPath = "E:\esp32\Espressif\frameworks\esp-idf-v5.5"
    }
    elseif (Test-Path "E:\esp32\Espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "E:\esp32\Espressif\frameworks\esp-idf-v5.4"
    }
    elseif (Test-Path "C:\esp32\Espressif\frameworks\esp-idf-v5.5.1") {
        $IdfPath = "C:\esp32\Espressif\frameworks\esp-idf-v5.5.1"
    }
    elseif (Test-Path "C:\esp32\Espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "C:\esp32\Espressif\frameworks\esp-idf-v5.4"
    }
    elseif (Test-Path "C:\Espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "C:\Espressif\frameworks\esp-idf-v5.4"
    }
    elseif (Test-Path "$env:USERPROFILE\.espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "$env:USERPROFILE\.espressif\frameworks\esp-idf-v5.4"
    }
    else {
        Write-Host "ERROR: ESP-IDF path not found" -ForegroundColor Red
        Write-Host "Please specify ESP-IDF path: .\build.ps1 -IdfPath 'C:\path\to\esp-idf'" -ForegroundColor Yellow
        exit 1
    }
}

if (-not (Test-Path $IdfPath)) {
    Write-Host "ERROR: ESP-IDF path does not exist: $IdfPath" -ForegroundColor Red
    exit 1
}

# Setup ESP-IDF environment
Write-Host "[1] Setting up ESP-IDF environment..." -ForegroundColor Yellow
Write-Host "   ESP-IDF path: $IdfPath" -ForegroundColor Gray

$exportScript = Join-Path $IdfPath "export.ps1"
if (-not (Test-Path $exportScript)) {
    Write-Host "ERROR: export.ps1 not found in: $IdfPath" -ForegroundColor Red
    exit 1
}

Write-Host "   Found export.ps1: $exportScript" -ForegroundColor Gray
$ErrorActionPreference = "SilentlyContinue"
& $exportScript 2>&1 | Out-Null
$ErrorActionPreference = "Continue"

$idfPyCheck = Get-Command idf.py -ErrorAction SilentlyContinue
if (-not $idfPyCheck) {
    Write-Host "ERROR: ESP-IDF environment not properly set up" -ForegroundColor Red
    Write-Host "Please run: cd $IdfPath && .\install.bat esp32,esp32s3" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK: ESP-IDF environment setup complete" -ForegroundColor Green

# Project directory
Set-Location $PSScriptRoot
Write-Host ""
Write-Host "[2] Project directory: $PSScriptRoot" -ForegroundColor Yellow

# Clean managed_components if requested
$managedComponentsDir = Join-Path $PSScriptRoot "managed_components"
if ($CleanComponents -and (Test-Path $managedComponentsDir)) {
    Write-Host ""
    Write-Host "[3] Cleaning managed_components..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $managedComponentsDir -ErrorAction SilentlyContinue
    Write-Host "OK: managed_components removed (will be re-downloaded)" -ForegroundColor Green
}

# Clean build directory and sdkconfig if requested
$buildDir = Join-Path $PSScriptRoot "build"
$sdkconfigFile = Join-Path $PSScriptRoot "sdkconfig"
if ($Clean) {
    Write-Host ""
    Write-Host "[3] Cleaning build..." -ForegroundColor Yellow
    if (Test-Path $buildDir) {
        Remove-Item -Recurse -Force $buildDir -ErrorAction SilentlyContinue
        Write-Host "    - build directory removed" -ForegroundColor Gray
    }
    if (Test-Path $sdkconfigFile) {
        Remove-Item -Force $sdkconfigFile -ErrorAction SilentlyContinue
        Write-Host "    - sdkconfig removed (will regenerate from defaults)" -ForegroundColor Gray
    }
    Write-Host "OK: Clean complete" -ForegroundColor Green
}

# Configure build type (MUST be set before set-target)
# Reason: `idf.py set-target` will generate sdkconfig immediately.
# If SDKCONFIG_DEFAULTS isn't set yet, it will generate sdkconfig with wrong defaults
# (e.g., single-app partition table), causing build failures.
Write-Host ""
Write-Host "[4] Configuring build type..." -ForegroundColor Yellow
if ($BuildType -eq "ota") {
    Write-Host "    - Using: sdkconfig.defaults + sdkconfig.ota" -ForegroundColor Cyan
    $env:SDKCONFIG_DEFAULTS = "sdkconfig.defaults;sdkconfig.ota"
}
else {
    Write-Host "    - Using: sdkconfig.defaults + sdkconfig.singleapp" -ForegroundColor Cyan
    $env:SDKCONFIG_DEFAULTS = "sdkconfig.defaults;sdkconfig.singleapp"
}

# Set target (after SDKCONFIG_DEFAULTS is set)
Write-Host ""
Write-Host "[5] Setting target: $Target" -ForegroundColor Yellow
idf.py set-target $Target
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to set target" -ForegroundColor Red
    exit 1
}

# Build
Write-Host ""
Write-Host "[6] Building..." -ForegroundColor Yellow
Write-Host "   (This may take several minutes)" -ForegroundColor Gray
idf.py -D SDKCONFIG_DEFAULTS="$env:SDKCONFIG_DEFAULTS" build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check ESP-IDF environment variables" -ForegroundColor Gray
    Write-Host "2. Check component dependencies (idf_component.yml)" -ForegroundColor Gray
    Write-Host "3. If managed_components hash error, run:" -ForegroundColor Gray
    Write-Host "   .\build.ps1 -CleanComponents -Clean" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "OK: Build successful!" -ForegroundColor Green
Write-Host ""
Write-Host "Build results:" -ForegroundColor Cyan
$binFile = "build\cores3-management.bin"
if (Test-Path $binFile) {
    $fileInfo = Get-Item $binFile
    Write-Host "   Firmware: $binFile ($([math]::Round($fileInfo.Length / 1KB, 2)) KB)" -ForegroundColor Cyan
}

# Flash
if ($Flash) {
    Write-Host ""
    Write-Host "[7] Flashing firmware..." -ForegroundColor Yellow
    if ($Port) {
        idf.py -p $Port flash
    }
    else {
        Write-Host "   Auto-detecting port..." -ForegroundColor Gray
        idf.py flash
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: Flash complete" -ForegroundColor Green
    }
    else {
        Write-Host "ERROR: Flash failed" -ForegroundColor Red
        exit 1
    }
}

# Monitor
if ($Monitor) {
    Write-Host ""
    Write-Host "[8] Starting serial monitor..." -ForegroundColor Yellow
    Write-Host "   Exit: Ctrl+]" -ForegroundColor Gray
    if ($Port) {
        idf.py -p $Port monitor
    }
    else {
        idf.py monitor
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
