<#
.SYNOPSIS
    E2E Test Runner Script (Windows PowerShell)

.DESCRIPTION
    PowerShell script for running Selenium E2E tests.
    Automates virtual environment setup, environment variables, and test execution.

.PARAMETER Headless
    Run browser in headless mode (default: true)

.PARAMETER SlowMode
    Slow mode for debugging (default: false)

.PARAMETER TestFile
    Run specific test file (e.g., test_dashboard.py)

.PARAMETER TestCase
    Run specific test case (e.g., TestDashboard::test_tc_dash_001)

.PARAMETER Markers
    Pytest marker filter (e.g., "not slow")

.PARAMETER Report
    Generate HTML report (default: false)

.PARAMETER Parallel
    Parallel execution (number of processes, 0 to disable)

.PARAMETER Install
    Install dependencies only

.EXAMPLE
    .\run_tests.ps1
    # Run tests in headless mode

.EXAMPLE
    .\run_tests.ps1 -Headless $false
    # Run with visible browser

.EXAMPLE
    .\run_tests.ps1 -TestFile test_dashboard.py -Report
    # Run dashboard tests and generate HTML report

.EXAMPLE
    .\run_tests.ps1 -Markers "not slow" -Parallel 4
    # Skip slow tests and run with 4 processes
#>

param(
    [bool]$Headless = $true,
    [bool]$SlowMode = $false,
    [string]$TestFile = "",
    [string]$TestCase = "",
    [string]$Markers = "",
    [switch]$Report,
    [int]$Parallel = 0,
    [switch]$Install,
    [switch]$Help
)

# Color output functions
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "`n[*] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[OK] $Message" "Green"
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-ColorOutput "[X] $Message" "Red"
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "    $Message" "Gray"
}

# Show help
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-ColorOutput "`n========================================" "Yellow"
Write-ColorOutput "    E2E Test Runner (PowerShell)" "Yellow"
Write-ColorOutput "========================================`n" "Yellow"

# Check Python
Write-Step "Checking Python environment..."

$PythonCmd = $null
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
}
elseif (Get-Command "python3" -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
}
else {
    Write-ErrorMsg "Python is not installed."
    exit 1
}

$PythonVersion = & $PythonCmd --version 2>&1
Write-Success "Python found: $PythonVersion"

# Virtual environment setup
$VenvPath = Join-Path $ScriptDir "venv"
$VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip = Join-Path $VenvPath "Scripts\pip.exe"

if (-not (Test-Path $VenvPath)) {
    Write-Step "Creating virtual environment..."
    & $PythonCmd -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to create virtual environment"
        exit 1
    }
    Write-Success "Virtual environment created: $VenvPath"
}

# Activate virtual environment
Write-Step "Activating virtual environment..."
if (Test-Path $VenvActivate) {
    . $VenvActivate
    Write-Success "Virtual environment activated"
}
else {
    Write-ErrorMsg "Cannot find activation script: $VenvActivate"
    exit 1
}

# Install dependencies
if ($Install -or -not (Test-Path (Join-Path $VenvPath "Scripts\pytest.exe"))) {
    Write-Step "Installing dependencies..."
    & $VenvPip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to install dependencies"
        exit 1
    }
    Write-Success "Dependencies installed"
    
    if ($Install) {
        Write-ColorOutput "`nDependencies installed. To run tests:" "Green"
        Write-ColorOutput "    .\run_tests.ps1" "White"
        exit 0
    }
}

# Create screenshots directory
$ScreenshotDir = Join-Path $ScriptDir "screenshots"
if (-not (Test-Path $ScreenshotDir)) {
    New-Item -ItemType Directory -Path $ScreenshotDir | Out-Null
    Write-Info "Screenshots directory created: $ScreenshotDir"
}

# Set environment variables
Write-Step "Setting environment variables..."

# Load .env file
$EnvFile = Join-Path $ScriptDir ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Info ".env file loaded"
}

# Override with command line arguments
$env:E2E_HEADLESS = if ($Headless) { "true" } else { "false" }
$env:E2E_SLOW_MODE = if ($SlowMode) { "true" } else { "false" }
$env:E2E_SCREENSHOT_DIR = $ScreenshotDir

Write-Info "E2E_HEADLESS = $env:E2E_HEADLESS"
Write-Info "E2E_SLOW_MODE = $env:E2E_SLOW_MODE"
Write-Info "E2E_BASE_URL = $env:E2E_BASE_URL"

# Build pytest arguments
$PytestArgs = @("-v", "--tb=short")

# Specific test file
if ($TestFile) {
    $TestPath = Join-Path "tests" $TestFile
    if ($TestCase) {
        $TestPath = "${TestPath}::${TestCase}"
    }
    $PytestArgs += $TestPath
}
elseif ($TestCase) {
    $PytestArgs += "-k"
    $PytestArgs += $TestCase
}

# Marker filter
if ($Markers) {
    $PytestArgs += "-m"
    $PytestArgs += $Markers
}

# HTML report
if ($Report) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $ReportPath = "reports\report_$Timestamp.html"
    
    # Create reports directory
    $ReportDir = Join-Path $ScriptDir "reports"
    if (-not (Test-Path $ReportDir)) {
        New-Item -ItemType Directory -Path $ReportDir | Out-Null
    }
    
    $PytestArgs += "--html=$ReportPath"
    $PytestArgs += "--self-contained-html"
}

# Parallel execution
if ($Parallel -gt 0) {
    $PytestArgs += "-n"
    $PytestArgs += $Parallel.ToString()
}

# Run tests
Write-Step "Running tests..."
Write-Info "pytest $($PytestArgs -join ' ')"
Write-ColorOutput ""

$PytestExe = Join-Path $VenvPath "Scripts\pytest.exe"

# Execute pytest
& $VenvPython -m pytest $PytestArgs
$ExitCode = $LASTEXITCODE

# Output results
Write-ColorOutput ""
if ($ExitCode -eq 0) {
    Write-Success "All tests passed!"
}
else {
    Write-ErrorMsg "Some tests failed (exit code: $ExitCode)"
}

if ($Report) {
    Write-Info "Report generated: $ReportPath"
}

exit $ExitCode
