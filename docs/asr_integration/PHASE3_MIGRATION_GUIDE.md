# Phase 3 데이터베이스 마이그레이션 가이드

**작성일:** 2025-12-10  
**대상:** Phase 3에서 추가된 테이블 생성

---

## 📊 추가되는 테이블

1. **`asr_results`** - ASR 결과 저장
   - 음성 인식 결과
   - 응급 상황 정보
   - 장비 및 세션 정보

2. **`emergency_alerts`** - 응급 상황 알림 이력
   - 알림 우선순위 및 상태
   - API 전송 정보
   - 확인 처리 정보

---

## 🚀 마이그레이션 방법

### 방법 1: Python 스크립트 사용 (권장) ⭐

**가장 간단하고 안전한 방법입니다.**

```bash
cd backend
python migrate_phase3.py
```

**특징:**
- 기존 테이블 존재 여부 자동 확인
- 없으면 자동 생성
- 인덱스 자동 생성
- 마이그레이션 검증 포함
- 기존 데이터 보존

**출력 예시:**
```
============================================================
Phase 3 데이터베이스 마이그레이션 시작
============================================================
asr_results 테이블 생성 중...
✅ asr_results 테이블 생성 완료
emergency_alerts 테이블 생성 중...
✅ emergency_alerts 테이블 생성 완료
...
============================================================
✅ Phase 3 마이그레이션 완료!
============================================================
```

---

### 방법 2: SQL 스크립트 직접 실행

#### MySQL 사용 시:

```bash
cd backend
mysql -u [username] -p [database_name] < migrations/phase3_migration.sql
```

**예시:**
```bash
mysql -u root -p cores3_management < migrations/phase3_migration.sql
```

#### MySQL Workbench에서:
1. MySQL Workbench 열기
2. 데이터베이스 연결
3. `File` → `Open SQL Script`
4. `backend/migrations/phase3_migration.sql` 선택
5. 실행 (⚡ 아이콘 클릭)

---

### 방법 3: init_db.py 사용 (전체 테이블 재생성)

**주의:** 이 방법은 모든 테이블을 재생성하지만, 기존 데이터는 보존됩니다.

```bash
cd backend
python init_db.py
```

---

## ✅ 마이그레이션 검증

### MySQL에서 확인:

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

-- 데이터 확인 (샘플)
SELECT * FROM asr_results LIMIT 5;
SELECT * FROM emergency_alerts LIMIT 5;
```

### Python 스크립트로 확인:

```python
from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print("생성된 테이블:")
for table in ['asr_results', 'emergency_alerts']:
    if table in tables:
        print(f"✅ {table}")
        columns = [col['name'] for col in inspector.get_columns(table)]
        print(f"   컬럼: {', '.join(columns)}")
    else:
        print(f"❌ {table} 없음")
```

---

## 🔧 문제 해결

### 1. 외래 키 제약 조건 오류

**오류 메시지:**
```
Cannot add foreign key constraint
```

**해결 방법:**
- `devices` 테이블이 존재하는지 확인
- `users` 테이블이 존재하는지 확인
- 기존 테이블이 있으면 `init_db.py` 실행

```sql
-- 테이블 확인
SHOW TABLES;

-- devices 테이블 확인
DESCRIBE devices;
```

### 2. 권한 오류

**오류 메시지:**
```
Access denied for user
```

**해결 방법:**
- 데이터베이스 사용자에게 CREATE TABLE 권한 부여

```sql
-- 권한 부여 (MySQL root로 실행)
GRANT ALL PRIVILEGES ON cores3_management.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 테이블이 이미 존재함

**Python 스크립트 사용 시:**
- 자동으로 처리됩니다 (에러 없음)

**SQL 스크립트 사용 시:**
- `IF NOT EXISTS` 구문으로 안전합니다
- 에러 없이 건너뜁니다

### 4. 인덱스 생성 실패

**해결 방법:**
- Python 스크립트는 자동으로 재시도합니다
- SQL 스크립트는 `IF NOT EXISTS`로 안전합니다

---

## 🔄 롤백 (필요 시)

**주의:** 테이블 삭제 시 모든 데이터가 삭제됩니다. 백업을 먼저 수행하세요.

### 백업:

```bash
# MySQL 덤프
mysqldump -u [username] -p [database_name] > backup_before_rollback.sql
```

### 롤백:

```sql
-- 테이블 삭제
DROP TABLE IF EXISTS emergency_alerts;
DROP TABLE IF EXISTS asr_results;
```

---

## 📋 마이그레이션 체크리스트

- [ ] 데이터베이스 백업 수행
- [ ] 마이그레이션 스크립트 실행
- [ ] 테이블 생성 확인
- [ ] 인덱스 생성 확인
- [ ] 외래 키 제약 조건 확인
- [ ] 애플리케이션 재시작
- [ ] API 테스트

---

## 📝 참고 사항

1. **기존 데이터 보존:** 마이그레이션은 기존 데이터를 보존합니다.
2. **인덱스 자동 생성:** 성능 최적화를 위해 인덱스가 자동 생성됩니다.
3. **외래 키 제약:** 데이터 무결성을 보장하기 위해 외래 키가 설정됩니다.
4. **트랜잭션:** SQL 스크립트는 트랜잭션으로 실행됩니다.

---

## 🎯 다음 단계

마이그레이션 완료 후:

1. **애플리케이션 재시작**
   ```bash
   # 백엔드 서버 재시작
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **API 테스트**
   - ASR 결과 저장 API 테스트
   - 응급 상황 알림 API 테스트
   - 대시보드 통계 확인

3. **데이터 확인**
   - 대시보드에서 ASR 통계 확인
   - 응급 상황 이력 확인

---

**완료일:** 2025-12-10  
**마이그레이션 상태:** ✅ 준비 완료

