# 카메라 영상 Sink 전송 기능 설계

**작성일**: 2025-12-08  
**상태**: 설계 완료

---

## 📋 요구사항

### 기능 요구사항

1. **장비 상세 페이지에서 영상 sink 주소 입력**

   - URL 입력 필드
   - 전송 방식 선택 (MJPEG 스틸컷 / 실시간 스트림)
   - 스틸컷 주기 설정 (방식1일 경우)

2. **카메라 구동 시 영상 전송**

   - **방식1 (MJPEG 스틸컷)**: 설정한 주기에 맞춰서 JPEG 이미지 전송
   - **방식2 (실시간 스트림)**: WebSocket 또는 RTSP로 실시간 스트림 전송

3. **카메라 제어 연동**
   - 카메라 시작 → 영상 전송 시작
   - 카메라 일시정지 → 영상 전송 일시정지
   - 카메라 정지 → 영상 전송 정지

---

## 🏗️ 아키텍처 설계

### 전체 데이터 플로우

```
[프론트엔드] 장비 상세 페이지
    │
    ├─ 영상 sink 주소 입력
    │     - URL: http://192.168.1.100:8080/video
    │     - 방식: MJPEG 스틸컷 / 실시간 스트림
    │     - 주기: 1초 (스틸컷일 경우)
    │
    └─ 카메라 시작 버튼 클릭
          │
          ▼
    [백엔드] POST /control/devices/{id}/camera
          {
            action: "start",
            sink_url: "http://192.168.1.100:8080/video",
            stream_mode: "mjpeg_stills" | "realtime_websocket" | "realtime_rtsp",
            frame_interval: 1000  // ms (스틸컷일 경우)
          }
          │
          ├─ MQTT 명령 전송
          │     TOPIC: devices/cores3_01/control/camera
          │     PAYLOAD: {
          │       command: "camera",
          │       action: "start",
          │       sink_url: "...",
          │       stream_mode: "...",
          │       frame_interval: 1000
          │     }
          │
          └─ 응답 반환
                │
                ▼
    [CoreS3] MQTT 수신
          │
          ├─ 카메라 시작
          │     cameraStart()
          │
          └─ 영상 전송 시작
                │
                ├─ 방식1: MJPEG 스틸컷
                │     - 주기적으로 JPEG 이미지 캡처
                │     - HTTP POST로 sink_url에 전송
                │     - Content-Type: image/jpeg
                │
                └─ 방식2: 실시간 스트림
                      │
                      ├─ WebSocket 모드
                      │     - WebSocket 연결
                      │     - MJPEG 스트림 전송
                      │
                      └─ RTSP 모드
                            - RTSP 서버 시작
                            - sink_url로 스트림 전송
```

---

## 📦 구현 계획

### Phase 1: 백엔드 스키마 및 API 수정

#### 1.1 `backend/app/schemas/control.py`

**변경 내용**:

```python
class CameraControlRequest(BaseModel):
    """카메라 제어 요청"""
    action: Literal["start", "pause", "stop"]
    sink_url: Optional[str] = Field(None, description="영상 sink 주소 (URL)")
    stream_mode: Optional[Literal["mjpeg_stills", "realtime_websocket", "realtime_rtsp"]] = Field(
        None,
        description="전송 방식"
    )
    frame_interval: Optional[int] = Field(
        None,
        ge=100,
        le=10000,
        description="프레임 간격 (ms, 스틸컷일 경우)"
    )
```

#### 1.2 `backend/app/api/control.py`

**변경 내용**:

- `control_camera()` 함수에서 `sink_url`, `stream_mode`, `frame_interval` 파라미터를 MQTT 메시지에 포함

---

### Phase 2: 프론트엔드 UI 추가

#### 2.1 `frontend/src/components/DeviceControl.tsx`

**추가할 UI 요소**:

1. **영상 Sink 설정 섹션** (카메라 제어 위에 배치)

   - Sink URL 입력 필드
   - 전송 방식 선택 (라디오 버튼)
     - MJPEG 스틸컷
     - 실시간 스트림 (WebSocket)
     - 실시간 스트림 (RTSP)
   - 프레임 간격 입력 (스틸컷일 경우만 표시)

2. **카메라 제어 버튼**
   - 기존 버튼 유지
   - `handleCameraControl()` 함수에서 sink 설정 포함

#### 2.2 `frontend/src/lib/api.ts`

**변경 내용**:

```typescript
export const controlAPI = {
  camera: (
    deviceId: number,
    action: "start" | "pause" | "stop",
    sinkUrl?: string,
    streamMode?: "mjpeg_stills" | "realtime_websocket" | "realtime_rtsp",
    frameInterval?: number
  ) =>
    api.post(`/control/devices/${deviceId}/camera`, {
      action,
      sink_url: sinkUrl,
      stream_mode: streamMode,
      frame_interval: frameInterval,
    }),
  // ...
};
```

---

### Phase 3: 펌웨어 구현

#### 3.1 `firmware/include/camera_module.h`

**추가할 함수**:

```cpp
// 영상 sink 설정
void cameraSetSink(const char* sinkUrl, const char* streamMode, int frameInterval);
void cameraClearSink();

// 영상 전송 상태
bool isCameraSinkActive();
```

#### 3.2 `firmware/src/camera_module.cpp`

**구현 내용**:

1. **Sink 설정 변수 추가**:

```cpp
static String sinkUrl = "";
static String streamMode = "";
static int frameInterval = 1000;  // ms
static bool sinkActive = false;
static unsigned long lastFrameTime = 0;
static HTTPClient httpClient;  // HTTP 전송용
static WiFiClient wsClient;    // WebSocket 전송용
```

