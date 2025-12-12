# ESP-IDF 빌드 빠른 시작 가이드

## 1단계: 환경 확인

```powershell
cd firmware_idf
.\check_build_env.ps1
```

모든 항목이 ✅이면 다음 단계로 진행합니다.

## 2단계: 빌드 타입 선택

프로젝트는 두 가지 빌드 타입을 지원합니다:

### 🌟 OTA 버전 (기본값, 프로덕션용)

- 무선 펌웨어 업데이트
- 자동 롤백
- 듀얼 파티션 (4MB × 2)

### 🚀 Single App 버전 (개발용)

- 더 큰 앱 파티션 (6MB)
- 빠른 반복 개발
- OTA 오버헤드 없음

> 📖 자세한 내용: [BUILD_TYPES.md](BUILD_TYPES.md)

## 3단계: 빌드

### 방법 1: 빌드 스크립트 사용 (권장)

```powershell
# OTA 버전 (기본)
.\build.ps1

# Single App 버전
.\build.ps1 -BuildType single

# 빌드 + 플래시 + 모니터
.\build.ps1 -BuildType ota -Flash -Monitor -Port COM3
```

### 방법 2: 수동 빌드

```powershell
# ESP-IDF 환경 설정 (새 터미널마다 필요)
E:\esp32\Espressif\frameworks\esp-idf-v5.5.1\export.ps1

# OTA 버전
idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.ota" set-target esp32s3
idf.py build

# Single App 버전
idf.py -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.singleapp" set-target esp32s3
idf.py build
```

## 4단계: 플래시 및 모니터링

```powershell
# 방법 1: 빌드 스크립트 사용
.\build.ps1 -BuildType ota -Flash -Monitor -Port COM3

# 방법 2: idf.py 직접 사용
idf.py -p COM3 flash monitor
```

## 빌드 옵션

```powershell
# 클린 빌드
.\build.ps1 -BuildType ota -Clean

# 플래시만
.\build.ps1 -Flash -Port COM3

# 모니터링만
idf.py -p COM3 monitor
```

## 빠른 명령어 참조

| 작업               | 명령어                                            |
| ------------------ | ------------------------------------------------- |
| **개발용 빌드**    | `.\build.ps1 -BuildType single`                   |
| **프로덕션 빌드**  | `.\build.ps1 -BuildType ota`                      |
| **빌드 + 플래시**  | `.\build.ps1 -BuildType single -Flash -Port COM3` |
| **클린 빌드**      | `.\build.ps1 -BuildType ota -Clean`               |
| **빌드 타입 전환** | `.\build.ps1 -BuildType single -Clean`            |

## 문제 해결

빌드 오류 발생 시:

1. **환경 확인:**

   ```powershell
   .\check_build_env.ps1
   ```

2. **빌드 타입 전환 시 클린 빌드:**

   ```powershell
   Remove-Item -Recurse -Force build
   .\build.ps1 -BuildType <ota|single>
   ```

3. **상세 빌드 로그:**

   ```powershell
   idf.py build -v
   ```

4. **완전 초기화:**
   ```powershell
   Remove-Item sdkconfig, sdkconfig.old
   Remove-Item -Recurse build
   .\build.ps1 -BuildType ota
   ```

## 시리얼 포트 확인

Windows에서 COM 포트 확인:

```powershell
mode
# 또는
Get-WmiObject Win32_SerialPort | Select-Object Name, DeviceID
```

Linux/Mac에서:

```bash
ls /dev/tty*
```

## 참고 자료

- **빌드 타입 가이드:** [BUILD_TYPES.md](BUILD_TYPES.md) 📖
- **상세 빌드 가이드:** [BUILD_GUIDE.md](BUILD_GUIDE.md)
- **OTA 업데이트:** [OTA_GUIDE.md](OTA_GUIDE.md)
- **ESP-IDF 문서:** https://docs.espressif.com/projects/esp-idf/
