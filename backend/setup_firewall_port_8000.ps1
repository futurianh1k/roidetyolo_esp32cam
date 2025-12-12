# Windows Firewall Port 8000 Allow Script
# Requires Administrator Privileges
# Usage: Run PowerShell as Administrator, then: .\setup_firewall_port_8000.ps1

# Check administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires administrator privileges." -ForegroundColor Red
    Write-Host "   Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   How to:" -ForegroundColor Cyan
    Write-Host "   1. Search for 'PowerShell' in Start Menu" -ForegroundColor Cyan
    Write-Host "   2. Right-click 'Windows PowerShell'" -ForegroundColor Cyan
    Write-Host "   3. Select 'Run as Administrator'" -ForegroundColor Cyan
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Windows Firewall Port 8000 Allow Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check existing rule
$existingRule = Get-NetFirewallRule -DisplayName "Backend Server Port 8000" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "WARNING: Existing firewall rule found." -ForegroundColor Yellow
    $response = Read-Host "Delete existing rule and create new one? (Y/N)"
    if ($response -eq "Y" -or $response -eq "y") {
        Remove-NetFirewallRule -DisplayName "Backend Server Port 8000"
        Write-Host "OK: Existing rule deleted" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing rule." -ForegroundColor Yellow
        exit 0
    }
}

# Add new firewall rule
Write-Host "Adding firewall rule..." -ForegroundColor Yellow

try {
    New-NetFirewallRule `
        -DisplayName "Backend Server Port 8000" `
        -Description "Port for ESP32 devices to access backend server" `
        -Direction Inbound `
        -LocalPort 8000 `
        -Protocol TCP `
        -Action Allow `
        -Profile Any `
        -Enabled True | Out-Null
    
    Write-Host "OK: Firewall rule added successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Rule Information:" -ForegroundColor Cyan
    Get-NetFirewallRule -DisplayName "Backend Server Port 8000" | Format-Table DisplayName, Enabled, Direction, Action, Profile
    
} catch {
    Write-Host "ERROR: Failed to add firewall rule: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Check if backend server is bound to 0.0.0.0" -ForegroundColor Cyan
Write-Host "   Run: .\check_server_binding.ps1" -ForegroundColor Gray
Write-Host "2. Start backend server" -ForegroundColor Cyan
Write-Host "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host "3. Test audio playback from ESP32" -ForegroundColor Cyan
