# 빌드 타입 가이드

CoreS3 Management 펌웨어는 두 가지 빌드 타입을 지원합니다.

## 빌드 타입 비교

### 1. OTA 버전 (기본값) ✨

**사용 케이스:**

- 프로덕션 환경
- 원격 펌웨어 업데이트 필요
- 안전한 업데이트와 자동 롤백 필요

**특징:**

- ✅ 듀얼 파티션 (ota_0, ota_1)
- ✅ 무선 펌웨어 업데이트 (HTTPS/MQTT)
- ✅ 자동 롤백 (부팅 실패 시)
- ❌ 앱 파티션 크기 제한 (각 4MB)

**파티션 레이아웃:**

```
nvs       (16KB)  - 설정 저장
otadata   (8KB)   - OTA 상태
phy_init  (4KB)   - WiFi 초기화
ota_0     (4MB)   - 앱 파티션 0 ← 현재 실행
ota_1     (4MB)   - 앱 파티션 1 ← 업데이트 대상
spiffs    (~8MB)  - 파일 시스템
```

**빌드 명령:**

```powershell
# 기본 (OTA)
.\build.ps1

# 명시적
.\build.ps1 -BuildType ota

# 플래시 포함
.\build.ps1 -BuildType ota -Flash -Monitor
```

---

### 2. Single App 버전 🚀

**사용 케이스:**

- 개발 및 테스트
- OTA 불필요
- 큰 앱 크기 필요 (AI 모델, 에셋 등)
- 빠른 반복 개발

**특징:**

- ✅ 단일 파티션 (factory)
- ✅ 더 큰 앱 파티션 (6MB)
- ✅ 더 큰 파일 시스템 (~10MB)
- ❌ OTA 업데이트 불가
- ❌ 롤백 불가

**파티션 레이아웃:**

```
nvs       (24KB)  - 설정 저장
phy_init  (4KB)   - WiFi 초기화
factory   (6MB)   - 앱 파티션 ← 단일
spiffs    (~10MB) - 파일 시스템 (더 큼)
```

**빌드 명령:**

```powershell
# Single App 버전
.\build.ps1 -BuildType single

# 플래시 포함
.\build.ps1 -BuildType single -Flash -Monitor

# 클린 빌드
.\build.ps1 -BuildType single -Clean
```

---

## 빌드 타입 전환

### OTA → Single App

```powershell
# 1. 클린 빌드 (권장)
.\build.ps1 -BuildType single -Clean

# 2. 플래시
.\build.ps1 -BuildType single -Flash
```

### Single App → OTA

```powershell
# 1. 클린 빌드 (권장)
.\build.ps1 -BuildType ota -Clean

# 2. 플래시
.\build.ps1 -BuildType ota -Flash
```

**⚠️ 중요:** 빌드 타입을 전환할 때는 `-Clean` 플래그를 사용하여 클린 빌드를 권장합니다.

---

## 파티션 크기 비교

| 구분            | OTA 버전 | Single App 버전 |
| --------------- | -------- | --------------- |
| **앱 파티션**   | 4MB × 2  | 6MB × 1         |
| **파일 시스템** | ~8MB     | ~10MB           |
| **업데이트**    | 무선 OTA | USB만           |
| **롤백**        | 자동     | 없음            |
| **개발 속도**   | 보통     | 빠름            |
| **프로덕션**    | 권장     | 비권장          |

---

## 빌드 스크립트 전체 옵션

```powershell
.\build.ps1 `
    -BuildType <ota|single> `  # 빌드 타입 (기본: ota)
    -Target <esp32s3>       `  # 타겟 (기본: esp32s3)
    -Port <COM3>            `  # 시리얼 포트
    -Flash                  `  # 플래시 수행
    -Monitor                `  # 시리얼 모니터 시작
    -Clean                  `  # 클린 빌드
    -IdfPath <경로>         `  # ESP-IDF 경로 (자동 감지)
```

### 예시

**개발용 (Single App, 빠른 반복):**

```powershell
# 빌드만
.\build.ps1 -BuildType single

# 빌드 + 플래시 + 모니터
.\build.ps1 -BuildType single -Flash -Monitor -Port COM3
```

**프로덕션용 (OTA):**

```powershell
# OTA 빌드
.\build.ps1 -BuildType ota

# 클린 빌드 + 플래시
.\build.ps1 -BuildType ota -Clean -Flash -Port COM3
```

---

## 현재 빌드 타입 확인

빌드된 펌웨어의 파티션 테이블 확인:

```powershell
# 파티션 테이블 보기
idf.py partition-table

# 또는
esptool.py --chip esp32s3 --port COM3 read_flash 0x8000 0x1000 partition.bin
python %IDF_PATH%\components\partition_table\parttool.py partition.bin
```

---

## 문제 해결

### 빌드 실패 시

```powershell
# 1. 완전 클린 빌드
Remove-Item -Recurse -Force build
.\build.ps1 -BuildType <ota|single>

# 2. sdkconfig 재생성
Remove-Item sdkconfig
.\build.ps1 -BuildType <ota|single>
```

### 플래시 실패 시

```powershell
# 1. 포트 확인
mode

# 2. 올바른 포트로 플래시
.\build.ps1 -BuildType <ota|single> -Flash -Port COM3

# 3. 수동 플래시
idf.py -p COM3 flash
```

---

## 권장 사항

### 개발 단계

- **Single App 사용**
- 빠른 반복 개발
- 큰 디버그 정보 포함 가능

### 테스트 단계

- **OTA 버전으로 전환**
- OTA 업데이트 기능 테스트
- 롤백 시나리오 검증

### 프로덕션 배포

- **OTA 버전 필수**
- 원격 펌웨어 업데이트
- 안전한 업데이트 프로세스

---

## 참고 자료

- **ESP-IDF 파티션 테이블:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/partition-tables.html
- **OTA 업데이트 가이드:** [OTA_GUIDE.md](OTA_GUIDE.md)
- **빌드 스크립트:** [build.ps1](build.ps1)