2. **`cameraSetSink()` 구현**:

   - sink URL, 전송 방식, 주기 저장
   - 전송 방식에 따라 초기화

3. **`cameraLoop()` 수정**:

   - 카메라 활성화 시 프레임 캡처
   - 전송 방식에 따라 분기:
     - **MJPEG 스틸컷**: 주기적으로 HTTP POST로 JPEG 전송
     - **WebSocket**: WebSocket으로 MJPEG 스트림 전송
     - **RTSP**: RTSP 서버로 스트림 전송

4. **HTTP 전송 함수** (MJPEG 스틸컷):

```cpp
void sendMjpegStill(camera_fb_t* fb) {
    if (sinkUrl.length() == 0) return;

    httpClient.begin(sinkUrl);
    httpClient.addHeader("Content-Type", "image/jpeg");
    httpClient.POST(fb->buf, fb->len);
    httpClient.end();
}
```

5. **WebSocket 전송 함수** (실시간 스트림):

```cpp
void sendWebSocketStream(camera_fb_t* fb) {
    // WebSocket 연결 확인
    // MJPEG 프레임 전송
    // --binary-frame--
    // [JPEG 데이터]
}
```

6. **RTSP 서버** (실시간 스트림):
   - Micro-RTSP 라이브러리 활용
   - sink URL로 스트림 전송

#### 3.3 `firmware/src/mqtt_module.cpp`

**변경 내용**:

- `handleCameraControl()` 함수에서 `sink_url`, `stream_mode`, `frame_interval` 파라미터 파싱
- `cameraSetSink()` 호출

---

## 🔄 동작 시나리오

### 시나리오 1: MJPEG 스틸컷 전송

1. 사용자가 장비 상세 페이지에서:

   - Sink URL: `http://192.168.1.100:8080/video`
   - 전송 방식: MJPEG 스틸컷
   - 프레임 간격: 1초 (1000ms)
   - 카메라 시작 버튼 클릭

2. 백엔드에서 MQTT 명령 전송:

```json
{
  "command": "camera",
  "action": "start",
  "sink_url": "http://192.168.1.100:8080/video",
  "stream_mode": "mjpeg_stills",
  "frame_interval": 1000
}
```

3. CoreS3에서:

   - 카메라 시작
   - Sink 설정 저장
   - 1초마다 JPEG 이미지 캡처
   - HTTP POST로 sink URL에 전송

4. 카메라 일시정지:

   - 프레임 캡처 중단
   - 전송 중단

5. 카메라 정지:
   - 카메라 정지
   - Sink 설정 초기화

---

### 시나리오 2: 실시간 WebSocket 스트림

1. 사용자가 장비 상세 페이지에서:

   - Sink URL: `ws://192.168.1.100:8080/video`
   - 전송 방식: 실시간 스트림 (WebSocket)
   - 카메라 시작 버튼 클릭

2. CoreS3에서:
   - 카메라 시작
   - WebSocket 연결
   - 실시간으로 MJPEG 프레임 전송 (~30 FPS)

---

### 시나리오 3: 실시간 RTSP 스트림

1. 사용자가 장비 상세 페이지에서:

   - Sink URL: `rtsp://192.168.1.100:8554/stream`
   - 전송 방식: 실시간 스트림 (RTSP)
   - 카메라 시작 버튼 클릭

2. CoreS3에서:
   - 카메라 시작
   - RTSP 서버 시작
   - sink URL로 스트림 전송

---

## 📊 기술 스택

### 프론트엔드

- React (Next.js)
- React Query
- Tailwind CSS

### 백엔드

- FastAPI
- Pydantic (스키마 검증)
- MQTT (명령 전송)

### 펌웨어

- ESP32-Camera (카메라 제어)
- HTTPClient (HTTP POST)
- ArduinoWebsockets (WebSocket 전송)
- Micro-RTSP (RTSP 서버)

---

## ⚠️ 주의사항

### 1. 네트워크 대역폭

**MJPEG 스틸컷**:

- 1초마다 전송: 약 50-100 KB/s
- 0.5초마다 전송: 약 100-200 KB/s

**실시간 스트림**:

- 30 FPS: 약 1-2 MB/s
- WiFi 대역폭 고려 필요

### 2. 메모리 관리

- JPEG 버퍼 크기: ~10-50 KB
- PSRAM 사용 필수
- 버퍼 누수 방지

### 3. 에러 처리

- HTTP 전송 실패 시 재시도 로직
- WebSocket 연결 끊김 시 재연결
- RTSP 서버 오류 처리

### 4. 보안

- Sink URL 검증 (HTTP/HTTPS/WS/WSS/RTSP만 허용)
- 인증 토큰 지원 (향후)
- Rate limiting (DoS 방지)

---

## 🚀 구현 순서

1. **Phase 1: 백엔드** (1시간)

   - 스키마 수정
   - API 수정
   - MQTT 메시지 확장

2. **Phase 2: 프론트엔드** (2시간)

   - UI 컴포넌트 추가
   - API 클라이언트 수정
   - 상태 관리

3. **Phase 3: 펌웨어** (3-4시간)
   - MJPEG 스틸컷 구현
   - WebSocket 스트림 구현
   - RTSP 스트림 구현 (선택적)

---

## 📝 다음 단계

1. 설계 검토 및 승인
2. Phase 1부터 순차적으로 구현
3. 각 Phase별 테스트
4. 통합 테스트

---

**작성일**: 2025-12-08  
**상태**: ✅ 설계 완료  
**다음**: Phase 1 구현 시작
