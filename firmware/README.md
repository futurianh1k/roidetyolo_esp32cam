# Core S3 Management System - Firmware

M5Stack Core S3용 IoT 장비 관리 펌웨어입니다.

## 기능

### ✅ 통신
- WiFi 연결 및 자동 재연결
- MQTT 양방향 통신 (백엔드와 연동)
- 실시간 상태 보고

### ✅ 카메라
- OV2640 카메라 제어
- RTSP 스트리밍 (TODO)
- 시작/일시정지/정지 제어

### ✅ 오디오
- **마이크**: I2S 마이크 제어 (ES7210)
- **스피커**: HTTP 오디오 스트리밍 재생 (AW88298)
- 16kHz 샘플링

### ✅ 디스플레이
- LCD 텍스트 표시
- 이모티콘 표시
- 시스템 정보 표시
- 상태 메시지 표시

### ✅ 제어
- MQTT를 통한 원격 제어
- 버튼을 통한 수동 제어
- 실시간 응답 전송

### ✅ 상태 모니터링
- 배터리 레벨
- 메모리 사용량
- CPU 온도
- WiFi 신호 강도
- 카메라/마이크 상태

## 하드웨어 사양

- **MCU**: ESP32-S3 (Dual-Core, 240MHz)
- **메모리**: 8MB PSRAM, 16MB Flash
- **카메라**: OV2640 (2MP)
- **마이크**: ES7210 (I2S)
- **스피커**: AW88298 (I2S)
- **디스플레이**: ILI9342C (320x240 LCD)
- **WiFi**: 2.4GHz 802.11 b/g/n
- **Bluetooth**: BLE 5.0

## 개발 환경 설정

### 1. PlatformIO 설치

**VS Code 사용:**
1. VS Code 설치
2. PlatformIO IDE 확장 프로그램 설치
3. PlatformIO 아이콘 클릭 → Open Project

**명령줄 사용:**
```bash
pip install platformio
```

### 2. 프로젝트 클론 및 열기

```bash
cd firmware
```

VS Code에서:
- File → Open Folder → `firmware` 폴더 선택

### 3. 설정 파일 수정

`include/config.h` 파일을 열고 다음 내용을 수정:

```cpp
// WiFi 설정
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// MQTT 설정
#define MQTT_BROKER "192.168.1.100"  // 백엔드 서버 IP

// 장비 설정
#define DEVICE_ID "core_s3_001"  // 고유 장비 ID
#define DEVICE_NAME "Core S3 Camera"
#define DEVICE_LOCATION "Office"
```

### 4. 빌드 및 업로드

**VS Code (PlatformIO):**
- 하단 상태바에서 `Build` (✓) 클릭
- `Upload` (→) 클릭

**명령줄:**
```bash
# 빌드
platformio run

# 업로드
platformio run --target upload

# 시리얼 모니터
platformio device monitor
```

### 5. 시리얼 모니터 확인

```
=================================
Core S3 Management System
=================================
Device ID: core_s3_001
Device Name: Core S3 Camera
Connecting to WiFi...
WiFi connected!
IP Address: 192.168.1.150
Initializing camera...
Camera initialized successfully
Initializing audio...
Audio initialized successfully
Connecting to MQTT broker...
MQTT connected!
=================================
System initialized successfully!
=================================
```

## 프로젝트 구조

```
firmware/
├── platformio.ini         # PlatformIO 설정
├── include/
│   ├── config.h          # 설정 파일
│   ├── pins.h            # 핀 정의
│   ├── camera_module.h   # 카메라 헤더
│   ├── audio_module.h    # 오디오 헤더
│   ├── display_module.h  # 디스플레이 헤더
│   ├── mqtt_module.h     # MQTT 헤더
│   └── status_module.h   # 상태 헤더
├── src/
│   ├── main.cpp          # 메인 프로그램
│   ├── camera_module.cpp # 카메라 제어
│   ├── audio_module.cpp  # 오디오 제어
│   ├── display_module.cpp # 디스플레이 제어
│   ├── mqtt_module.cpp   # MQTT 통신
│   └── status_module.cpp # 상태 보고
└── README.md
```

## MQTT 통신 프로토콜

### 구독 토픽 (장비가 수신)

```
devices/{device_id}/control/camera      # 카메라 제어
devices/{device_id}/control/microphone  # 마이크 제어
devices/{device_id}/control/speaker     # 스피커 제어
devices/{device_id}/control/display     # 디스플레이 제어
```

### 발행 토픽 (장비가 전송)

```
devices/{device_id}/status              # 상태 보고
devices/{device_id}/response            # 명령 응답
```

### 메시지 형식

