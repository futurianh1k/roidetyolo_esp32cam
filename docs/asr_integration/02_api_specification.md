# ASR API 명세서

**버전**: 1.0.0  
**작성일**: 2025-12-08  
**기준**: OpenAPI 3.0

---

## 📋 목차

1. [ASR 서버 API](#asr-서버-api)
2. [백엔드 프록시 API](#백엔드-프록시-api)
3. [WebSocket 프로토콜](#websocket-프로토콜)
4. [데이터 스키마](#데이터-스키마)
5. [에러 코드](#에러-코드)

---

## 🎯 ASR 서버 API

**Base URL**: `http://192.168.x.x:8001`

### 1. 세션 시작

**`POST /asr/session/start`**

음성인식 세션을 새로 생성합니다.

#### Request Body

```json
{
  "device_id": "cores3_01",
  "language": "auto",
  "sample_rate": 16000,
  "vad_enabled": true
}
```

| 필드        | 타입    | 필수 | 기본값 | 설명                                  |
| ----------- | ------- | ---- | ------ | ------------------------------------- |
| device_id   | string  | ✅   | -      | 장비 고유 ID                          |
| language    | string  | ❌   | "auto" | 언어 코드 (auto, ko, en, zh, ja, yue) |
| sample_rate | integer | ❌   | 16000  | 오디오 샘플레이트 (Hz)                |
| vad_enabled | boolean | ❌   | true   | VAD 활성화 여부                       |

#### Response

**Status**: `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "ws_url": "ws://192.168.x.x:8001/ws/asr/550e8400-e29b-41d4-a716-446655440000",
  "status": "ready",
  "message": "세션이 생성되었습니다. WebSocket으로 연결하세요."
}
```

| 필드       | 타입          | 설명                |
| ---------- | ------------- | ------------------- |
| session_id | string (UUID) | 생성된 세션 ID      |
| ws_url     | string (URL)  | WebSocket 연결 URL  |
| status     | string        | 세션 상태 ("ready") |
| message    | string        | 안내 메시지         |

#### Error Responses

| Status | 설명           | 응답 예시                                     |
| ------ | -------------- | --------------------------------------------- |
| 500    | 세션 생성 실패 | `{"detail": "세션 생성 실패: [에러 메시지]"}` |

#### 예제

**cURL**:

```bash
curl -X POST http://192.168.1.100:8001/asr/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "cores3_01",
    "language": "ko",
    "sample_rate": 16000,
    "vad_enabled": true
  }'
```

**Python**:

```python
import requests

response = requests.post('http://192.168.1.100:8001/asr/session/start',
    json={
        'device_id': 'cores3_01',
        'language': 'ko',
        'sample_rate': 16000,
        'vad_enabled': True
    })

session = response.json()
print(f"Session ID: {session['session_id']}")
print(f"WebSocket URL: {session['ws_url']}")
```

---

### 2. 세션 상태 조회

**`GET /asr/session/{session_id}/status`**

세션의 현재 상태를 조회합니다.

#### Path Parameters

| 파라미터   | 타입          | 필수 | 설명    |
| ---------- | ------------- | ---- | ------- |
| session_id | string (UUID) | ✅   | 세션 ID |

#### Response

**Status**: `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "cores3_01",
  "is_active": true,
  "is_processing": false,
  "segments_count": 5,
  "last_result": "안녕하세요",
  "created_at": "2025-12-08T10:30:00.123456",
  "language": "ko"
}
```

| 필드           | 타입              | 설명                      |
| -------------- | ----------------- | ------------------------- |
| session_id     | string            | 세션 ID                   |
| device_id      | string            | 장비 ID                   |
| is_active      | boolean           | 세션 활성 여부            |
| is_processing  | boolean           | 현재 음성 처리 중 여부    |
| segments_count | integer           | 인식된 음성 세그먼트 수   |
| last_result    | string (nullable) | 마지막 인식 결과          |
| created_at     | string (datetime) | 세션 생성 시각 (ISO 8601) |
| language       | string            | 언어 코드                 |

#### Error Responses

| Status | 설명                | 응답 예시                                             |
| ------ | ------------------- | ----------------------------------------------------- |
| 404    | 세션을 찾을 수 없음 | `{"detail": "세션을 찾을 수 없습니다: [session_id]"}` |

---

### 3. 세션 종료

**`POST /asr/session/{session_id}/stop`**

세션을 종료하고 리소스를 해제합니다.

#### Path Parameters

| 파라미터   | 타입          | 필수 | 설명    |
| ---------- | ------------- | ---- | ------- |
| session_id | string (UUID) | ✅   | 세션 ID |

#### Response

**Status**: `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "stopped",
  "message": "세션이 종료되었습니다.",
  "segments_count": 5
}
```

| 필드           | 타입    | 설명                  |
| -------------- | ------- | --------------------- |
| session_id     | string  | 종료된 세션 ID        |
| status         | string  | 상태 ("stopped")      |
| message        | string  | 안내 메시지           |
| segments_count | integer | 총 인식된 세그먼트 수 |

#### Error Responses

| Status | 설명                | 응답 예시                                             |
| ------ | ------------------- | ----------------------------------------------------- |
| 404    | 세션을 찾을 수 없음 | `{"detail": "세션을 찾을 수 없습니다: [session_id]"}` |

---

### 4. 활성 세션 목록

**`GET /asr/sessions`**

모든 활성 세션 목록을 조회합니다.

#### Response

**Status**: `200 OK`

```json
{
  "total": 2,
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "device_id": "cores3_01",
      "is_active": true,
      "is_processing": false,
      "segments_count": 5,
      "last_result": "안녕하세요",
      "created_at": "2025-12-08T10:30:00.123456",
      "language": "ko"
    },
    {
      "session_id": "660e9500-f30c-52e5-b827-557766550111",
      "device_id": "cores3_02",
      "is_active": true,
      "is_processing": true,
      "segments_count": 3,
      "last_result": "테스트",
      "created_at": "2025-12-08T10:32:15.789012",
      "language": "auto"
    }
  ]
}
```

---

### 5. 헬스 체크

**`GET /health`**

서버 상태를 확인합니다.

#### Response

**Status**: `200 OK`

```json
{
  "status": "healthy",
  "recognizer_loaded": true,
  "active_sessions": 2
}
```

---

## 🔄 백엔드 프록시 API

**Base URL**: `http://localhost:8000`

### 1. 장비 음성인식 시작

**`POST /asr/devices/{device_id}/session/start`**

장비의 음성인식 세션을 시작합니다.

#### Path Parameters

| 파라미터  | 타입    | 필수 | 설명                      |
| --------- | ------- | ---- | ------------------------- |
| device_id | integer | ✅   | 장비 ID (데이터베이스 PK) |

#### Request Body

```json
{
  "language": "auto",
  "vad_enabled": true
}
```

#### Response

**Status**: `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": 1,
  "device_name": "CoreS3-01",
  "ws_url": "ws://192.168.1.100:8001/ws/asr/550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "음성인식이 시작되었습니다."
}
```

#### 동작 순서

1. 장비가 온라인 상태인지 확인
2. ASR 서버에 세션 생성 요청
3. MQTT로 CoreS3에 `start_asr` 명령 전송
4. 세션 정보 응답

---

### 2. 장비 음성인식 종료

**`POST /asr/devices/{device_id}/session/stop`**

장비의 음성인식 세션을 종료합니다.

#### Path Parameters

| 파라미터  | 타입    | 필수 | 설명    |
| --------- | ------- | ---- | ------- |
| device_id | integer | ✅   | 장비 ID |

#### Request Body

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response

**Status**: `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": 1,
  "status": "stopped",
  "segments_count": 5
}
```

---

### 3. 세션 상태 조회

**`GET /asr/devices/{device_id}/session/status`**

장비의 현재 음성인식 세션 상태를 조회합니다.

#### Path Parameters

| 파라미터  | 타입    | 필수 | 설명    |
| --------- | ------- | ---- | ------- |
| device_id | integer | ✅   | 장비 ID |

#### Response

**Status**: `200 OK`

```json
{
  "device_id": 1,
  "device_name": "CoreS3-01",
  "has_active_session": true,
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "is_processing": false,
    "segments_count": 5,
    "last_result": "안녕하세요",
    "created_at": "2025-12-08T10:30:00.123456"
  }
}
```

---

## 🔌 WebSocket 프로토콜

### 1. CoreS3 ↔ ASR 서버

**URL**: `ws://192.168.x.x:8001/ws/asr/{session_id}`

#### 클라이언트 → 서버 메시지

##### 오디오 청크 전송

```json
{
  "type": "audio_chunk",
  "data": "AAABAAIAAwAEAAUA...==",
  "timestamp": 1234567890
}
```

| 필드      | 타입            | 필수 | 설명                                    |
| --------- | --------------- | ---- | --------------------------------------- |
| type      | string          | ✅   | 메시지 타입 ("audio_chunk")             |
| data      | string (Base64) | ✅   | 오디오 데이터 (16-bit PCM, 16kHz, 모노) |
| timestamp | integer         | ✅   | 타임스탬프 (ms)                         |

**오디오 형식**:

- 샘플레이트: 16000 Hz
- 비트 깊이: 16-bit signed integer
- 채널: 모노 (1 채널)
- 인코딩: Base64
- 청크 크기: 1024 samples (권장)

##### Ping (연결 유지)

```json
{
  "type": "ping"
}
```

---

#### 서버 → 클라이언트 메시지

##### 연결 확인

```json
{
  "type": "connected",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "WebSocket 연결 성공. 오디오 전송을 시작하세요."
}
```

##### 인식 결과

```json
{
  "type": "recognition_result",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "안녕하세요 반갑습니다",
  "timestamp": "2025-12-08 10:30:45",
  "duration": 2.3,
  "is_final": true,
  "is_emergency": false,
  "emergency_keywords": []
}
```

| 필드               | 타입          | 설명                            |
| ------------------ | ------------- | ------------------------------- |
| type               | string        | "recognition_result"            |
| session_id         | string        | 세션 ID                         |
| text               | string        | 인식된 텍스트                   |
| timestamp          | string        | 인식 시각 (YYYY-MM-DD HH:MM:SS) |
| duration           | float         | 음성 길이 (초)                  |
| is_final           | boolean       | 최종 결과 여부                  |
| is_emergency       | boolean       | 응급 상황 여부                  |
| emergency_keywords | array[string] | 감지된 응급 키워드 목록         |

##### 처리 중

```json
{
  "type": "processing",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "음성 감지 중..."
}
```

##### 에러

```json
{
  "type": "error",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "오디오 처리 오류: [상세 메시지]"
}
```

##### Pong (Ping 응답)

```json
{
  "type": "pong",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. Frontend ↔ 백엔드

**URL**: `ws://localhost:8000/ws/asr/monitor/{device_id}`

#### 서버 → 클라이언트 메시지

```json
{
  "type": "recognition_result",
  "device_id": 1,
  "device_name": "CoreS3-01",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "안녕하세요",
  "timestamp": "2025-12-08 10:30:45",
  "duration": 2.3,
  "is_emergency": false,
  "emergency_keywords": []
}
```

---

## 📦 데이터 스키마

### SessionStartRequest

```typescript
interface SessionStartRequest {
  device_id: string; // 장비 ID
  language?: string; // 언어 코드 (기본: "auto")
  sample_rate?: number; // 샘플레이트 (기본: 16000)
  vad_enabled?: boolean; // VAD 활성화 (기본: true)
}
```

### SessionStartResponse

```typescript
interface SessionStartResponse {
  session_id: string; // UUID
  ws_url: string; // WebSocket URL
  status: string; // "ready"
  message: string; // 안내 메시지
}
```

### SessionStatusResponse

```typescript
interface SessionStatusResponse {
  session_id: string; // UUID
  device_id: string; // 장비 ID
  is_active: boolean; // 활성 여부
  is_processing: boolean; // 처리 중 여부
  segments_count: number; // 세그먼트 수
  last_result: string | null; // 마지막 결과
  created_at: string; // ISO 8601 datetime
  language: string; // 언어 코드
}
```

### RecognitionResult

```typescript
interface RecognitionResult {
  type: "recognition_result";
  session_id: string;
  text: string;
  timestamp: string;
  duration: number;
  is_final: boolean;
  is_emergency: boolean;
  emergency_keywords: string[];
}
```

---

## ⚠️ 에러 코드

### HTTP 에러

| 코드 | 설명                  | 예시                  |
| ---- | --------------------- | --------------------- |
| 400  | 잘못된 요청           | 필수 파라미터 누락    |
| 404  | 리소스를 찾을 수 없음 | 존재하지 않는 세션 ID |
| 500  | 서버 내부 오류        | 모델 로딩 실패        |

### WebSocket Close Codes

| 코드 | 설명                | 사유                     |
| ---- | ------------------- | ------------------------ |
| 1000 | 정상 종료           | 클라이언트가 연결을 닫음 |
| 4004 | 세션을 찾을 수 없음 | 잘못된 session_id        |
| 4010 | 인증 실패           | (향후 구현)              |

---

## 📝 사용 예제

### Python 클라이언트 전체 플로우

```python
import requests
import asyncio
import websockets
import json
import base64
import numpy as np

class ASRClient:
    def __init__(self, api_url="http://192.168.1.100:8001"):
        self.api_url = api_url
        self.session_id = None
        self.ws_url = None

    def start_session(self, device_id="test_device"):
        """세션 시작"""
        response = requests.post(
            f"{self.api_url}/asr/session/start",
            json={"device_id": device_id}
        )
        data = response.json()

        self.session_id = data['session_id']
        self.ws_url = data['ws_url']

        return data

    async def stream_audio(self, audio_data, sample_rate=16000):
        """오디오 스트리밍"""
        async with websockets.connect(self.ws_url) as ws:
            # 연결 확인
            welcome = await ws.recv()
            print(f"Connected: {welcome}")

            # 오디오 전송
            chunk_size = 1024
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]

                # int16 변환
                chunk_int16 = (chunk * 32768).astype(np.int16)

                # Base64 인코딩
                chunk_bytes = chunk_int16.tobytes()
                chunk_base64 = base64.b64encode(chunk_bytes).decode()

                # 전송
                message = {
                    "type": "audio_chunk",
                    "data": chunk_base64,
                    "timestamp": i / sample_rate
                }
                await ws.send(json.dumps(message))

                # 결과 수신
                try:
                    response = await asyncio.wait_for(
                        ws.recv(), timeout=0.1
                    )
                    result = json.loads(response)

                    if result['type'] == 'recognition_result':
                        print(f"Result: {result['text']}")

                except asyncio.TimeoutError:
                    pass

                await asyncio.sleep(chunk_size / sample_rate)

    def stop_session(self):
        """세션 종료"""
        response = requests.post(
            f"{self.api_url}/asr/session/{self.session_id}/stop"
        )
        return response.json()

# 사용 예제
async def main():
    client = ASRClient()

    # 1. 세션 시작
    client.start_session("cores3_01")

    # 2. 오디오 로드
    audio = np.random.randn(16000 * 5).astype(np.float32)  # 5초

    # 3. 스트리밍
    await client.stream_audio(audio)

    # 4. 세션 종료
    client.stop_session()

asyncio.run(main())
```

---

## 🔗 참고 자료

- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket Protocol RFC6455](https://datatracker.ietf.org/doc/html/rfc6455)
- [Base64 Encoding](https://tools.ietf.org/html/rfc4648)

---

**문서 버전**: 1.0.0  
**최종 수정**: 2025-12-08
