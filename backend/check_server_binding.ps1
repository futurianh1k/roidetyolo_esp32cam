# Backend Server Binding Check Script
# Usage: .\check_server_binding.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Backend Server Binding Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check port 8000 usage
Write-Host "[1] Port 8000 Usage Check" -ForegroundColor Yellow
$port8000 = netstat -ano | findstr :8000
if ($port8000) {
    Write-Host "OK: Port 8000 is in use" -ForegroundColor Green
    Write-Host $port8000
    
    # Check binding address
    if ($port8000 -match "0\.0\.0\.0:8000" -or $port8000 -match "\[::\]:8000") {
        Write-Host "OK: Correctly bound - accessible from all network interfaces" -ForegroundColor Green
    } elseif ($port8000 -match "127\.0\.0\.1:8000") {
        Write-Host "WARNING: Only local access - bound to 127.0.0.1" -ForegroundColor Yellow
        Write-Host "   ESP32 devices need 0.0.0.0 binding" -ForegroundColor Yellow
    } else {
        Write-Host "WARNING: Binding address check needed" -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR: Port 8000 is not in use. Check if backend server is running." -ForegroundColor Red
}

Write-Host ""

# 2. Check config file
Write-Host "[2] Config File Check" -ForegroundColor Yellow
$envFile = ".\.env"
if (Test-Path $envFile) {
    Write-Host "OK: .env file found" -ForegroundColor Green
    
    $hostSetting = Select-String -Path $envFile -Pattern "^HOST="
    if ($hostSetting) {
        Write-Host "   HOST setting: $hostSetting" -ForegroundColor Cyan
        if ($hostSetting -match "HOST=0\.0\.0\.0") {
            Write-Host "   OK: Correct setting - 0.0.0.0" -ForegroundColor Green
        } else {
            Write-Host "   WARNING: Recommend changing HOST to 0.0.0.0" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   WARNING: No HOST setting. Default (0.0.0.0) will be used." -ForegroundColor Yellow
    }
} else {
    Write-Host "WARNING: .env file not found. Create one based on env.example." -ForegroundColor Yellow
}

Write-Host ""

# 3. Local connection test
Write-Host "[3] Local Connection Test" -ForegroundColor Yellow
try {
    $response = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue
    if ($response.TcpTestSucceeded) {
        Write-Host "OK: localhost:8000 connection successful" -ForegroundColor Green
    } else {
        Write-Host "ERROR: localhost:8000 connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "ERROR: Connection test failed: $_" -ForegroundColor Red
}

Write-Host ""

# 4. Network IP check
Write-Host "[4] Network IP Check" -ForegroundColor Yellow
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object IPAddress, InterfaceAlias
if ($ipAddresses) {
    Write-Host "OK: Network interfaces:" -ForegroundColor Green
    foreach ($ip in $ipAddresses) {
        Write-Host "   - $($ip.IPAddress) ($($ip.InterfaceAlias))" -ForegroundColor Cyan
        Write-Host "     Test: http://$($ip.IPAddress):8000/docs" -ForegroundColor Gray
    }
} else {
    Write-Host "WARNING: No active network interfaces found." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Check Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
