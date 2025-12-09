# ASR 시스템 함수 상세 문서

**버전**: 1.0.0  
**작성일**: 2025-12-08

---

## 📋 목차

1. [ASR 서버 클래스 및 함수](#asr-서버-클래스-및-함수)
2. [세션 관리](#세션-관리)
3. [오디오 처리](#오디오-처리)
4. [WebSocket 핸들러](#websocket-핸들러)
5. [유틸리티 함수](#유틸리티-함수)

---

## 🎯 ASR 서버 클래스 및 함수

### 1. SessionManager

**위치**: `backend/rk3588asr/asr_api_server.py`

**설명**: 전역 세션 관리자 (싱글톤 패턴)

#### 클래스 정의

```python
class SessionManager:
    """
    세션 관리자 (싱글톤)

    모든 음성인식 세션을 중앙에서 관리합니다.
    메모리에서 세션 목록을 유지하며, 생성/조회/삭제 기능을 제공합니다.

    Attributes:
        sessions (Dict[str, ASRSession]): 세션 ID를 키로 하는 세션 딕셔너리

    Note:
        싱글톤 패턴으로 구현되어 애플리케이션 전체에서 하나의 인스턴스만 존재합니다.
    """
```

#### 메서드

##### `__new__(cls)`

**목적**: 싱글톤 인스턴스 생성

**동작**:

1. 클래스 변수 `_instance`가 None인지 확인
2. None이면 새 인스턴스 생성 후 `_instance`에 저장
3. 기존 인스턴스 반환

**반환값**: `SessionManager` 인스턴스

**예제**:

```python
manager1 = SessionManager()
manager2 = SessionManager()
assert manager1 is manager2  # True (같은 인스턴스)
```

---

##### `create_session(device_id, language, sample_rate, vad_enabled)`

**목적**: 새 음성인식 세션 생성

**파라미터**:
| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| device_id | str | - | 장비 고유 ID |
| language | str | "auto" | 언어 코드 (auto, ko, en, zh, ja, yue) |
| sample_rate | int | 16000 | 오디오 샘플레이트 (Hz) |
| vad_enabled | bool | True | VAD 활성화 여부 |

**반환값**: `ASRSession` 객체

**동작 순서**:

1. UUID로 고유한 세션 ID 생성
2. ASRSession 인스턴스 생성
3. sessions 딕셔너리에 추가
4. 로그 기록
5. ASRSession 반환

**예외**:

- `RuntimeError`: recognizer가 초기화되지 않은 경우

**예제**:

```python
manager = SessionManager()

# 세션 생성
session = manager.create_session(
    device_id="cores3_01",
    language="ko",
    sample_rate=16000,
    vad_enabled=True
)

print(f"Session created: {session.session_id}")
```

**로그 출력**:

```
2025-12-08 10:30:00 - INFO - ✅ ASR 세션 생성: 550e8400-e29b-41d4-a716-446655440000 (device: cores3_01)
2025-12-08 10:30:00 - INFO - 📝 세션 등록: 550e8400-e29b-41d4-a716-446655440000 (총 1개)
```

---

##### `get_session(session_id)`

**목적**: 세션 ID로 세션 조회

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| session_id | str | 조회할 세션 ID (UUID) |

**반환값**:

- `ASRSession` 객체 (세션이 존재하는 경우)
- `None` (세션이 없는 경우)

**예제**:

```python
session = manager.get_session("550e8400-e29b-41d4-a716-446655440000")

if session:
    print(f"Session found: {session.device_id}")
else:
    print("Session not found")
```

---

##### `remove_session(session_id)`

**목적**: 세션 종료 및 제거

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| session_id | str | 제거할 세션 ID |

**반환값**: None

**동작 순서**:

1. 세션 ID 존재 여부 확인
2. 세션의 `stop()` 메서드 호출 (VAD Processor 종료)
3. sessions 딕셔너리에서 삭제
4. 로그 기록

**예제**:

```python
manager.remove_session("550e8400-e29b-41d4-a716-446655440000")
```

**로그 출력**:

```
2025-12-08 10:35:00 - INFO - 🛑 세션 종료: 550e8400-e29b-41d4-a716-446655440000
2025-12-08 10:35:00 - INFO - 🗑️ 세션 제거: 550e8400-e29b-41d4-a716-446655440000 (남은 세션: 0개)
```

---

##### `get_all_sessions()`

**목적**: 모든 활성 세션 목록 조회

**반환값**: `List[Dict]` - 각 세션의 상태 정보 리스트

**예제**:

```python
sessions = manager.get_all_sessions()

for session_info in sessions:
    print(f"Device: {session_info['device_id']}, Active: {session_info['is_active']}")
```

**출력 예시**:

```
Device: cores3_01, Active: True
Device: cores3_02, Active: True
```

---

### 2. ASRSession

**위치**: `backend/rk3588asr/asr_api_server.py`

**설명**: 개별 음성인식 세션

#### 클래스 정의

```python
class ASRSession:
    """
    음성인식 세션

    하나의 장비(CoreS3)에 대한 음성인식 세션을 나타냅니다.
    VADStreamingProcessor를 소유하고, WebSocket 연결을 관리하며,
    인식 결과를 저장합니다.

    Attributes:
        session_id (str): 고유 세션 ID (UUID)
        device_id (str): 장비 ID
        language (str): 언어 코드
        sample_rate (int): 샘플레이트
        created_at (datetime): 생성 시각
        processor (VADStreamingProcessor): VAD 프로세서
        websocket (Optional[WebSocket]): WebSocket 연결
        recognition_results (deque): 인식 결과 큐 (최대 100개)
    """
```

#### 메서드

##### `__init__(session_id, device_id, language, sample_rate, vad_enabled)`

**목적**: 세션 초기화

**파라미터**:

- `session_id` (str): 세션 ID
- `device_id` (str): 장비 ID
- `language` (str): 언어 코드
- `sample_rate` (int): 샘플레이트
- `vad_enabled` (bool): VAD 활성화

**동작 순서**:

1. 기본 속성 초기화
2. 전역 recognizer 존재 여부 확인
3. VADStreamingProcessor 생성
4. WebSocket 연결 변수 초기화 (None)
5. 인식 결과 큐 생성 (deque, maxlen=100)

**예외**:

- `RuntimeError`: recognizer가 None인 경우

---

##### `start()`

**목적**: 세션 시작 (VAD Processor 활성화)

**반환값**: None

**동작**:

```python
def start(self):
    """세션 시작"""
    self.processor.start_session()
    logger.info(f"🎤 세션 시작: {self.session_id}")
```

---

##### `stop()`

**목적**: 세션 종료 (VAD Processor 비활성화)

**반환값**: None

**동작**:

```python
def stop(self):
    """세션 종료"""
    self.processor.stop_session()
    logger.info(f"🛑 세션 종료: {self.session_id}")
```

---

##### `process_audio_chunk(audio_data)` (async)

**목적**: 오디오 청크 처리 및 음성인식

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| audio_data | np.ndarray | float32 PCM 오디오 (16kHz) |

**반환값**:

- `Dict`: 인식 결과 (음성 구간 감지 시)
- `None`: 결과 없음 (침묵 또는 처리 중)

**동작 순서**:

1. VAD Processor에 오디오 전달
2. 인식 결과 수신 (text, timestamp, duration)
3. 응급 상황 감지 (matcher.find_best_match)
4. 응급 상황 시 API 알림 전송
5. 결과를 recognition_results 큐에 저장
6. 결과 반환

**결과 구조**:

```python
{
    'text': '안녕하세요',
    'timestamp': '2025-12-08 10:30:45',
    'duration': 2.3,
    'confidence': 1.0,
    'is_emergency': False,
    'emergency_keywords': []
}
```

**예제**:

```python
# 오디오 데이터 (16kHz float32)
audio_chunk = np.random.randn(1024).astype(np.float32)

# 처리
result = await session.process_audio_chunk(audio_chunk)

if result:
    print(f"Recognition: {result['text']}")
    if result['is_emergency']:
        print(f"Emergency detected: {result['emergency_keywords']}")
```

---

##### `get_status()`

**목적**: 세션 상태 조회

**반환값**: `Dict` - 세션 상태 정보

**반환 구조**:

```python
{
    'session_id': 'uuid-xxxx',
    'device_id': 'cores3_01',
    'is_active': True,
    'is_processing': False,
    'segments_count': 5,
    'last_result': '안녕하세요',
    'created_at': '2025-12-08T10:30:00.123456',
    'language': 'ko'
}
```

---

### 3. VADStreamingProcessor

**위치**: `backend/rk3588asr/demo_vad_final.py` (재사용)

**설명**: Voice Activity Detection 기반 실시간 음성인식 프로세서

#### 주요 메서드

##### `process_audio_chunk(audio_data)`

**목적**: 오디오 청크 처리 및 VAD 판단

**알고리즘**:

1. **에너지 계산**:

   ```python
   energy = np.sqrt(np.mean(audio_data ** 2))  # RMS
   ```

2. **음성/침묵 판단**:

   ```python
   is_speech = energy > self.energy_threshold  # 기본: 0.01
   ```

3. **상태 전환**:

   ```
   [침묵] ──음성 감지──> [음성]
      ▲                     │
      └──침묵 1.5초────────┘
   ```

4. **음성 구간 인식**:
   - 버퍼에 최소 0.5초 이상 누적
   - Sherpa-ONNX로 텍스트 변환
   - 결과 반환

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| audio_data | np.ndarray | float32 PCM 오디오 |

**반환값**:

- `Dict`: 인식 결과 (음성 구간 완료 시)
- `None`: 처리 중 또는 침묵

---

## 🌐 WebSocket 핸들러

### `websocket_asr_endpoint(websocket, session_id)` (async)

**위치**: `backend/rk3588asr/asr_api_server.py`

**설명**: WebSocket 음성 스트리밍 엔드포인트

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| websocket | WebSocket | FastAPI WebSocket 객체 |
| session_id | str | 세션 ID (URL 경로 파라미터) |

**동작 순서**:

1. **세션 확인**:

   ```python
   session = session_manager.get_session(session_id)
   if not session:
       await websocket.close(code=4004, reason="세션을 찾을 수 없습니다")
       return
   ```

2. **연결 수락**:

   ```python
   await websocket.accept()
   session.websocket = websocket

   # 환영 메시지 전송
   await websocket.send_json({
       "type": "connected",
       "session_id": session_id,
       "message": "WebSocket 연결 성공. 오디오 전송을 시작하세요."
   })
   ```

3. **메시지 수신 루프**:

   ```python
   while True:
       data = await websocket.receive_text()
       message = json.loads(data)

       if message['type'] == 'audio_chunk':
           # 오디오 처리
           audio_base64 = message['data']
           audio_bytes = base64.b64decode(audio_base64)
           audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
           audio_float32 = audio_int16.astype(np.float32) / 32768.0

           # VAD 처리
           result = await session.process_audio_chunk(audio_float32)

           if result:
               # 인식 결과 전송
               await websocket.send_json({
                   "type": "recognition_result",
                   "session_id": session_id,
                   "text": result['text'],
                   "timestamp": result['timestamp'],
                   "duration": result['duration'],
                   "is_final": True,
                   "is_emergency": result.get('is_emergency', False),
                   "emergency_keywords": result.get('emergency_keywords', [])
               })
   ```

4. **예외 처리**:
   ```python
   except WebSocketDisconnect:
       logger.info(f"🔌 WebSocket 연결 끊김: {session_id}")
   except Exception as e:
       logger.error(f"❌ WebSocket 오류: {e}", exc_info=True)
   finally:
       session.websocket = None
       logger.info(f"🧹 WebSocket 정리 완료: {session_id}")
   ```

**메시지 타입 처리**:

| 타입          | 처리 로직                                 |
| ------------- | ----------------------------------------- |
| `audio_chunk` | Base64 디코딩 → VAD 처리 → 인식 결과 전송 |
| `ping`        | `pong` 응답 전송 (연결 유지)              |
| 기타          | 경고 로그 출력                            |

**에러 처리**:

| 에러 타입             | 처리 방법                             |
| --------------------- | ------------------------------------- |
| `JSONDecodeError`     | 에러 메시지 전송 ("잘못된 JSON 형식") |
| `Exception`           | 에러 메시지 전송 + 로그 기록          |
| `WebSocketDisconnect` | 정상 종료, 로그 기록                  |

---

## 🛠️ API 엔드포인트 함수

### `start_session(request)` (async)

**위치**: `backend/rk3588asr/asr_api_server.py`

**설명**: POST /asr/session/start 핸들러

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| request | SessionStartRequest | Pydantic 모델 |

**동작 순서**:

1. SessionManager로 세션 생성
2. 세션 시작 (VAD 활성화)
3. WebSocket URL 생성
4. SessionStartResponse 반환

**예외 처리**:

```python
try:
    session = session_manager.create_session(...)
    session.start()
    return SessionStartResponse(...)
except Exception as e:
    logger.error(f"❌ 세션 생성 실패: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail=f"세션 생성 실패: {str(e)}"
    )
```

---

### `get_session_status(session_id)` (async)

**위치**: `backend/rk3588asr/asr_api_server.py`

**설명**: GET /asr/session/{session_id}/status 핸들러

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| session_id | str | 경로 파라미터 (UUID) |

**동작 순서**:

1. SessionManager에서 세션 조회
2. 세션이 없으면 404 에러
3. 세션의 get_status() 호출
4. SessionStatusResponse 반환

**예외 처리**:

```python
session = session_manager.get_session(session_id)

if not session:
    raise HTTPException(
        status_code=404,
        detail=f"세션을 찾을 수 없습니다: {session_id}"
    )

return SessionStatusResponse(**session.get_status())
```

---

### `stop_session(session_id)` (async)

**위치**: `backend/rk3588asr/asr_api_server.py`

**설명**: POST /asr/session/{session_id}/stop 핸들러

**파라미터**:
| 이름 | 타입 | 설명 |
|------|------|------|
| session_id | str | 경로 파라미터 (UUID) |

**동작 순서**:

1. 세션 조회
2. 세션이 없으면 404 에러
3. 인식 결과 개수 저장
4. SessionManager에서 세션 제거 (자동으로 stop() 호출)
5. SessionStopResponse 반환

---

## 🔧 유틸리티 함수

### Base64 인코딩/디코딩

**CoreS3 (C++)**:

```cpp
// int16 → Base64
String base64Audio = base64::encode((uint8_t*)audioBuffer, bytesRead);
```

**ASR 서버 (Python)**:

```python
# Base64 → numpy array
audio_bytes = base64.b64decode(audio_base64)
audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
audio_float32 = audio_int16.astype(np.float32) / 32768.0
```

---

### 오디오 형식 변환

**int16 → float32**:

```python
# 정규화: [-32768, 32767] → [-1.0, 1.0]
audio_float32 = audio_int16.astype(np.float32) / 32768.0
```

**float32 → int16**:

```python
# 역정규화: [-1.0, 1.0] → [-32768, 32767]
audio_int16 = (audio_float32 * 32768).astype(np.int16)
```

---

## 📊 데이터 흐름 요약

```
┌─────────────┐
│ CoreS3      │
│ I2S Mic     │
│ int16 PCM   │
└──────┬──────┘
       │ Base64 encode
       ▼
┌─────────────┐
│ WebSocket   │
│ JSON msg    │
└──────┬──────┘
       │ Base64 decode
       ▼
┌─────────────┐
│ ASR Server  │
│ numpy array │
│ float32     │
└──────┬──────┘
       │ VAD process
       ▼
┌─────────────┐
│ Sherpa-ONNX │
│ Recognizer  │
└──────┬──────┘
       │ text result
       ▼
┌─────────────┐
│ WebSocket   │
│ JSON result │
└──────┬──────┘
       │
       ├──> CoreS3 (Display)
       │
       └──> Frontend (Chat Window)
```

---

## 🧪 테스트 함수

### test_audio_processing()

**목적**: 오디오 처리 파이프라인 테스트

```python
def test_audio_processing():
    """오디오 처리 테스트"""
    # 1. 더미 오디오 생성 (1초, 16kHz)
    audio_int16 = np.random.randint(-32768, 32767, 16000, dtype=np.int16)

    # 2. Base64 인코딩
    audio_bytes = audio_int16.tobytes()
    audio_base64 = base64.b64encode(audio_bytes).decode()

    # 3. Base64 디코딩
    decoded_bytes = base64.b64decode(audio_base64)
    decoded_int16 = np.frombuffer(decoded_bytes, dtype=np.int16)

    # 4. float32 변환
    audio_float32 = decoded_int16.astype(np.float32) / 32768.0

    # 5. 검증
    assert len(audio_float32) == 16000
    assert audio_float32.dtype == np.float32
    assert -1.0 <= audio_float32.min() <= audio_float32.max() <= 1.0

    print("✅ Audio processing test passed")
```

---

## 📝 로깅 규칙

### 로그 레벨

| 레벨    | 용도             | 예시                        |
| ------- | ---------------- | --------------------------- |
| DEBUG   | 상세 디버그 정보 | `오디오 수신: 1024 samples` |
| INFO    | 일반 정보        | `✅ 세션 생성 완료`         |
| WARNING | 경고             | `⚠️ 알 수 없는 메시지 타입` |
| ERROR   | 오류             | `❌ JSON 파싱 실패`         |

### 로그 포맷

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

**출력 예시**:

```
2025-12-08 10:30:45 - asr_api_server - INFO - [start_session:123] - ✅ ASR 세션 생성: 550e8400-...
```

---

**문서 버전**: 1.0.0  
**최종 수정**: 2025-12-08
