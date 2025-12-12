# ESP-IDF 빌드 가이드

**작성일:** 2025-12-10  
**프로젝트:** Core S3 Management System - ESP-IDF Version

---

## 전제 조건

### 1. ESP-IDF 설치

ESP-IDF v5.4 이상이 필요합니다.

**Windows 설치 방법:**

1. **ESP-IDF 설치 프로그램 사용 (권장)**
   - https://dl.espressif.com/dl/esp-idf/ 에서 최신 설치 프로그램 다운로드
   - 설치 프로그램 실행 후 ESP-IDF v5.4 이상 선택
   - 설치 경로: `C:\Espressif\frameworks\esp-idf-v5.4` (기본값)

2. **수동 설치**
   ```powershell
   # Git 설치 필요
   git clone --recursive https://github.com/espressif/esp-idf.git
   cd esp-idf
   git checkout v5.4
   git submodule update --init --recursive
   
   # 설치 스크립트 실행
   .\install.bat esp32,esp32s3
   ```

**Linux/Ubuntu 설치 방법:**

1. **필수 패키지 설치**
   ```bash
   sudo apt-get update
   sudo apt-get install -y git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0
   ```

2. **ESP-IDF 다운로드 및 설치**
   ```bash
   mkdir -p ~/esp
   cd ~/esp
   git clone --recursive https://github.com/espressif/esp-idf.git
   cd esp-idf
   git checkout v5.4
   git submodule update --init --recursive
   
   # 설치 스크립트 실행
   ./install.sh esp32,esp32s3
   ```

### 2. ESP-IDF 환경 변수 설정

**Windows PowerShell에서:**
```powershell
# ESP-IDF 설치 경로로 이동
cd C:\Espressif\frameworks\esp-idf-v5.4

# 환경 변수 설정 (매번 실행 필요)
.\export.ps1
```

**Windows CMD에서:**
```cmd
cd C:\Espressif\frameworks\esp-idf-v5.4
.\export.bat
```

**Linux/Ubuntu에서:**
```bash
# ESP-IDF 설치 경로로 이동
cd ~/esp/esp-idf

# 환경 변수 설정 (매번 실행 필요)
. ./export.sh
```

**영구 설정 (선택사항):**

**Windows:**
- 시스템 환경 변수에 `IDF_PATH` 추가: `C:\Espressif\frameworks\esp-idf-v5.4`
- PATH에 추가: `%IDF_PATH%\tools`

**Linux:**
- `~/.bashrc` 또는 `~/.zshrc`에 추가:
  ```bash
  alias get_idf='. $HOME/esp/esp-idf/export.sh'
  ```
  사용 시: `get_idf` 명령 실행

---

## 빌드 방법

### 방법 1: 빌드 스크립트 사용 (권장)

**Windows:**
```powershell
cd firmware_idf
.\build.ps1
```

**Linux/Ubuntu:**
```bash
cd firmware_idf
./build.sh
```

**옵션:**
- `--flash` 또는 `-f`: 빌드 후 플래시
- `--monitor` 또는 `-m`: 플래시 후 시리얼 모니터 시작
- `--port PORT` 또는 `-p PORT`: 시리얼 포트 지정
- `--clean` 또는 `-c`: 클린 빌드
- `--help` 또는 `-h`: 도움말

**예제:**
```bash
# 빌드만
./build.sh

# 빌드 후 플래시
./build.sh --flash

# 빌드, 플래시, 모니터링
./build.sh --flash --monitor

# 특정 포트로 플래시
./build.sh --port /dev/ttyUSB0 --flash
```

### 방법 2: 수동 빌드

#### 1. 프로젝트 디렉토리로 이동

**Windows:**
```powershell
cd D:\cursorworks\roidetyolo_esp32cam\firmware_idf
```

**Linux:**
```bash
cd /path/to/roidetyolo_esp32cam/firmware_idf
```

#### 2. ESP-IDF 환경 설정 (새 터미널마다 필요)

