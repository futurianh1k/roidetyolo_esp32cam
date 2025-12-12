# PowerShell에서 Phase 3 마이그레이션 실행하기

PowerShell에서는 `<` 리다이렉션이 다르게 작동하므로, 다음 방법 중 하나를 사용하세요.

## 방법 1: PowerShell 스크립트 사용 (권장) ⭐

```powershell
cd backend
.\migrate_phase3.ps1
```

또는 매개변수 지정:

```powershell
.\migrate_phase3.ps1 -DatabaseName "cores3_management" -Username "root"
```

## 방법 2: Get-Content 사용

```powershell
cd backend
Get-Content migrations\phase3_migration.sql | mysql -u root -p cores3_management
```

비밀번호를 직접 입력하려면:

```powershell
$password = Read-Host "MySQL 비밀번호" -AsSecureString
$plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
)
Get-Content migrations\phase3_migration.sql | mysql -u root -p$plainPassword cores3_management
```

## 방법 3: cmd.exe 사용

```powershell
cd backend
cmd /c "mysql -u root -p cores3_management < migrations\phase3_migration.sql"
```

## 방법 4: Python 스크립트 사용 (가장 간단) ⭐⭐⭐

```powershell
cd backend
python migrate_phase3.py
```

**이 방법을 가장 권장합니다!** PowerShell의 리다이렉션 문제를 피할 수 있습니다.

## 방법 5: MySQL Workbench 사용

1. MySQL Workbench 열기
2. 데이터베이스 연결
3. `File` → `Open SQL Script`
4. `backend/migrations/phase3_migration.sql` 선택
5. 실행 (⚡ 아이콘 클릭)

---

## 실행 권한 오류 시

PowerShell 스크립트 실행이 차단된 경우:

```powershell
# 실행 정책 확인
Get-ExecutionPolicy

# 임시로 실행 정책 변경 (현재 세션만)
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# 스크립트 실행
.\migrate_phase3.ps1
```

---

## 추천 방법

**가장 간단하고 안전한 방법:**

```powershell
cd backend
python migrate_phase3.py
```

이 방법은:

- ✅ PowerShell 리다이렉션 문제 없음
- ✅ 자동 검증 포함
- ✅ 에러 처리 포함
- ✅ 크로스 플랫폼 호환
