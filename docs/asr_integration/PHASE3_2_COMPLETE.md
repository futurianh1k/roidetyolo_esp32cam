# Phase 3-2: 응급 상황 알림 개선 완료 보고서

**작성일:** 2025-12-10  
**작업 내용:** 응급 상황 알림 우선순위 설정, 이력 저장, 조회 API 구현  
**상태:** ✅ 완료

---

## 📊 작업 요약

### 목표
- 응급 상황 알림 이력 저장
- 우선순위 설정 기능
- 알림 조회 및 통계 API
- 알림 확인 처리 기능

### 결과
- ✅ 응급 상황 알림 모델 생성 (`EmergencyAlert`)
- ✅ 우선순위 계산 로직 구현
- ✅ 알림 이력 저장 로직 구현
- ✅ 알림 조회 API 3개 추가
- ✅ 알림 통계 API 추가
- ✅ 알림 확인 처리 API 추가

---

## 📁 구현된 파일

### 1. `backend/app/models/emergency_alert.py` (신규 생성)

**응급 상황 알림 데이터베이스 모델**

**주요 필드:**
- `id`: 기본 키
- `device_id`: 장비 ID (외래 키)
- `asr_result_id`: ASR 결과 ID (외래 키, 선택)
- `recognized_text`: 인식된 텍스트
- `emergency_keywords`: 응급 키워드 (JSON 형식)
- `priority`: 우선순위 (LOW, MEDIUM, HIGH, CRITICAL)
- `status`: 상태 (PENDING, SENT, FAILED, ACKNOWLEDGED)
- `api_endpoint`: API 엔드포인트
- `api_response`: API 응답
- `sent_at`: 전송 시각
- `acknowledged_at`: 확인 시각
- `acknowledged_by`: 확인한 사용자 ID

**우선순위 계산 규칙:**
- **CRITICAL**: "쓰러졌어", "의식없어", "심장마비", "호흡곤란"
- **HIGH**: "도와줘", "구조", "응급", "위험"
- **MEDIUM**: "아파", "불편", "도움"
- **LOW**: 기타

---

### 2. `backend/app/services/emergency_alert_service.py` (신규 생성)

**응급 상황 알림 서비스**

**주요 함수:**
- `calculate_priority()`: 키워드 기반 우선순위 계산
- `create_emergency_alert()`: 알림 이력 생성
- `update_alert_status()`: 알림 상태 업데이트
- `acknowledge_alert()`: 알림 확인 처리

---

### 3. `backend/app/schemas/emergency_alert.py` (신규 생성)

**Pydantic 스키마**

**주요 스키마:**
- `EmergencyAlertResponse`: 알림 응답
- `EmergencyAlertListResponse`: 알림 목록 응답
- `EmergencyAlertSearchRequest`: 검색 요청
- `EmergencyAlertStatsResponse`: 통계 응답

---

### 4. `backend/app/api/asr.py` (업데이트)

**추가된 기능:**

#### 4-1. 알림 이력 저장
- `receive_asr_result()` 함수에 알림 이력 저장 로직 추가
- 응급 상황 감지 시 자동으로 알림 이력 생성

#### 4-2. 알림 조회 API
- `GET /asr/emergency-alerts`: 알림 목록 조회 (검색 및 필터링)
- `GET /asr/emergency-alerts/stats`: 알림 통계 조회
- `POST /asr/emergency-alerts/{alert_id}/acknowledge`: 알림 확인 처리

**검색 및 필터링 옵션:**
- `device_id`: 장비 ID로 필터링
- `priority`: 우선순위로 필터링
- `status`: 상태로 필터링
- `start_date`: 시작 날짜 (YYYY-MM-DD)
- `end_date`: 종료 날짜 (YYYY-MM-DD)
- `page`: 페이지 번호
- `page_size`: 페이지 크기 (최대 100)

---

## 🔍 API 사용 예시

### 1. 알림 목록 조회

```bash
GET /asr/emergency-alerts?priority=high&status=pending&page=1&page_size=20
```

