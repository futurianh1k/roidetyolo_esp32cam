# 펌웨어 빌드 환경 안정화 가이드

**작성일**: 2025-12-10  
**대상**: M5Stack Core S3  
**상태**: ✅ 빌드 환경 안정화 완료

---

## 📋 개요

M5Stack Core S3 펌웨어의 빌드 환경을 안정화하여 빌드 에러 없이 컴파일할 수 있도록 구성했습니다.

---

## 🔧 빌드 환경 구성

### PlatformIO 설정

**파일**: `firmware/platformio.ini`

**주요 설정**:

```ini
[env:m5stack-cores3]
platform = espressif32          # 최신 안정 버전 자동 선택
board = m5stack-cores3          # M5Stack Core S3 보드
framework = arduino             # Arduino Core 프레임워크
extra_scripts = pre:pre_build.py
```

**빌드 플래그** (최소한의 필수 플래그만 사용):

- `-DCORE_DEBUG_LEVEL=4`: 디버그 레벨
- `-DESP32S3`: ESP32-S3 타겟 지정
- `-DBOARD_HAS_PSRAM`: PSRAM 지원
- `-mfix-esp32-psram-cache-issue`: PSRAM 캐시 이슈 수정
- `-DARDUINO_M5STACK_CORES3`: M5Stack Core S3 보드 식별
- `-DARDUINO_USB_CDC_ON_BOOT=1`: USB CDC 활성화
- `-DARDUINO_USB_MODE=1`: USB 모드 설정
- `-DMQTT_MAX_PACKET_SIZE=1024`: MQTT 패킷 크기 제한

**라이브러리 의존성**:

- `m5stack/M5Unified@^0.1.13`: M5Stack 통합 라이브러리
- `m5stack/M5GFX@^0.1.14`: M5Stack 그래픽 라이브러리
- `knolleary/PubSubClient@^2.8`: MQTT 클라이언트
- `bblanchon/ArduinoJson@^6.21.4`: JSON 파싱
- `espressif/esp32-camera`: ESP32 카메라 드라이버
- `gilmaimon/ArduinoWebsockets@^0.5.3`: WebSocket 클라이언트

---

## 🛠️ 빌드 전 스크립트

**파일**: `firmware/pre_build.py`

**기능**:

1. **M5GFX 라이브러리 패치**
   - `lgfx_qrcode.h`의 `bool` 타입 재정의 문제 해결
   - C/C++ 혼합 컴파일 충돌 방지

**패치 내용**:

```cpp
// Before
#ifndef __cplusplus
typedef unsigned char bool;
...

// After
#if !defined(__cplusplus) && !defined(__bool_true_false_are_defined)
typedef unsigned char bool;
...
```

---

## ✅ 빌드 확인

### 빌드 명령어

```bash
cd firmware
pio run
```

### 빌드 성공 확인

빌드가 성공하면 다음과 같은 메시지가 표시됩니다:

```
Building in release mode
...
Linking .pio\build\m5stack-cores3\firmware.elf
...
SUCCESS
```

### 펌웨어 업로드

```bash
pio run --target upload
```

---

## 🔍 문제 해결

### 1. 빌드 에러가 발생하는 경우

**증상**: 컴파일 에러 발생

**해결 방법**:

1. **빌드 캐시 정리**:

   ```bash
   cd firmware
   pio run --target clean
   ```

2. **플랫폼 패키지 업데이트**:

   ```bash
   pio pkg update
   ```

3. **라이브러리 재설치**:
   ```bash
   pio lib uninstall --all
   pio lib install
   ```

### 2. M5GFX 라이브러리 충돌

**증상**: `bool` 타입 재정의 에러

**해결 방법**:

- `pre_build.py`가 자동으로 패치를 적용합니다
- 패치가 적용되지 않으면 수동으로 확인:
  ```bash
  # .pio/libdeps/m5stack-cores3/M5GFX@*/src/lgfx/utility/lgfx_qrcode.h
  # 파일의 bool 정의 부분 확인
  ```

### 3. WiFi 라이브러리 에러

**증상**: IPv6 관련 에러

**해결 방법**:

- 현재 설정에서는 기본 Arduino WiFi 라이브러리 사용
- 추가 설정이 필요한 경우 `platformio.ini`에 빌드 플래그 추가

---

## 📊 빌드 환경 정보

### PlatformIO 버전

- **플랫폼**: `espressif32` (최신 안정 버전)
- **보드**: `m5stack-cores3`
- **프레임워크**: `arduino`

### 라이브러리 버전

- **M5Unified**: `^0.1.13`
- **M5GFX**: `^0.1.14`
- **PubSubClient**: `^2.8`
- **ArduinoJson**: `^6.21.4`
- **ArduinoWebsockets**: `^0.5.3`

### 하드웨어 설정

- **CPU 주파수**: 240MHz
- **Flash 주파수**: 80MHz
- **PSRAM**: QIO OPI 모드
- **파티션 테이블**: `huge_app.csv` (4MB Flash)

---

## 🎯 다음 단계

빌드 환경이 안정화되었으므로 다음 단계로 진행할 수 있습니다:

1. **Phase 2: 기본 기능 복구**

   - 디스플레이 기능
   - 오디오 기능
   - 카메라 기능
   - 상태 보고

2. **Phase 3: ASR WebSocket 통신**
   - WebSocket 모듈 구현
   - 오디오 스트리밍

---

## 📝 변경 사항 요약

### 수정된 파일

1. **`firmware/platformio.ini`**

   - 최소한의 필수 빌드 플래그만 유지
   - 불필요한 복잡한 설정 제거
   - 명확한 주석 추가

2. **`firmware/pre_build.py`**
   - `sdkconfig.h` 복사 로직 제거 (PlatformIO가 자동 생성)
   - M5GFX 라이브러리 패치만 유지
   - 코드 단순화

### 제거된 설정

- `esp_log_fix.h` 헤더 파일 (불필요)
- 복잡한 ESP-IDF 로그 시스템 설정
- WiFi IPv6 관련 빌드 플래그
- `sdkconfig.h` 수동 복사 로직

---

## ✅ 검증 완료

- ✅ `pio run` 성공
- ✅ 빌드 에러 없음
- ✅ 라이브러리 의존성 해결
- ✅ M5GFX 패치 자동 적용

---

**작성일**: 2025-12-10  
**상태**: ✅ 빌드 환경 안정화 완료  
**다음 단계**: Phase 2 - 기본 기능 복구