**Windows:**
```powershell
# ESP-IDF 환경 변수 설정
C:\Espressif\frameworks\esp-idf-v5.4\export.ps1
```

**Linux:**
```bash
# ESP-IDF 환경 변수 설정
. ~/esp/esp-idf/export.sh
```

#### 3. 타겟 칩 설정

M5Stack Core S3는 ESP32-S3를 사용합니다:

```bash
idf.py set-target esp32s3
```

#### 4. 빌드 실행

```bash
idf.py build
```

#### 5. 빌드 결과 확인

빌드 성공 시:
- `build/` 디렉토리에 펌웨어 파일 생성
- `build/cores3-management.bin` - 플래시용 바이너리
- `build/bootloader/bootloader.bin` - 부트로더
- `build/partition_table/partition-table.bin` - 파티션 테이블

---

## 빌드 오류 해결

### 오류 1: ESP-IDF 환경 변수 미설정

**증상:**
```
'idf.py' is not recognized as an internal or external command
```

**해결:**
```powershell
# ESP-IDF export 스크립트 실행
C:\Espressif\frameworks\esp-idf-v5.4\export.ps1
```

### 오류 2: Python 버전 문제

**증상:**
```
Python version mismatch
```

**해결:**
- Python 3.8 이상 필요
- ESP-IDF 설치 프로그램이 자동으로 Python 환경 설정

### 오류 3: 컴포넌트 누락

**증상:**
```
Component 'xxx' not found
```

**해결:**
```powershell
# 컴포넌트 매니저 업데이트
idf.py reconfigure
```

### 오류 4: CMake 오류

**증상:**
```
CMake Error: ...
```

**해결:**
```powershell
# 빌드 디렉토리 정리 후 재빌드
idf.py fullclean
idf.py build
```

---

## 빠른 빌드 스크립트

프로젝트에 포함된 빌드 스크립트를 사용할 수 있습니다:

- **Windows:** `build.ps1` (PowerShell)
- **Linux:** `build.sh` (Bash)

자세한 사용법은 위의 "방법 1: 빌드 스크립트 사용" 섹션을 참조하세요.

---

## 플래시 및 모니터링

### 1. 펌웨어 플래시

**Windows:**
```powershell
# 포트 자동 감지
idf.py flash

# 또는 포트 지정
idf.py -p COM3 flash
```

**Linux:**
```bash
# 포트 자동 감지
idf.py flash

# 또는 포트 지정
idf.py -p /dev/ttyUSB0 flash
```

### 2. 시리얼 모니터

**Windows:**
```powershell
# 플래시 후 자동 모니터링
idf.py -p COM3 flash monitor

# 모니터링만
idf.py -p COM3 monitor
```

**Linux:**
```bash
# 플래시 후 자동 모니터링
idf.py -p /dev/ttyUSB0 flash monitor

# 모니터링만
idf.py -p /dev/ttyUSB0 monitor
```

### 3. 플래시 + 모니터링 (한 번에)

**Windows:**
```powershell
idf.py -p COM3 flash monitor
```

**Linux:**
```bash
idf.py -p /dev/ttyUSB0 flash monitor
```

**모니터 종료:** `Ctrl+]`

---

## 빌드 옵션

### 1. 클린 빌드

```powershell
# 전체 클린
idf.py fullclean
idf.py build

# 또는
idf.py clean build
```

### 2. 병렬 빌드 (빠른 빌드)

**Windows:**
```powershell
# CPU 코어 수만큼 병렬 빌드
idf.py -j$env:NUMBER_OF_PROCESSORS build
```

**Linux:**
```bash
# CPU 코어 수만큼 병렬 빌드
idf.py -j$(nproc) build
```

### 3. 상세 빌드 로그

```bash
# 상세 로그 출력
idf.py build -v
```

### 4. 빌드 정보 확인

```powershell
# 빌드 크기 정보
idf.py size

# 빌드 구성 정보
idf.py show_efuse_table
```

---

## 메뉴 설정 (sdkconfig)

