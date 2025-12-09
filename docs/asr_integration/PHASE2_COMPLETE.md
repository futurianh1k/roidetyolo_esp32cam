# Phase 2 완료 보고서 - 백엔드 수정

**완료일**: 2025-12-08  
**소요 시간**: 약 1시간  
**상태**: ✅ 완료

---

## 📋 작업 요약

Phase 2에서는 FastAPI 백엔드를 수정하여 ASR 서버와 CoreS3 장비를 연결하는 프록시 API를 구현했습니다.

---

## 📦 생성된 파일 (3개)

### 1. backend/app/schemas/asr.py (180 라인)

**목적**: ASR 관련 데이터 스키마 정의

**Pydantic 모델 (7개)**:

| 클래스                     | 용도           | 필드 수 |
| -------------------------- | -------------- | ------- |
| `ASRSessionStartRequest`   | 세션 시작 요청 | 2       |
| `ASRSessionStartResponse`  | 세션 시작 응답 | 6       |
| `ASRSessionStopRequest`    | 세션 종료 요청 | 1       |
| `ASRSessionStopResponse`   | 세션 종료 응답 | 4       |
| `ASRSessionStatus`         | 세션 상태      | 6       |
| `ASRSessionStatusResponse` | 세션 상태 응답 | 4       |
| `RecognitionResult`        | 음성인식 결과  | 10      |

**주요 특징**:

- ✅ Field 설명 (description) 포함
- ✅ JSON 예제 (json_schema_extra) 포함
- ✅ 타입 안정성 (Type Hints)
- ✅ API 문서 자동 생성

---

### 2. backend/app/services/asr_service.py (280 라인)

**목적**: ASR 서버와 HTTP 통신하는 클라이언트 서비스

**주요 클래스**:

#### ASRService

```python
class ASRService:
    """ASR 서버 클라이언트 서비스"""

    def __init__(self, asr_server_url, timeout=30.0, max_retries=3)

    async def _request(method, endpoint, **kwargs)
        # HTTP 요청 (재시도 로직 포함)
        # 최대 3회 재시도
        # 1초 간격으로 재시도

    async def create_session(device_id, language, sample_rate, vad_enabled)
        # ASR 세션 생성
        # POST /asr/session/start

    async def get_session_status(session_id)
        # 세션 상태 조회
        # GET /asr/session/{id}/status

    async def stop_session(session_id)
        # 세션 종료
        # POST /asr/session/{id}/stop

    async def list_sessions()
        # 모든 세션 목록
        # GET /asr/sessions

    async def health_check()
        # ASR 서버 헬스 체크
        # GET /health
```

**주요 기능**:

- ✅ 재시도 로직 (최대 3회, 1초 간격)
- ✅ 에러 처리 (HTTPStatusError, RequestError)
- ✅ 로깅 (INFO, DEBUG, ERROR 레벨)
- ✅ 타임아웃 설정 (기본 30초)

**전역 인스턴스**:

```python
asr_service = ASRService()  # 싱글톤

# 편의 함수
create_asr_session(device_id, language)
stop_asr_session(session_id)
get_asr_session_status(session_id)
```

---

### 3. backend/app/api/asr.py (300 라인)

**목적**: ASR API 라우터 (프론트엔드용 API 엔드포인트)

**API 엔드포인트 (5개)**:

#### 1. POST /asr/devices/{device_id}/session/start

**설명**: 장비 음성인식 세션 시작

**동작 순서**:

1. 장비 확인 (DB 조회)
2. 장비 온라인 상태 확인
3. 이미 활성 세션 있는지 확인
4. ASR 서버에 세션 생성 요청 (HTTP)
5. MQTT로 CoreS3에 `start_asr` 명령 전송
6. 세션 상태 저장 (메모리)
7. 응답 반환

**MQTT 메시지**:

