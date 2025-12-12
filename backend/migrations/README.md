# Phase 3 데이터베이스 마이그레이션 가이드

## 개요

Phase 3에서 추가된 테이블:
- `asr_results` - ASR 결과 저장
- `emergency_alerts` - 응급 상황 알림 이력

## 마이그레이션 방법

### 방법 1: Python 스크립트 사용 (권장) ⭐⭐⭐

**PowerShell에서도 이 방법을 가장 권장합니다!**

```bash
# Windows PowerShell
cd backend
python migrate_phase3.py

# Linux/Mac
cd backend
python3 migrate_phase3.py
```

이 스크립트는:
- 기존 테이블 존재 여부 확인
- 없으면 자동 생성
- 인덱스 자동 생성
- 마이그레이션 검증

### 방법 2: SQL 스크립트 직접 실행

#### MySQL 사용 시:

**Linux/Mac:**
```bash
mysql -u [username] -p [database_name] < migrations/phase3_migration.sql
```

**Windows PowerShell:**
```powershell
# 방법 1: Get-Content 사용
Get-Content migrations\phase3_migration.sql | mysql -u root -p cores3_management

# 방법 2: cmd.exe 사용
cmd /c "mysql -u root -p cores3_management < migrations\phase3_migration.sql"

# 방법 3: PowerShell 스크립트 사용
.\migrate_phase3.ps1
```

#### SQLite 사용 시:
```bash
sqlite3 [database_file] < migrations/phase3_migration_sqlite.sql
```

또는 SQLite 콘솔에서:
```sql
.read migrations/phase3_migration_sqlite.sql
```

### 방법 3: init_db.py 사용 (전체 테이블 재생성)

**주의:** 이 방법은 기존 데이터를 보존하지만, 모든 테이블을 재생성합니다.

```bash
cd backend
python init_db.py
```

## 마이그레이션 검증

### MySQL:
```sql
-- 테이블 확인
SHOW TABLES LIKE 'asr_results';
SHOW TABLES LIKE 'emergency_alerts';

-- 테이블 구조 확인
DESCRIBE asr_results;
DESCRIBE emergency_alerts;

-- 인덱스 확인
SHOW INDEX FROM asr_results;
SHOW INDEX FROM emergency_alerts;
```

### SQLite:
```sql
-- 테이블 확인
.tables

-- 테이블 구조 확인
.schema asr_results
.schema emergency_alerts

-- 인덱스 확인
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='asr_results';
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='emergency_alerts';
```

## 롤백 (필요 시)

### 테이블 삭제:
```sql
-- MySQL
DROP TABLE IF EXISTS emergency_alerts;
DROP TABLE IF EXISTS asr_results;

-- SQLite
DROP TABLE IF EXISTS emergency_alerts;
DROP TABLE IF EXISTS asr_results;
```

**주의:** 테이블 삭제 시 모든 데이터가 삭제됩니다. 백업을 먼저 수행하세요.

## 문제 해결

### 1. 외래 키 제약 조건 오류
- `devices` 테이블이 존재하는지 확인
- `users` 테이블이 존재하는지 확인

### 2. 권한 오류
- 데이터베이스 사용자에게 CREATE TABLE 권한이 있는지 확인

### 3. 테이블이 이미 존재함
- `migrate_phase3.py` 스크립트는 자동으로 처리합니다
- SQL 스크립트는 `IF NOT EXISTS`를 사용하므로 안전합니다

## 참고

- 마이그레이션 스크립트는 기존 데이터를 보존합니다
- 인덱스는 성능 최적화를 위해 자동 생성됩니다
- 외래 키 제약 조건은 데이터 무결성을 보장합니다