**제어 명령 (서버 → 장비):**
```json
{
  "command": "camera",
  "action": "start",
  "timestamp": 1234567890,
  "request_id": "abc123"
}
```

**상태 보고 (장비 → 서버):**
```json
{
  "device_id": "core_s3_001",
  "battery_level": 85,
  "memory_usage": 45000,
  "temperature": 38.5,
  "camera_status": "active",
  "mic_status": "stopped",
  "wifi_rssi": -45,
  "timestamp": 1234567890
}
```

**제어 응답 (장비 → 서버):**
```json
{
  "request_id": "abc123",
  "command": "camera",
  "action": "start",
  "success": true,
  "message": "Camera started",
  "timestamp": 1234567890
}
```

## 버튼 기능

- **버튼 A (왼쪽)**: 카메라 ON/OFF
- **버튼 B (중앙)**: 마이크 ON/OFF
- **버튼 C (오른쪽)**: 시스템 정보 표시

## LED 상태

- **초록색**: 정상 작동
- **노란색**: 일시정지
- **빨간색**: 오류
- **파란색**: WiFi 연결 중
- **보라색**: MQTT 연결 중

## 디버그

### 시리얼 모니터

```bash
platformio device monitor --baud 115200
```

### 디버그 메시지 활성화

`config.h`:
```cpp
#define DEBUG_ENABLED 1
```

### 디버그 레벨 설정

`platformio.ini`:
```ini
build_flags = 
    -DCORE_DEBUG_LEVEL=4  ; 0=None, 1=Error, 2=Warn, 3=Info, 4=Debug
```

## 문제 해결

### WiFi 연결 실패
```
- SSID와 비밀번호 확인
- 2.4GHz WiFi 사용 확인 (5GHz 미지원)
- 라우터와의 거리 확인
```

### MQTT 연결 실패
```
- 브로커 IP 주소 확인
- 방화벽 설정 확인 (포트 1883)
- 브로커가 실행 중인지 확인
```

### 카메라 초기화 실패
```
- 카메라 케이블 연결 확인
- PSRAM 활성화 확인
- 펌웨어 재업로드
```

### 오디오 문제
```
- I2S 핀 연결 확인
- 샘플링 레이트 확인 (16kHz)
- 볼륨 확인
```

## 고급 설정

### 카메라 해상도 변경

`config.h`:
```cpp
#define CAMERA_FRAMESIZE FRAMESIZE_QVGA  // 320x240
// FRAMESIZE_VGA    // 640x480
// FRAMESIZE_SVGA   // 800x600
// FRAMESIZE_XGA    // 1024x768
// FRAMESIZE_HD     // 1280x720
// FRAMESIZE_UXGA   // 1600x1200
```

### 카메라 품질 조정

```cpp
#define CAMERA_QUALITY 10  // 0-63 (낮을수록 고품질)
```

### 상태 보고 간격 변경

```cpp
#define STATUS_REPORT_INTERVAL 10000  // 밀리초 (10초)
```

### MQTT QoS 변경

```cpp
#define MQTT_QOS 1  // 0, 1, 2
```

## 성능 최적화

### 메모리 사용 최적화
- PSRAM 활성화 (기본 설정됨)
- 프레임 버퍼 개수 조정 (`fb_count`)
- JSON 문서 크기 조정

### 전력 절약
- 슬립 모드 활성화 (TODO)
- LCD 밝기 조정
- WiFi 절전 모드 활성화

### 네트워크 최적화
- MQTT Keep-Alive 간격 조정
- WiFi 전송 파워 조정
- QoS 레벨 조정

## OTA 업데이트 (TODO)

무선 펌웨어 업데이트 기능:

```cpp
// TODO: OTA 업데이트 구현
// - ArduinoOTA 사용
// - HTTP OTA 사용
```

## 보안 고려사항

1. **WiFi 비밀번호**: 하드코딩하지 말고 별도 설정 파일 사용
2. **MQTT 인증**: USERNAME/PASSWORD 사용
3. **TLS/SSL**: MQTT over TLS 사용 (TODO)
4. **펌웨어 암호화**: Flash 암호화 활성화 (TODO)

## 참고 자료

- [M5Stack Core S3 문서](https://docs.m5stack.com/en/core/CoreS3)
- [ESP32-Camera 라이브러리](https://github.com/espressif/esp32-camera)
- [PubSubClient (MQTT)](https://github.com/knolleary/pubsubclient)
- [ArduinoJson](https://arduinojson.org/)
- [PlatformIO](https://platformio.org/)

## 라이선스

MIT License

## 지원

문제가 발생하면:
1. 시리얼 모니터 로그 확인
2. 설정 파일 확인
3. 하드웨어 연결 확인
4. 펌웨어 재업로드