```json
{
  "command": "microphone",
  "action": "start_asr",
  "session_id": "uuid-xxxx",
  "ws_url": "ws://192.168.1.100:8001/ws/asr/uuid-xxxx",
  "language": "ko",
  "request_id": "asr_start_1_uuid"
}
```

**에러 처리**:

- 404: 장비를 찾을 수 없음
- 400: 장비가 오프라인
- 409: 이미 활성 세션 존재
- 500: ASR 서버 또는 MQTT 통신 실패

#### 2. POST /asr/devices/{device_id}/session/stop

**설명**: 장비 음성인식 세션 종료

**동작 순서**:

1. 장비 확인
2. 활성 세션 확인
3. MQTT로 CoreS3에 `stop_asr` 명령 전송
4. ASR 서버에 세션 종료 요청
5. 세션 상태 제거
6. 응답 반환

#### 3. GET /asr/devices/{device_id}/session/status

**설명**: 장비 음성인식 세션 상태 조회

**반환 정보**:

- device_id, device_name
- has_active_session
- session 상태 (is_active, is_processing, segments_count, last_result)

#### 4. GET /asr/sessions

**설명**: 모든 활성 세션 목록 조회 (관리자용)

#### 5. GET /asr/health

**설명**: ASR 서버 헬스 체크

---

## 🔧 수정된 파일 (5개)

### 1. backend/app/main.py

**변경 내용**:

- ASR 라우터 import 추가
- `app.include_router(asr.router)` 등록

**코드**:

```python
from app.api import auth, users, devices, control, audio, websocket, asr
...
app.include_router(asr.router)  # ASR (음성인식) API
```

---

### 2. backend/app/config.py

**변경 내용**:

- ASR_SERVER_URL 설정 추가

**코드**:

```python
# ASR (음성인식 서버)
ASR_SERVER_URL: str = "http://localhost:8001"  # ASR WebSocket API 서버 URL
```

**환경변수**:

```env
# .env 파일에 추가
ASR_SERVER_URL=http://192.168.1.100:8001
```

---

### 3. backend/app/services/**init**.py

**변경 내용**:

- asr_service, ASRService export 추가

**코드**:

```python
from app.services.asr_service import asr_service, ASRService

__all__ = [
    ...,
    "asr_service",
    "ASRService",
]
```

---

### 4. backend/app/schemas/**init**.py

**변경 내용**:

- ASR 스키마 7개 export 추가

**코드**:

```python
from app.schemas.asr import (
    ASRSessionStartRequest,
    ASRSessionStartResponse,
    ASRSessionStopRequest,
    ASRSessionStopResponse,
    ASRSessionStatus,
    ASRSessionStatusResponse,
    RecognitionResult,
)
```

---

### 5. backend/app/schemas/control.py

**변경 내용**:

- MicrophoneControlRequest에 액션 추가

**코드**:

```python
class MicrophoneControlRequest(BaseModel):
    """
    마이크 제어 요청

    액션:
    - start: 일반 마이크 시작
    - pause: 일시정지
    - stop: 정지
    - start_asr: 음성인식 모드로 시작 (ASR 서버 연동)  # ✨ NEW
    - stop_asr: 음성인식 모드 종료                    # ✨ NEW
    """
    action: Literal["start", "pause", "stop", "start_asr", "stop_asr"]
```

---

## 🔄 데이터 플로우

### 세션 시작 플로우

```
[프론트엔드]
    │
    └─ POST /asr/devices/1/session/start
       {language: "ko", vad_enabled: true}
              │
              ▼
    [백엔드 API: asr.py]
              │
              ├─ ① 장비 확인 (DB)
              │    - 존재 여부
              │    - 온라인 상태
              │    - 이미 세션 있는지
              │
              ├─ ② ASR 서버에 세션 생성 요청
              │    POST http://192.168.1.100:8001/asr/session/start
              │    → {session_id, ws_url}
              │
              ├─ ③ MQTT 명령 전송
              │    TOPIC: devices/cores3_01/control/microphone
              │    PAYLOAD: {
              │      command: "microphone",
              │      action: "start_asr",
              │      session_id: "...",
              │      ws_url: "ws://...",
              │      language: "ko"
              │    }
              │
              ├─ ④ 세션 상태 저장
              │    active_sessions[device_id] = session_id
              │
              └─ ⑤ 응답 반환
                   {
                     session_id, device_id, device_name,
                     ws_url, status, message
                   }
```

