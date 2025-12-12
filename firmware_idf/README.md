# Core S3 Management System - ESP-IDF Version

ESP-IDF 기반 펌웨어 (FreeRTOS 멀티태스크 구조, **OTA 지원**)

## 하드웨어 사양 (M5Stack CoreS3)

- **MCU**: ESP32-S3 (240MHz, Dual Core)
- **Flash**: 16MB
- **PSRAM**: 8MB (Quad mode) ⚠️
- **Display**: ILI9341 (320x240)
- **Camera**: OV2640 (2MP)
- **Audio**: ES7210 (ADC) + AW88298 (Speaker)

## 프로젝트 구조

```
firmware_idf/
├── CMakeLists.txt              # 프로젝트 루트 CMakeLists
├── sdkconfig.defaults          # ESP-IDF 공통 설정
├── sdkconfig.ota               # OTA 버전 설정
├── sdkconfig.singleapp         # Single App 버전 설정
├── partitions_custom.csv       # OTA 파티션 테이블 (2×4MB)
├── partitions_singleapp.csv    # Single App 파티션 테이블 (6MB)
├── BUILD_TYPES.md              # 빌드 타입 가이드 📖
├── OTA_GUIDE.md                # OTA 업데이트 가이드 📖
├── main/
│   ├── CMakeLists.txt          # Main 컴포넌트 CMakeLists
│   ├── idf_component.yml       # 컴포넌트 의존성
│   ├── main.cc                 # 진입점 (app_main)
│   ├── application.h/cc        # Application 싱글톤
│   ├── device_state.h          # 상태 정의
│   ├── device_state_machine.h/cc  # 상태 머신
│   ├── audio/                  # 오디오 모듈
│   ├── camera/                 # 카메라 모듈
│   ├── network/                # 네트워크 모듈
│   ├── display/                # 디스플레이 모듈
│   └── asr/                    # 음성인식 모듈
└── build/                      # 빌드 출력
    └── cores3-management.bin   # OTA 펌웨어 파일
```

## 파티션 레이아웃 (16MB)

### OTA 버전 (기본값)

| Partition | Type        | Offset   | Size    | 설명        |
| --------- | ----------- | -------- | ------- | ----------- |
| nvs       | data/nvs    | 0x9000   | 16KB    | 설정 저장   |
| otadata   | data/ota    | 0xD000   | 8KB     | OTA 상태    |
| phy_init  | data/phy    | 0xF000   | 4KB     | WiFi 초기화 |
| **ota_0** | app/ota_0   | 0x10000  | **4MB** | 앱 파티션 0 |
| **ota_1** | app/ota_1   | 0x410000 | **4MB** | 앱 파티션 1 |
| spiffs    | data/spiffs | 0x810000 | ~8MB    | 파일 시스템 |

### Single App 버전

| Partition   | Type        | Offset   | Size    | 설명        |
| ----------- | ----------- | -------- | ------- | ----------- |
| nvs         | data/nvs    | 0x9000   | 24KB    | 설정 저장   |
| phy_init    | data/phy    | 0xF000   | 4KB     | WiFi 초기화 |
| **factory** | app/factory | 0x10000  | **6MB** | 앱 파티션   |
| spiffs      | data/spiffs | 0x610000 | ~10MB   | 파일 시스템 |

## 빌드 방법

### 전제 조건

1. ESP-IDF v5.4 이상 설치
2. ESP-IDF 환경 변수 설정 (`export.sh` 또는 `export.bat` 실행)

### 빌드 타입 선택

프로젝트는 두 가지 빌드 타입을 지원합니다:

#### 1. **OTA 버전** (기본값, 프로덕션용) ✨

- 듀얼 파티션 (4MB × 2)
- 무선 펌웨어 업데이트
- 자동 롤백

```powershell
# Windows
.\build.ps1                    # 또는
.\build.ps1 -BuildType ota

# Linux/Mac
idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.ota" build
```

