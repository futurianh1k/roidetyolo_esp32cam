# Phase 3 데이터베이스 마이그레이션 스크립트 (PowerShell)
# ASR 결과 및 응급 상황 알림 테이블 생성

param(
    [string]$DatabaseName = "cores3_management",
    [string]$Username = "root",
    [string]$Password = "",
    [string]$Host = "localhost",
    [int]$Port = 3306
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Phase 3 데이터베이스 마이그레이션 시작" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# SQL 파일 경로
$sqlFile = Join-Path $PSScriptRoot "migrations\phase3_migration.sql"

if (-not (Test-Path $sqlFile)) {
    Write-Host "❌ SQL 파일을 찾을 수 없습니다: $sqlFile" -ForegroundColor Red
    exit 1
}

# 비밀번호 입력 (없는 경우)
if ([string]::IsNullOrEmpty($Password)) {
    $securePassword = Read-Host "MySQL 비밀번호를 입력하세요" -AsSecureString
    $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    )
}

# MySQL 명령 실행
try {
    Write-Host "`n데이터베이스 마이그레이션 실행 중..." -ForegroundColor Yellow
    
    # SQL 파일 내용 읽기
    $sqlContent = Get-Content $sqlFile -Raw -Encoding UTF8
    
    # MySQL 명령 실행
    $mysqlCommand = "mysql -h $Host -P $Port -u $Username -p$Password $DatabaseName"
    
    $sqlContent | & cmd /c $mysqlCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ 마이그레이션 완료!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "`n❌ 마이그레이션 실패 (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n❌ 오류 발생: $_" -ForegroundColor Red
    exit 1
}

