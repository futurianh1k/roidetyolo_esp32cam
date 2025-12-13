# ESP32 펌웨어 가이드

## 개요

이 문서는 Core S3 (M5Stack Core S3) 장비의 펌웨어 구조와 기능을 설명합니다.

## 아키텍처

```
firmware_idf/
├── main/
│   ├── application.cc       # 메인 애플리케이션 (이벤트 루프)
│   ├── config.h              # 설정 값 (WiFi, MQTT, 서버 등)
│   ├── device_state.h        # 장비 상태 정의
│   ├── device_state_machine.cc # 상태 머신
│   │
│   ├── network/
│   │   ├── wifi_manager.cc   # WiFi 연결 관리
│   │   ├── mqtt_client_wrapper.cc # MQTT 클라이언트
│   │   ├── websocket_client.cc    # WebSocket 클라이언트
│   │   └── backend_client.cc      # HTTP 클라이언트 (백엔드 통신)
│   │
│   ├── status/
│   │   └── status_reporter.cc # 상태 보고 서비스
│   │
│   ├── audio/
│   │   ├── audio_codec.cc    # 오디오 코덱 (ES8311)
│   │   └── audio_service.cc  # 오디오 서비스
│   │
│   ├── camera/
│   │   └── camera_service.cc # 카메라 서비스 (GC0308)
│   │
│   ├── asr/
│   │   └── asr_service.cc    # 음성 인식 서비스
│   │
│   ├── display/
│   │   └── display_service.cc # 디스플레이 서비스
│   │
│   └── power/
│       └── power_manager.cc  # 전원 관리 (AXP2101)
```

## 주요 기능

### 1. 백엔드 상태 전송 (`StatusReporter`)

펌웨어는 10초마다 백엔드 서버에 장비 상태를 HTTP POST로 전송합니다.

**API Endpoint**: `POST /devices/{device_id}/status`

**전송 데이터**:

```json
{
  "battery_level": -1, // 배터리 잔량 (-1: 미지원)
  "memory_usage": 200000, // 남은 힙 메모리 (bytes)
  "storage_usage": -1, // 스토리지 사용량 (-1: 미지원)
  "temperature": 0.0, // CPU 온도
  "cpu_usage": 0, // CPU 사용률
  "camera_status": "active", // active, paused, stopped
  "mic_status": "stopped" // active, paused, stopped
}
```

### 2. MQTT 명령 수신

펌웨어는 MQTT를 통해 원격 명령을 수신합니다.

#### 구독 토픽

| 토픽                                     | 설명            |
| ---------------------------------------- | --------------- |
| `devices/{device_id}/control/camera`     | 카메라 제어     |
| `devices/{device_id}/control/microphone` | 마이크 제어     |
| `devices/{device_id}/control/speaker`    | 스피커 제어     |
| `devices/{device_id}/control/display`    | 디스플레이 제어 |
| `devices/{device_id}/control/system`     | 시스템 제어     |
| `devices/{device_id}/command`            | 통합 명령       |

#### 명령 형식

**카메라 제어**:

```json
{
  "action": "start" | "stop" | "pause"
}
```

**마이크 제어 (ASR 시작)**:

```json
{
  "action": "start_asr",
  "language": "ko",
  "ws_url": "ws://..." // 옵션
}
```

**마이크 제어 (ASR 중지)**:

```json
{
  "action": "stop_asr"
}
```

**디스플레이 제어**:

```json
{
  "action": "show_text",
  "text": "표시할 텍스트"
}
```

```json
{
  "action": "clear"
}
```

**시스템 제어**:

```json
{
  "action": "restart"
}
```

### 3. 음성 인식 (ASR)

- WebSocket을 통해 음성 인식 서버와 연결
- 실시간 음성 스트리밍 및 결과 수신
- 긴급 키워드 감지 지원

## 설정 (`config.h`)

```c
// WiFi 설정
#define WIFI_SSID "your_ssid"
#define WIFI_PASSWORD "your_password"

// MQTT 설정
#define MQTT_BROKER "10.10.11.18"
#define MQTT_PORT 1883

// 장비 설정
#define DEVICE_ID "core_s3_001"
#define DEVICE_DB_ID 1  // 백엔드 DB ID

// 백엔드 서버
#define BACKEND_HOST "10.10.11.18"
#define BACKEND_PORT 8000

// 상태 보고 주기
#define STATUS_REPORT_INTERVAL_MS 10000
```

## 빌드

### 사전 요구사항

- ESP-IDF v5.x
- Python 3.8+

### 빌드 명령

```powershell
# PowerShell
.\build.ps1 -Target build

# 또는
idf.py build
```

### 플래시

```powershell
.\build.ps1 -Target flash -Port COM3
```

## 상태 머신

```
┌─────────────┐
│   Starting  │ ──> 초기화 중
└─────────────┘
       │
       ▼
┌─────────────┐
│   Idle      │ ──> 대기 상태
└─────────────┘
       │ WiFi 연결
       ▼
┌─────────────┐
│ Connecting  │ ──> 네트워크 연결 중
└─────────────┘
       │ 연결 성공
       ▼
┌─────────────┐
│  Connected  │ ──> 네트워크 연결됨
└─────────────┘
       │ ASR 시작
       ▼
┌─────────────┐
│  Listening  │ ──> 음성 인식 중
└─────────────┘
       │ 처리 중
       ▼
┌─────────────┐
│ Processing  │ ──> 결과 처리 중
└─────────────┘
```

## 참고자료

- ESP-IDF HTTP Client: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html
- ESP-IDF MQTT: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/mqtt.html
- xiaozhi-esp32: https://github.com/78/xiaozhi-esp32
