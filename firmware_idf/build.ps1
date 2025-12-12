# ESP-IDF Build Script
# Usage: .\build.ps1

param(
    [string]$IdfPath = "",
    [string]$Target = "esp32s3",
    [string]$Port = "",
    [switch]$Flash = $false,
    [switch]$Monitor = $false,
    [switch]$Clean = $false
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "ESP-IDF Build Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ESP-IDF 경로 찾기
if ([string]::IsNullOrEmpty($IdfPath)) {
    # 1. IDF_PATH 환경 변수 확인
    if ($env:IDF_PATH -and (Test-Path $env:IDF_PATH)) {
        $IdfPath = $env:IDF_PATH
        Write-Host "[INFO] Using IDF_PATH: $IdfPath" -ForegroundColor Cyan
    }
    # 2. E:\esp32\Espressif 경로 확인 (사용자 설치 경로 - 최우선)
    elseif (Test-Path "E:\esp32\Espressif\frameworks\esp-idf-v5.5.1") {
        $IdfPath = "E:\esp32\Espressif\frameworks\esp-idf-v5.5.1"
    }
    elseif (Test-Path "E:\esp32\Espressif\frameworks\esp-idf-v5.5") {
        $IdfPath = "E:\esp32\Espressif\frameworks\esp-idf-v5.5"
    }
    elseif (Test-Path "E:\esp32\Espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "E:\esp32\Espressif\frameworks\esp-idf-v5.4"
    }
    elseif (Test-Path "E:\esp32\Espressif\frameworks\esp-idf-v5.3") {
        $IdfPath = "E:\esp32\Espressif\frameworks\esp-idf-v5.3"
    }
    # 3. C:\esp32\Espressif 경로 확인
    elseif (Test-Path "C:\esp32\Espressif\frameworks\esp-idf-v5.5.1") {
        $IdfPath = "C:\esp32\Espressif\frameworks\esp-idf-v5.5.1"
    }
    elseif (Test-Path "C:\esp32\Espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "C:\esp32\Espressif\frameworks\esp-idf-v5.4"
    }
    elseif (Test-Path "C:\esp32\Espressif\frameworks\esp-idf-v5.3") {
        $IdfPath = "C:\esp32\Espressif\frameworks\esp-idf-v5.3"
    }
    elseif (Test-Path "C:\esp32\Espressif\frameworks\esp-idf-v5.2") {
        $IdfPath = "C:\esp32\Espressif\frameworks\esp-idf-v5.2"
    }
    # 3-1. C:\esp32\Espressif 직접 경로 확인 (frameworks 없이)
    elseif (Test-Path "C:\esp32\Espressif\esp-idf\export.ps1") {
        $IdfPath = "C:\esp32\Espressif\esp-idf"
    }
    elseif (Test-Path "C:\esp32\Espressif\export.ps1") {
        $IdfPath = "C:\esp32\Espressif"
    }
    # 4. C:\esp32 직접 경로 확인
    elseif (Test-Path "C:\esp32\export.ps1") {
        $IdfPath = "C:\esp32"
    }
    # 4. 일반적인 설치 경로 확인
    elseif (Test-Path "C:\Espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "C:\Espressif\frameworks\esp-idf-v5.4"
    }
    elseif (Test-Path "C:\Espressif\frameworks\esp-idf-v5.3") {
        $IdfPath = "C:\Espressif\frameworks\esp-idf-v5.3"
    }
    elseif (Test-Path "C:\Espressif\frameworks\esp-idf-v5.2") {
        $IdfPath = "C:\Espressif\frameworks\esp-idf-v5.2"
    }
    # 5. 사용자 홈 디렉토리 확인
    elseif (Test-Path "$env:USERPROFILE\.espressif\frameworks\esp-idf-v5.4") {
        $IdfPath = "$env:USERPROFILE\.espressif\frameworks\esp-idf-v5.4"
    }
    elseif (Test-Path "$env:USERPROFILE\.espressif\frameworks\esp-idf-v5.3") {
        $IdfPath = "$env:USERPROFILE\.espressif\frameworks\esp-idf-v5.3"
    }
    else {
        Write-Host "ERROR: ESP-IDF path not found" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please specify ESP-IDF path:" -ForegroundColor Yellow
        Write-Host "  .\build.ps1 -IdfPath 'C:\path\to\esp-idf'" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Or set IDF_PATH environment variable:" -ForegroundColor Yellow
        Write-Host "  `$env:IDF_PATH = 'C:\path\to\esp-idf'" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Common locations:" -ForegroundColor Yellow
        Write-Host "  - E:\esp32\Espressif\frameworks\esp-idf-v5.5.1" -ForegroundColor Gray
        Write-Host "  - C:\esp32\Espressif\frameworks\esp-idf-v5.4" -ForegroundColor Gray
        Write-Host "  - C:\Espressif\frameworks\esp-idf-v5.4" -ForegroundColor Gray
        Write-Host "  - $env:USERPROFILE\.espressif\frameworks\esp-idf-v5.4" -ForegroundColor Gray
        exit 1
    }
}

# ESP-IDF 경로 확인
if (-not (Test-Path $IdfPath)) {
    Write-Host "ERROR: ESP-IDF path does not exist: $IdfPath" -ForegroundColor Red
    exit 1
}

# ESP-IDF 환경 설정
Write-Host "[1] Setting up ESP-IDF environment..." -ForegroundColor Yellow
Write-Host "   ESP-IDF path: $IdfPath" -ForegroundColor Gray

# export.ps1 파일 찾기
$exportScript = Join-Path $IdfPath "export.ps1"
if (-not (Test-Path $exportScript)) {
    Write-Host "ERROR: export.ps1 not found in: $IdfPath" -ForegroundColor Red
    Write-Host "   Please check ESP-IDF installation path" -ForegroundColor Yellow
    exit 1
}

if (Test-Path $exportScript) {
    Write-Host "   Found export.ps1: $exportScript" -ForegroundColor Gray
    
    # export.ps1 실행 (오류 무시하고 계속 진행)
    $ErrorActionPreference = "SilentlyContinue"
    & $exportScript 2>&1 | Out-Null
    $ErrorActionPreference = "Continue"
    
    # idf.py가 사용 가능한지 확인
    $idfPyCheck = Get-Command idf.py -ErrorAction SilentlyContinue
    if (-not $idfPyCheck) {
        Write-Host ""
        Write-Host "ERROR: ESP-IDF environment not properly set up" -ForegroundColor Red
        Write-Host ""
        Write-Host "The Python virtual environment is missing or not configured." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Please run the ESP-IDF install script:" -ForegroundColor Yellow
        Write-Host "  cd $IdfPath" -ForegroundColor Cyan
        Write-Host "  .\install.bat esp32,esp32s3" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Or if using ESP-IDF installer, run:" -ForegroundColor Yellow
        Write-Host "  cd E:\esp32\Espressif" -ForegroundColor Cyan
        Write-Host "  .\install.bat" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "See INSTALL_ESP_IDF.md for detailed instructions." -ForegroundColor Gray
        exit 1
    }
    
    Write-Host "OK: ESP-IDF environment setup complete" -ForegroundColor Green
}
else {
    Write-Host "ERROR: export.ps1 not found: $exportScript" -ForegroundColor Red
    exit 1
}

# 프로젝트 디렉토리로 이동
Set-Location $PSScriptRoot
Write-Host ""
Write-Host "[2] Project directory: $PSScriptRoot" -ForegroundColor Yellow

# 클린 빌드
if ($Clean) {
    Write-Host ""
    Write-Host "[3] Running clean build..." -ForegroundColor Yellow
    idf.py fullclean
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Clean build warning (continuing)" -ForegroundColor Yellow
    }
}

