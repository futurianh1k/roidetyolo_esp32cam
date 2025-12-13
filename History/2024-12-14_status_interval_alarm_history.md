# 개발 내역: 상태 보고 주기 변경 및 알람 이력 기능

**날짜**: 2024-12-14  
**작성자**: AI Assistant (Claude)  
**브랜치**: feature/esp-idf-migration

---

## 1. 요청 사항

### 사용자 요청
1. 상태 보고 주기를 기본 1분으로 변경하고, 웹 페이지에서 동적으로 변경 가능하도록
2. 알람 발송 이력 기록 기능 추가
   - 알람 타입 (sound, text, recorded)
   - 발송 시간
   - 누가 활성화했는지 (system, admin, user, schedule)
3. 펌웨어 스택 오버플로우 버그 수정

---

## 2. 구현 내용

### 2.1 상태 보고 주기 변경 기능

#### 변경 파일

| 레이어 | 파일 | 변경 내용 |
|--------|------|-----------|
| DB | `backend/app/models/device.py` | `status_report_interval` 컬럼 추가 (기본값 60초) |
| 백엔드 | `backend/app/schemas/device.py` | 스키마에 interval 필드 추가 |
| 백엔드 | `backend/app/schemas/control.py` | `set_interval` 액션 추가 |
| 백엔드 | `backend/app/api/control.py` | `set_interval` 처리 및 DB 업데이트 |
| 펌웨어 | `firmware_idf/main/config.h` | 기본값 60000ms (60초)로 변경 |
| 펌웨어 | `firmware_idf/main/status/status_reporter.h` | `SetInterval()` 메서드 추가 |
| 펌웨어 | `firmware_idf/main/status/status_reporter.cc` | interval 동적 변경 구현 |
| 펌웨어 | `firmware_idf/main/application.cc` | MQTT `set_interval` 명령 처리 |
| 프론트엔드 | `frontend/src/lib/api.ts` | `setReportInterval()` 함수 추가, Device 인터페이스 업데이트 |
| 프론트엔드 | `frontend/src/app/devices/[id]/page.tsx` | 보고 주기 드롭다운 UI 추가 |

#### 사용 가능한 주기 옵션
- 10초, 30초, 1분, 2분, 5분, 10분, 30분, 1시간

---

### 2.2 알람 이력 기록 기능

#### 새로 생성된 파일

| 파일 | 설명 |
|------|------|
| `backend/app/models/alarm_history.py` | AlarmHistory 모델 |
| `backend/app/schemas/alarm_history.py` | 알람 이력 스키마 |
| `backend/app/api/alarm_history.py` | 알람 이력 API 엔드포인트 |

#### 알람 이력 데이터 구조

```python
class AlarmHistory:
    id: int                      # PK
    device_id: int               # 장비 ID (FK)
    alarm_type: str              # 'sound' | 'text' | 'recorded'
    alarm_subtype: str           # 'beep', 'alert', 'emergency' 등
    content: str                 # TTS 텍스트 또는 파일 경로
    triggered_by: str            # 'system' | 'admin' | 'user' | 'schedule'
    triggered_user_id: int       # 트리거한 사용자 ID (FK)
    created_at: datetime         # 생성 시간
    parameters: str              # JSON 형태의 추가 파라미터
    status: str                  # 'sent' | 'delivered' | 'failed'
```

#### API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/alarm-history` | 전체 알람 이력 조회 (필터링 가능) |
| GET | `/alarm-history/device/{id}` | 특정 장비 알람 이력 |
| GET | `/alarm-history/{id}` | 알람 이력 상세 |
| DELETE | `/alarm-history/{id}` | 알람 이력 삭제 |

#### 필터 파라미터
- `device_id`: 장비 ID
- `alarm_type`: `sound`, `text`, `recorded`
- `triggered_by`: `system`, `admin`, `user`, `schedule`
- `start_date`, `end_date`: 날짜 범위

---

### 2.3 스택 오버플로우 버그 수정

#### 문제 현상
- 이모지 전송 또는 상태 보고 시 `Tmr Svc` 태스크에서 스택 오버플로우 발생
- ESP32 재부팅

#### 원인 분석
- FreeRTOS Timer Service 태스크의 스택 크기: 2048 바이트
- `StatusReporter::TimerCallback`에서 직접 HTTP 요청 수행
- HTTP 요청은 많은 스택을 사용하여 오버플로우 발생

#### 해결 방법

1. **sdkconfig 수정**
   - `CONFIG_FREERTOS_TIMER_TASK_STACK_DEPTH`: 2048 → 4096
   - `CONFIG_TIMER_TASK_STACK_DEPTH`: 2048 → 4096

2. **StatusReporter 아키텍처 개선**

**이전 (문제)**:
```
Timer Callback (2KB 스택) → 직접 HTTP 요청 → 스택 오버플로우!
```

**이후 (수정)**:
```
Timer Callback (4KB 스택) → 세마포어 발행만 (가벼움)
                              ↓
Report Task (8KB 스택) → HTTP 요청 수행 (충분한 스택)
```

---

### 2.4 DB 마이그레이션 스크립트

#### 생성된 파일

| 파일 | 설명 |
|------|------|
| `backend/scripts/migrate_db.py` | 통합 Python 마이그레이션 스크립트 |
| `backend/scripts/migrations/001_add_status_report_interval.sql` | interval 컬럼 추가 SQL |
| `backend/scripts/migrations/002_create_alarm_history.sql` | alarm_history 테이블 생성 SQL |

#### 사용법

```powershell
cd backend

# 상태 확인
python scripts/migrate_db.py --check

# 마이그레이션 실행
python scripts/migrate_db.py

# SQLAlchemy 기반 테이블 생성
python scripts/migrate_db.py --create-tables
```

---

## 3. 테스트 방법

### 3.1 펌웨어 빌드 및 플래시
```powershell
cd firmware_idf
.\build.ps1 -Target esp32s3 -Flash -Port COM5
```

### 3.2 백엔드 마이그레이션 및 실행
```powershell
cd backend
python scripts/migrate_db.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.3 웹에서 테스트
1. 장비 상세 페이지 접속
2. "보고 주기" 드롭다운으로 주기 변경
3. 알람 버튼 (비프음, 경고음, 긴급 알람) 클릭
4. `/alarm-history` API로 이력 확인

---

## 4. 참고 자료

- ESP-IDF FreeRTOS Timer: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/freertos.html
- FreeRTOS Task Stack Size: https://www.freertos.org/FAQMem.html
- SQLAlchemy Migrations: https://docs.sqlalchemy.org/en/20/core/metadata.html

---

## 5. 향후 개선 사항

1. **TTS (Text-to-Speech) 알람 구현**
   - 백엔드 TTS 서비스 연동
   - 펌웨어 PCM 스트리밍 수신

2. **알람 이력 프론트엔드 UI**
   - 알람 이력 목록 페이지
   - 필터링 및 검색 기능

3. **사용자 인증 연동**
   - 알람 이력에 실제 사용자 ID 기록
   - 권한별 접근 제어
