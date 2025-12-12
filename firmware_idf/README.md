# Core S3 Management System - ESP-IDF Version

ESP-IDF 기반 펌웨어 (FreeRTOS 멀티태스크 구조)

## 프로젝트 구조

```
firmware_idf/
├── CMakeLists.txt          # 프로젝트 루트 CMakeLists
├── main/
│   ├── CMakeLists.txt      # Main 컴포넌트 CMakeLists
│   ├── idf_component.yml   # 컴포넌트 의존성
│   ├── main.cc             # 진입점 (app_main)
│   ├── application.h/cc    # Application 싱글톤
│   ├── device_state.h       # 상태 정의
│   ├── device_state_machine.h/cc  # 상태 머신
│   ├── audio/              # 오디오 모듈
│   ├── camera/             # 카메라 모듈
│   ├── network/            # 네트워크 모듈
│   ├── display/            # 디스플레이 모듈
│   └── status/             # 상태 모듈
└── sdkconfig.defaults      # ESP-IDF 설정 기본값
```

## 빌드 방법

### 전제 조건

1. ESP-IDF v5.4 이상 설치
2. ESP-IDF 환경 변수 설정 (`export.sh` 또는 `export.bat` 실행)

### 빌드

```bash
cd firmware_idf
idf.py build
```

### 플래시

```bash
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
- [ ] 오디오 모듈 ESP-IDF 변환
- [ ] 카메라 모듈 ESP-IDF 변환
- [ ] 네트워크 모듈 ESP-IDF 변환
- [ ] 디스플레이 모듈 ESP-IDF 변환
- [ ] 통합 테스트

## 참고 자료

- **ESP-IDF 문서:** https://docs.espressif.com/projects/esp-idf/
- **FreeRTOS 문서:** https://www.freertos.org/
- **참고 프로젝트:** `xiaozhi-esp32/` (ESP-IDF 기반 완전한 구현)