# 타겟 설정
Write-Host ""
Write-Host "[4] Setting target: $Target" -ForegroundColor Yellow
idf.py set-target $Target
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to set target" -ForegroundColor Red
    exit 1
}

# 빌드
Write-Host ""
Write-Host "[5] Building..." -ForegroundColor Yellow
Write-Host "   (This may take several minutes)" -ForegroundColor Gray
idf.py build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK: Build successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Build results:" -ForegroundColor Cyan
    $binFile = "build\cores3-management.bin"
    if (Test-Path $binFile) {
        $fileInfo = Get-Item $binFile
        Write-Host "   Firmware: $binFile ($([math]::Round($fileInfo.Length / 1KB, 2)) KB)" -ForegroundColor Cyan
    }
    
    # 플래시
    if ($Flash) {
        Write-Host ""
        Write-Host "[6] Flashing firmware..." -ForegroundColor Yellow
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
    
    # 모니터링
    if ($Monitor) {
        Write-Host ""
        Write-Host "[7] Starting serial monitor..." -ForegroundColor Yellow
        Write-Host "   Exit: Ctrl+]" -ForegroundColor Gray
        if ($Port) {
            idf.py -p $Port monitor
        }
        else {
            idf.py monitor
        }
    }

    else {
        Write-Host ""
        Write-Host "ERROR: Build failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Check ESP-IDF environment variables" -ForegroundColor Gray
        Write-Host "2. Check component dependencies (idf_component.yml)" -ForegroundColor Gray
        Write-Host "3. Check CMakeLists.txt files" -ForegroundColor Gray
        Write-Host "4. Check detailed log: idf.py build -v" -ForegroundColor Gray
        exit 1
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Complete" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