---

## 📊 API 테스트

### cURL 예제

```bash
# 1. ASR 서버 헬스 체크
curl http://localhost:8000/asr/health

# 2. 세션 시작
curl -X POST http://localhost:8000/asr/devices/1/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "language": "ko",
    "vad_enabled": true
  }'

# 3. 세션 상태 조회
curl http://localhost:8000/asr/devices/1/session/status

# 4. 세션 종료
curl -X POST http://localhost:8000/asr/devices/1/session/stop \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'

# 5. 모든 세션 목록
curl http://localhost:8000/asr/sessions
```

---

## 🔐 보안 고려사항

### 인증 (현재 비활성화, TODO)

```python
# TODO: 로그인 수정 후 활성화
# current_user: User = Depends(require_operator)
```

### 입력 검증

- ✅ Pydantic 모델로 자동 검증
- ✅ 장비 존재 여부 확인
- ✅ 장비 온라인 상태 확인
- ✅ 중복 세션 방지

### 에러 처리

- ✅ try-except로 모든 예외 처리
- ✅ 상세한 에러 로깅
- ✅ 사용자 친화적 에러 메시지

---

## 🧪 테스트 방법

### 1. ASR 서버 실행 (먼저!)

```bash
# RK3588 보드 또는 로컬
cd backend/rk3588asr
taskset 0x0F python asr_api_server.py --host 0.0.0.0 --port 8001
```

### 2. 백엔드 서버 실행

```bash
cd backend
source ../venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. API 문서 확인

- http://localhost:8000/docs
- `/asr` 카테고리 확인

### 4. API 테스트

```bash
# Python으로 테스트
python -c "
import requests

# 세션 시작
r = requests.post('http://localhost:8000/asr/devices/1/session/start',
                  json={'language': 'ko', 'vad_enabled': True})
print(r.json())

# 세션 상태
session_id = r.json()['session_id']
r = requests.get(f'http://localhost:8000/asr/devices/1/session/status')
print(r.json())

# 세션 종료
r = requests.post(f'http://localhost:8000/asr/devices/1/session/stop',
                  json={'session_id': session_id})
print(r.json())
"
```

---

## 🔍 주요 로직 설명

### 세션 상태 관리

```python
# 메모리 기반 세션 관리
active_sessions: Dict[int, str] = {}  # {device_id: session_id}

# 세션 시작 시
active_sessions[device_id] = session_id

# 세션 종료 시
del active_sessions[device_id]
```

**장점**:

- 빠른 조회
- 간단한 구조

**단점**:

- 서버 재시작 시 세션 정보 손실
- TODO: 데이터베이스에 저장 (향후 개선)

---

### 재시도 로직

```python
async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
    """HTTP 요청 (재시도 로직 포함)"""

    for attempt in range(self.max_retries):  # 최대 3회
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error(f"시도 {attempt + 1}/{self.max_retries}: {e}")
            if attempt == self.max_retries - 1:
                raise
            await asyncio.sleep(1)  # 1초 대기
```

**특징**:

- 네트워크 불안정성 대응
- 지수 백오프 없이 고정 1초 간격 (간단함)
- 모든 에러 로깅

---

### MQTT 명령 전송

```python
# start_asr 명령
mqtt_topic = f"devices/{device.device_id}/control/microphone"
mqtt_payload = {
    "command": "microphone",
    "action": "start_asr",          # ✨ NEW 액션
    "session_id": session_id,       # ASR 세션 ID
    "ws_url": ws_url,                # WebSocket URL
    "language": language,            # 언어 코드
    "request_id": f"asr_start_{device_id}_{session_id[:8]}"
}

