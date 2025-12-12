# Phase 3-1: ASR 결과 저장 완료 보고서

**작성일:** 2025-12-10  
**작업 내용:** ASR 결과 데이터베이스 저장 및 조회 기능 구현  
**상태:** ✅ 완료

---

## 📊 작업 요약

### 목표
- ASR 결과를 데이터베이스에 저장
- 결과 조회 API 추가
- 검색 및 필터링 기능 구현
- 통계 API 추가

### 결과
- ✅ 데이터베이스 모델 생성 (`ASRResult`)
- ✅ 결과 저장 로직 구현
- ✅ 조회 API 3개 추가
- ✅ 검색 및 필터링 기능 구현
- ✅ 통계 API 추가

---

## 📁 구현된 파일

### 1. `backend/app/models/asr_result.py` (신규 생성)

**ASR 결과 데이터베이스 모델**

**주요 필드:**
- `id`: 기본 키
- `device_id`: 장비 ID (외래 키)
- `session_id`: ASR 세션 ID
- `text`: 인식된 텍스트
- `timestamp`: 인식 시각
- `duration`: 음성 길이 (초)
- `is_emergency`: 응급 상황 여부
- `emergency_keywords`: 응급 키워드 (JSON 형식)
- `created_at`: 생성 시각

**인덱스:**
- `idx_device_created`: 장비별 + 시간별 조회 최적화
- `idx_emergency_created`: 응급 상황별 + 시간별 조회 최적화

---

### 2. `backend/app/schemas/asr_result.py` (신규 생성)

**Pydantic 스키마**

**주요 스키마:**
- `ASRResultResponse`: ASR 결과 응답
- `ASRResultListResponse`: ASR 결과 목록 응답
- `ASRResultSearchRequest`: 검색 요청
- `ASRResultStatsResponse`: 통계 응답

---

### 3. `backend/app/api/asr.py` (업데이트)

**추가된 기능:**

#### 3-1. 결과 저장 로직
- `receive_asr_result()` 함수에 데이터베이스 저장 로직 추가
- 응급 키워드를 JSON 형식으로 저장

#### 3-2. 조회 API
- `GET /asr/results`: 결과 목록 조회 (검색 및 필터링)
- `GET /asr/results/{result_id}`: 특정 결과 조회
- `GET /asr/results/stats`: 통계 조회

**검색 및 필터링 옵션:**
- `device_id`: 장비 ID로 필터링
- `session_id`: 세션 ID로 필터링
- `is_emergency`: 응급 상황 여부로 필터링
- `text_query`: 텍스트 검색 (부분 일치)
- `start_date`: 시작 날짜 (YYYY-MM-DD)
- `end_date`: 종료 날짜 (YYYY-MM-DD)
- `page`: 페이지 번호
- `page_size`: 페이지 크기 (최대 100)

---

## 🔍 API 사용 예시

### 1. 결과 목록 조회

```bash
GET /asr/results?device_id=1&page=1&page_size=20
```

**응답:**
```json
{
    "total": 100,
    "page": 1,
    "page_size": 20,
    "results": [
        {
            "id": 1,
            "device_id": 1,
            "device_name": "CoreS3-01",
            "session_id": "uuid-xxx",
            "text": "도와줘 사람이 쓰러졌어",
            "timestamp": "2025-12-10 10:00:00",
            "duration": 2.3,
            "is_emergency": true,
            "emergency_keywords": ["도와줘", "쓰러졌어"],
            "created_at": "2025-12-10T10:00:00"
        }
    ]
}
```

### 2. 텍스트 검색

```bash
GET /asr/results?text_query=도와줘&is_emergency=true
```

### 3. 날짜 범위 검색

```bash
GET /asr/results?start_date=2025-12-01&end_date=2025-12-10
```

### 4. 통계 조회

```bash
GET /asr/results/stats?device_id=1&start_date=2025-12-01&end_date=2025-12-10
```

**응답:**
```json
{
    "total_count": 100,
    "emergency_count": 5,
    "total_duration": 230.5,
    "average_duration": 2.305,
    "device_stats": [
        {
            "device_id": 1,
            "device_name": "CoreS3-01",
            "count": 50,
            "total_duration": 115.0,
            "emergency_count": 3
        }
    ]
}
```

### 5. 특정 결과 조회

```bash
GET /asr/results/1
```

---

## ✅ 완료된 작업

- [x] ASR 결과 데이터베이스 모델 추가 (`ASRResult`)
- [x] Device 모델에 relationship 추가
- [x] 모델을 `__init__.py`에 등록
- [x] 결과 저장 로직 구현 (`receive_asr_result`)
- [x] 결과 조회 API 추가 (`GET /asr/results`)
- [x] 특정 결과 조회 API 추가 (`GET /asr/results/{result_id}`)
- [x] 통계 API 추가 (`GET /asr/results/stats`)
- [x] 검색 및 필터링 기능 구현
- [x] Pydantic 스키마 생성
- [x] 스키마를 `__init__.py`에 등록

---

## 📊 데이터베이스 마이그레이션

**주의:** 데이터베이스 마이그레이션이 필요합니다.

```bash
# Alembic 마이그레이션 생성
alembic revision --autogenerate -m "Add ASR result table"

# 마이그레이션 적용
alembic upgrade head
```

또는 직접 SQL 실행:

```sql
CREATE TABLE asr_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    timestamp VARCHAR(50) NOT NULL,
    duration FLOAT NOT NULL,
    is_emergency BOOLEAN NOT NULL DEFAULT 0,
    emergency_keywords TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX idx_device_created ON asr_results(device_id, created_at);
CREATE INDEX idx_emergency_created ON asr_results(is_emergency, created_at);
CREATE INDEX ix_asr_results_id ON asr_results(id);
CREATE INDEX ix_asr_results_device_id ON asr_results(device_id);
CREATE INDEX ix_asr_results_session_id ON asr_results(session_id);
CREATE INDEX ix_asr_results_is_emergency ON asr_results(is_emergency);
CREATE INDEX ix_asr_results_created_at ON asr_results(created_at);
```

---

## 🔍 다음 단계

### Phase 3-2: 응급 상황 알림 개선
- 알림 우선순위 설정
- 알림 이력 저장
- 알림 설정 UI

### Phase 3-3: 대시보드 개선
- ASR 통계 차트
- 응급 상황 이력
- 실시간 모니터링

---

**완료일:** 2025-12-10  
**다음 작업:** Phase 3-2 (응급 상황 알림 개선)