### 1. 메뉴 설정 열기

```bash
idf.py menuconfig
```

### 2. 주요 설정 항목

- **Serial flasher config**: 플래시 포트, 속도 설정
- **Partition Table**: 파티션 테이블 선택
- **Component config**: 컴포넌트별 설정
  - **ESP32S3-Specific**: PSRAM, CPU 주파수 등
  - **WiFi**: WiFi 설정
  - **Camera**: 카메라 설정

### 3. 설정 저장

메뉴에서 `Save` 선택 후 `Quit`

---

## 파티션 테이블 설정

M5Stack Core S3는 16MB Flash를 사용합니다.

**파티션 테이블 파일 생성:** `partitions.csv`

```
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,  0x6000,
phy_init, data, phy,     0xf000,  0x1000,
factory,  app,  factory, 0x10000, 0x200000,
```

**CMakeLists.txt에 추가:**
```cmake
set(PARTITION_TABLE_CSV_PATH "${CMAKE_CURRENT_SOURCE_DIR}/partitions.csv")
```

---

## 디버깅

### 1. 로그 레벨 설정

`menuconfig`에서:
- **Component config** → **Log output** → **Default log verbosity**
- 선택: **Info** 또는 **Debug**

### 2. 컴포넌트별 로그 레벨

코드에서:
```cpp
#include <esp_log.h>

// 로그 레벨 설정
esp_log_level_set("AudioService", ESP_LOG_DEBUG);
esp_log_level_set("CameraService", ESP_LOG_INFO);
```

### 3. 시리얼 모니터 필터

```bash
# 특정 태그만 필터링
idf.py monitor --print-filter="AudioService:*"
```

---

## 빌드 검증 체크리스트

빌드 전 확인:
- [ ] ESP-IDF v5.4 이상 설치됨
- [ ] 환경 변수 설정됨 (`idf.py --version` 확인)
- [ ] Python 3.8 이상 설치됨
- [ ] 프로젝트 디렉토리 구조 확인
- [ ] `CMakeLists.txt` 파일 존재
- [ ] `main/CMakeLists.txt` 파일 존재
- [ ] `idf_component.yml` 파일 존재

빌드 후 확인:
- [ ] `build/` 디렉토리 생성됨
- [ ] `build/cores3-management.bin` 파일 생성됨
- [ ] 빌드 오류 없음
- [ ] 경고만 있고 오류는 없음

---

## 문제 해결

### 문제 1: 컴파일 오류

**확인 사항:**
1. 모든 헤더 파일 경로 확인
2. `CMakeLists.txt`의 `INCLUDE_DIRS` 확인
3. 컴포넌트 의존성 확인 (`REQUIRES`)

**해결:**

**Windows:**
```powershell
# 상세 빌드 로그로 오류 확인
idf.py build -v 2>&1 | Select-String "error"
```

**Linux:**
```bash
# 상세 빌드 로그로 오류 확인
idf.py build -v 2>&1 | grep -i error
```

### 문제 2: 링크 오류

**확인 사항:**
1. 모든 소스 파일이 `CMakeLists.txt`에 포함됨
2. 라이브러리 의존성 확인

**해결:**
```bash
# 링크 맵 확인
idf.py size-components
```

### 문제 3: 메모리 부족

**확인 사항:**
1. 파티션 테이블 크기 확인
2. 스택 크기 확인

**해결:**
```bash
# menuconfig에서 파티션 테이블 크기 조정
idf.py menuconfig

# 태스크 스택 크기 조정
# 코드에서 xTaskCreate의 스택 크기 파라미터 증가
```

---

## 참고 자료

- **ESP-IDF 문서:** https://docs.espressif.com/projects/esp-idf/
- **빌드 시스템:** https://docs.espressif.com/projects/esp-idf/en/latest/api-guides/build-system.html
- **M5Stack Core S3:** https://docs.m5stack.com/en/core/CoreS3

---

**작성자:** AI Assistant  
**마지막 업데이트:** 2025-12-10