#### 2. **Single App 버전** (개발용) 🚀

- 단일 파티션 (6MB)
- 더 큰 앱 크기
- 빠른 개발

```powershell
# Windows
.\build.ps1 -BuildType single

# Linux/Mac
idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.singleapp" build
```

> 📖 자세한 내용: [BUILD_TYPES.md](BUILD_TYPES.md)

### 플래시

```powershell
# Windows
.\build.ps1 -BuildType ota -Flash -Monitor -Port COM3

# Linux/Mac
idf.py -p /dev/ttyUSB0 flash monitor
```

## 아키텍처

### FreeRTOS 태스크 구조

1. **메인 태스크** (`app_main` → `Application::Run()`)

   - 이벤트 루프 처리
   - 상태 관리
   - 스케줄링된 작업 처리

2. **오디오 입력 태스크** (예정)

   - I2S에서 PCM 데이터 읽기
   - 오디오 처리 파이프라인

3. **오디오 출력 태스크** (예정)

   - 스피커로 PCM 데이터 출력

4. **카메라 태스크** (예정)

   - JPEG 캡처
   - 네트워크 전송

5. **네트워크 태스크** (예정)
   - WiFi 연결 관리
   - MQTT/WebSocket 통신

## 상태 머신

디바이스 상태 전환은 `DeviceStateMachine`을 통해 관리됩니다.

**상태:**

- `kDeviceStateUnknown`: 초기 상태
- `kDeviceStateStarting`: 초기화 중
- `kDeviceStateIdle`: 대기
- `kDeviceStateConnecting`: 네트워크 연결 중
- `kDeviceStateConnected`: 네트워크 연결됨
- `kDeviceStateListening`: 음성 인식 대기
- `kDeviceStateProcessing`: 음성 처리 중
- `kDeviceStateSpeaking`: 음성 출력 중
- `kDeviceStateCameraActive`: 카메라 활성
- `kDeviceStateError`: 오류

## 개발 진행 상황

- [x] 프로젝트 구조 생성
- [x] Application 싱글톤 구현
- [x] 상태 머신 구현
- [x] **OTA 파티션 테이블 설정**
- [x] CoreS3 PSRAM 설정 (Quad mode)
- [x] 오디오 모듈 (I2S, OPUS 코덱)
- [x] 카메라 모듈 (OV2640)
- [x] 네트워크 모듈 (WiFi, MQTT, WebSocket)
- [x] 디스플레이 모듈 (ILI9341)
- [x] ASR 서비스 (음성인식)
- [ ] OTA 서비스 구현
- [ ] 통합 테스트

## OTA 업데이트

OTA(Over-The-Air) 펌웨어 업데이트 지원. 자세한 내용은 [OTA_GUIDE.md](OTA_GUIDE.md) 참조.

### 빠른 OTA 사용법

1. **펌웨어 빌드**

   ```bash
   idf.py build
   # 생성: build/cores3-management.bin
   ```

2. **MQTT로 OTA 명령 전송**

   ```json
   // Topic: devices/{device_id}/command
   {
     "type": "ota_update",
     "firmware_url": "https://your-server.com/firmware/latest.bin",
     "version": "1.0.1"
   }
   ```

3. **기기 자동 재부팅 및 업데이트 적용**

## 참고 자료

- **빌드 타입 가이드:** [BUILD_TYPES.md](BUILD_TYPES.md) 📖
- **OTA 업데이트 가이드:** [OTA_GUIDE.md](OTA_GUIDE.md) 📖
- **ESP-IDF 문서:** https://docs.espressif.com/projects/esp-idf/
- **ESP-IDF OTA:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/system/ota.html
- **FreeRTOS 문서:** https://www.freertos.org/
- **M5Stack CoreS3:** https://docs.m5stack.com/en/core/CoreS3
- **참고 프로젝트:** `xiaozhi-esp32/` (ESP-IDF 기반 완전한 구현)