**응답:**
```json
{
    "total": 50,
    "page": 1,
    "page_size": 20,
    "alerts": [
        {
            "id": 1,
            "device_id": 1,
            "device_name": "CoreS3-01",
            "asr_result_id": 100,
            "recognized_text": "도와줘 사람이 쓰러졌어",
            "emergency_keywords": ["도와줘", "쓰러졌어"],
            "priority": "critical",
            "status": "sent",
            "api_endpoint": "http://api.example.com/emergency",
            "api_response": "Success",
            "sent_at": "2025-12-10T10:00:00",
            "created_at": "2025-12-10T10:00:00",
            "acknowledged_at": null,
            "acknowledged_by": null,
            "acknowledged_by_username": null
        }
    ]
}
```

### 2. 알림 통계 조회

```bash
GET /asr/emergency-alerts/stats?device_id=1&start_date=2025-12-01&end_date=2025-12-10
```

**응답:**
```json
{
    "total_count": 100,
    "by_priority": {
        "low": 20,
        "medium": 30,
        "high": 35,
        "critical": 15
    },
    "by_status": {
        "pending": 5,
        "sent": 90,
        "failed": 3,
        "acknowledged": 2
    },
    "by_device": [
        {
            "device_id": 1,
            "device_name": "CoreS3-01",
            "count": 50
        }
    ],
    "recent_alerts": [
        {
            "id": 100,
            "device_id": 1,
            "priority": "critical",
            "status": "sent",
            "created_at": "2025-12-10T10:00:00"
        }
    ]
}
```

### 3. 알림 확인 처리

```bash
POST /asr/emergency-alerts/1/acknowledge
```

**응답:**
```json
{
    "status": "success",
    "message": "알림이 확인 처리되었습니다",
    "alert_id": 1
}
```

---

## ✅ 완료된 작업

- [x] 응급 상황 알림 모델 추가 (`EmergencyAlert`)
- [x] 우선순위 열거형 정의 (`AlertPriority`)
- [x] 상태 열거형 정의 (`AlertStatus`)
- [x] Device 모델에 relationship 추가
- [x] User 모델에 relationship 추가
- [x] 모델을 `__init__.py`에 등록
- [x] 우선순위 계산 로직 구현
- [x] 알림 이력 저장 로직 구현 (`receive_asr_result`)
- [x] 알림 조회 API 추가 (`GET /asr/emergency-alerts`)
- [x] 알림 통계 API 추가 (`GET /asr/emergency-alerts/stats`)
- [x] 알림 확인 처리 API 추가 (`POST /asr/emergency-alerts/{alert_id}/acknowledge`)
- [x] Pydantic 스키마 생성
- [x] 응급 상황 알림 서비스 생성

---

## 📊 데이터베이스 마이그레이션

**주의:** 데이터베이스 마이그레이션이 필요합니다.

```sql
CREATE TABLE emergency_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    asr_result_id INTEGER,
    recognized_text TEXT NOT NULL,
    emergency_keywords TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    api_endpoint VARCHAR(255),
    api_response TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by INTEGER,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (asr_result_id) REFERENCES asr_results(id) ON DELETE SET NULL,
    FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_device_priority_created ON emergency_alerts(device_id, priority, created_at);
CREATE INDEX idx_status_created ON emergency_alerts(status, created_at);
CREATE INDEX ix_emergency_alerts_id ON emergency_alerts(id);
CREATE INDEX ix_emergency_alerts_device_id ON emergency_alerts(device_id);
CREATE INDEX ix_emergency_alerts_asr_result_id ON emergency_alerts(asr_result_id);
CREATE INDEX ix_emergency_alerts_priority ON emergency_alerts(priority);
CREATE INDEX ix_emergency_alerts_status ON emergency_alerts(status);
CREATE INDEX ix_emergency_alerts_created_at ON emergency_alerts(created_at);
```

---

## 🔍 다음 단계

### Phase 3-3: 대시보드 개선
- ASR 통계 차트
- 응급 상황 이력 표시
- 실시간 모니터링

---

**완료일:** 2025-12-10  
**다음 작업:** Phase 3-3 (대시보드 개선)

