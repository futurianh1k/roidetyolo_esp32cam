# Phase 2 완료 보고서 - 프론트엔드 구현

**완료일**: 2025-12-08  
**소요 시간**: 약 1시간  
**상태**: ✅ 완료

---

## 📋 작업 요약

Phase 2에서는 프론트엔드에 영상 sink 설정 UI를 추가했습니다. 사용자가 장비 상세 페이지에서 영상 sink 주소를 입력하고, 전송 방식을 선택하며, 카메라 제어 시 sink 정보를 포함하여 전송할 수 있습니다.

---

## 📦 수정된 파일 (2개)

### 1. frontend/src/lib/api.ts

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

**주요 변경사항**:

- `camera()` 함수 시그니처 확장
- 선택적 파라미터: `sinkUrl`, `streamMode`, `frameInterval`
- API 요청 시 snake_case로 변환 (`sink_url`, `stream_mode`, `frame_interval`)

---

### 2. frontend/src/components/DeviceControl.tsx

**추가된 상태**:

```typescript
const [sinkUrl, setSinkUrl] = useState<string>("");
const [streamMode, setStreamMode] = useState<
  "mjpeg_stills" | "realtime_websocket" | "realtime_rtsp" | ""
>("");
const [frameInterval, setFrameInterval] = useState<number>(1000);
```

**추가된 UI 섹션**:

#### 영상 Sink 설정 박스

- 회색 배경 (`bg-gray-50`)
- 테두리 (`border border-gray-200`)
- 제목: "영상 Sink 설정 (선택사항)"

#### 1. Sink URL 입력 필드

- 텍스트 입력
- 플레이스홀더: 예시 URL 제공
- 도움말: "HTTP/WebSocket/RTSP URL 형식 지원"

#### 2. 전송 방식 선택 (라디오 버튼)

- **MJPEG 스틸컷**: 주기적 JPEG 전송
- **실시간 스트림 (WebSocket)**: WebSocket 스트림
- **실시간 스트림 (RTSP)**: RTSP 스트림
- `sinkUrl`이 있을 때만 표시

#### 3. 프레임 간격 설정 (슬라이더)

- `streamMode === 'mjpeg_stills'`일 경우만 표시
- 범위: 100ms ~ 10000ms
- 실시간 값 표시: "프레임 간격: {frameInterval}ms"
- 최소/최대 값 표시

#### 4. 설정 초기화 버튼

- 모든 sink 설정 초기화
- 작은 텍스트, 밑줄 스타일

**수정된 함수**:

#### `handleCameraControl()`

```typescript
const handleCameraControl = async (action: "start" | "pause" | "stop") => {
  // 검증
  if (action === "start") {
    if (sinkUrl && !streamMode) {
      toast.error("전송 방식을 선택하세요");
      return;
    }
    if (
      streamMode === "mjpeg_stills" &&
      (!frameInterval || frameInterval < 100 || frameInterval > 10000)
    ) {
      toast.error("프레임 간격은 100ms ~ 10000ms 사이여야 합니다");
      return;
    }
  }

  // API 호출
  await controlAPI.camera(
    device.id,
    action,
    sinkUrl || undefined,
    streamMode || undefined,
    streamMode === "mjpeg_stills" ? frameInterval : undefined
  );
};
```

---

## 🎨 UI/UX 특징

### 조건부 표시

- **전송 방식 선택**: `sinkUrl`이 있을 때만 표시
- **프레임 간격 슬라이더**: `streamMode === 'mjpeg_stills'`일 때만 표시

### 사용자 피드백

- 실시간 검증 및 에러 메시지
- Toast 알림으로 성공/실패 알림
- 명확한 라벨 및 도움말

### 접근성

- 오프라인 상태 시 모든 입력 비활성화
- 명확한 라벨 및 설명
- 키보드 네비게이션 지원

---

## 🔄 전체 데이터 플로우

### 카메라 시작 (sink 설정 포함)

```
[사용자] 장비 상세 페이지
    │
    ├─ Sink URL 입력
    │     "http://192.168.1.100:8080/video"
    │
    ├─ 전송 방식 선택
    │     "MJPEG 스틸컷"
    │
    ├─ 프레임 간격 설정
    │     1000ms
    │
    └─ "시작" 버튼 클릭
          │
          ▼
    [프론트엔드] handleCameraControl("start")
          │
          ├─ 검증
          │     - sinkUrl 있으면 streamMode 필수
          │     - mjpeg_stills면 frameInterval 필수
          │
          └─ API 호출
                controlAPI.camera(
                  deviceId,
                  "start",
                  "http://192.168.1.100:8080/video",
                  "mjpeg_stills",
                  1000
                )
                │
                ▼
    [백엔드] POST /control/devices/{id}/camera
          {
            action: "start",
            sink_url: "http://192.168.1.100:8080/video",
            stream_mode: "mjpeg_stills",
            frame_interval: 1000
          }
          │
          ├─ 검증
          │     - sink_url 있으면 stream_mode 필수
          │     - mjpeg_stills면 frame_interval 필수
          │
          └─ MQTT 전송
                TOPIC: devices/cores3_01/control/camera
                PAYLOAD: {
                  command: "camera",
                  action: "start",
                  sink_url: "...",
                  stream_mode: "mjpeg_stills",
                  frame_interval: 1000
                }
                │
                ▼
    [CoreS3] MQTT 수신
          │
          ├─ cameraSetSink(sinkUrl, streamMode, frameInterval)
          ├─ cameraStart()
          └─ cameraLoop()에서 주기적으로 프레임 전송
```

---

## ✅ 달성한 목표

### 프론트엔드 통합

- ✅ 영상 sink 설정 UI 추가
- ✅ 전송 방식 선택 기능
- ✅ 프레임 간격 설정 기능
- ✅ API 클라이언트 확장

### 사용자 경험

- ✅ 직관적인 UI/UX
- ✅ 실시간 검증 및 피드백
- ✅ 조건부 UI 표시
- ✅ 명확한 라벨 및 도움말

---

## 📝 변경 사항 요약

| 구분 | 파일 수 | 라인 수 |
| ---- | ------- | ------- |
| 수정 | 2       | ~150    |
| 합계 | 2       | 150     |

---

## 🎉 Phase 2 완료!

프론트엔드에 영상 sink 설정 기능이 완전히 통합되었습니다.

**완료된 기능**:

- ✅ Sink URL 입력
- ✅ 전송 방식 선택
- ✅ 프레임 간격 설정
- ✅ 카메라 제어 시 sink 정보 전송

**전체 시스템 준비 완료**:

- ✅ Phase 1: 백엔드
- ✅ Phase 2: 프론트엔드
- ✅ Phase 3: 펌웨어 (MJPEG 스틸컷 완료)

**카메라 영상 sink 전송 기능 통합 완료!** 🎊

---

**작성일**: 2025-12-08  
**상태**: ✅ 완료  
**다음**: WebSocket/RTSP 스트림 구현 (선택적)