mqtt_service.publish(mqtt_topic, json.dumps(mqtt_payload))
```

**CoreS3가 받을 정보**:

- session_id: ASR 서버 세션 ID
- ws_url: 연결할 WebSocket URL
- language: 음성인식 언어 설정

---

## 📡 API 엔드포인트 상세

### POST /asr/devices/{device_id}/session/start

**요청**:

```json
{
  "language": "ko",
  "vad_enabled": true
}
```

**응답 (성공)**:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": 1,
  "device_name": "CoreS3-01",
  "ws_url": "ws://192.168.1.100:8001/ws/asr/550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "음성인식이 시작되었습니다. CoreS3 장비가 자동으로 연결됩니다."
}
```

**응답 (에러)**:

```json
// 404 - 장비 없음
{"detail": "장비를 찾을 수 없습니다"}

// 400 - 장비 오프라인
{"detail": "장비가 오프라인 상태입니다"}

// 409 - 이미 세션 존재
{"detail": "이미 활성 세션이 존재합니다: uuid-xxxx"}

// 500 - 서버 에러
{"detail": "음성인식 세션 시작에 실패했습니다: [에러 메시지]"}
```

---

## ✅ 달성한 목표

### 프록시 API 구현

- ✅ FastAPI 라우터 생성
- ✅ ASR 서버 클라이언트 구현
- ✅ 데이터 스키마 정의
- ✅ 에러 처리 및 로깅

### MQTT 명령 확장

- ✅ `start_asr` 액션 추가
- ✅ `stop_asr` 액션 추가
- ✅ 세션 ID 및 WebSocket URL 전달

### 코드 품질

- ✅ 타입 힌트 (Type Hints)
- ✅ 주석 (Docstrings)
- ✅ 에러 처리
- ✅ 로깅

---

## 🚀 다음 단계: Phase 3

**Phase 3: CoreS3 펌웨어 수정** (3-4시간)

### 작업 내용

1. **ArduinoWebsockets 라이브러리 추가**

   - `platformio.ini` 수정
   - `gilmaimon/ArduinoWebsockets` 추가

2. **WebSocket 모듈 구현**

   - `firmware/include/websocket_module.h`
   - `firmware/src/websocket_module.cpp`
   - WebSocket 클라이언트 관리
   - 메시지 송수신

3. **오디오 스트리밍 구현**

   - `firmware/src/audio_module.cpp` 수정
   - I2S 마이크 → int16 PCM 캡처
   - Base64 인코딩
   - WebSocket으로 전송

4. **MQTT 핸들러 확장**

   - `firmware/src/mqtt_module.cpp` 수정
   - `handleMicrophoneControl("start_asr")` 구현
   - `handleMicrophoneControl("stop_asr")` 구현

5. **인식 결과 수신 및 표시**
   - WebSocket 메시지 수신
   - JSON 파싱
   - 디스플레이에 텍스트 표시

---

## 📝 변경 사항 요약

| 구분 | 파일 수 | 라인 수 |
| ---- | ------- | ------- |
| 생성 | 3       | 760     |
| 수정 | 5       | ~50     |
| 합계 | 8       | 810     |

---

## 🎉 Phase 2 완료!

백엔드 프록시 API가 완전히 구축되었습니다.

**준비 완료**:

- ✅ ASR 서버 ↔ 백엔드 통신
- ✅ 백엔드 ↔ CoreS3 MQTT 명령

**다음 필요**:

- 📝 CoreS3 ↔ ASR 서버 WebSocket 통신 (Phase 3)
- 📝 프론트엔드 UI (Phase 4)

---

**작성일**: 2025-12-08  
**상태**: ✅ 완료  
**다음**: Phase 3 (펌웨어)
