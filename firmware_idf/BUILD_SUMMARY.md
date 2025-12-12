# 빌드 설정 완료 요약

## ✅ 생성된 파일

### 파티션 테이블

- ✅ `partitions_custom.csv` - OTA 버전 (2×4MB 듀얼 파티션)
- ✅ `partitions_singleapp.csv` - Single App 버전 (6MB 단일 파티션)

### 설정 파일

- ✅ `sdkconfig.defaults` - 공통 기본 설정 (M5Stack CoreS3)
- ✅ `sdkconfig.ota` - OTA 버전 전용 설정
- ✅ `sdkconfig.singleapp` - Single App 버전 전용 설정

### 문서

- ✅ `BUILD_TYPES.md` - 빌드 타입 상세 가이드
- ✅ `OTA_GUIDE.md` - OTA 업데이트 가이드
- ✅ `QUICK_START.md` - 빠른 시작 가이드 (업데이트됨)
- ✅ `README.md` - 프로젝트 README (업데이트됨)

### 빌드 스크립트

- ✅ `build.ps1` - 업데이트됨 (BuildType 매개변수 추가)

---

## 🚀 빌드 명령어

### OTA 버전 (프로덕션)

```powershell
# 기본 빌드
.\build.ps1

# 또는 명시적으로
.\build.ps1 -BuildType ota

# 플래시 포함
.\build.ps1 -BuildType ota -Flash -Monitor -Port COM3

# 클린 빌드
.\build.ps1 -BuildType ota -Clean
```

### Single App 버전 (개발)

```powershell
# 빌드
.\build.ps1 -BuildType single

# 플래시 포함
.\build.ps1 -BuildType single -Flash -Monitor -Port COM3

# 클린 빌드
.\build.ps1 -BuildType single -Clean
```

---

## 📊 파티션 비교

### OTA 버전 (partitions_custom.csv)

```
nvs       (16KB)   - 설정 저장
otadata   (8KB)    - OTA 상태 정보
phy_init  (4KB)    - WiFi PHY 초기화
ota_0     (4MB)    - 앱 파티션 0 ← 현재 실행
ota_1     (4MB)    - 앱 파티션 1 ← 업데이트 대상
spiffs    (~8MB)   - 파일 시스템

총 16MB 활용
```

**특징:**

- ✅ 무선 펌웨어 업데이트
- ✅ 자동 Rollback
- ❌ 앱 크기 제한 4MB

### Single App 버전 (partitions_singleapp.csv)

```
nvs       (24KB)   - 설정 저장
phy_init  (4KB)    - WiFi PHY 초기화
factory   (6MB)    - 앱 파티션 (단일)
spiffs    (~10MB)  - 파일 시스템 (더 큼!)

총 16MB 활용
```

**특징:**

- ✅ 큰 앱 크기 (6MB)
- ✅ 큰 파일 시스템 (~10MB)
- ✅ 빠른 개발
- ❌ OTA 불가

---

## 🔄 빌드 타입 전환

### OTA → Single App

```powershell
# 클린 빌드 권장
.\build.ps1 -BuildType single -Clean
.\build.ps1 -BuildType single -Flash -Port COM3
```

### Single App → OTA

```powershell
# 클린 빌드 권장
.\build.ps1 -BuildType ota -Clean
.\build.ps1 -BuildType ota -Flash -Port COM3
```

⚠️ **중요:** 빌드 타입 전환 시 반드시 `-Clean` 플래그를 사용하세요!

---

## 💡 사용 권장 사항

### 개발 단계

```powershell
.\build.ps1 -BuildType single
```

- 빠른 반복 개발
- 큰 디버그 정보 포함 가능
- OTA 오버헤드 없음

### 테스트 단계

```powershell
.\build.ps1 -BuildType ota
```

- OTA 업데이트 기능 테스트
- 롤백 시나리오 검증

### 프로덕션 배포

```powershell
.\build.ps1 -BuildType ota -Clean
```

- 무선 펌웨어 업데이트
- 안전한 업데이트 프로세스
- 자동 롤백

---

## 📖 관련 문서

1. **빌드 타입 선택:** [BUILD_TYPES.md](BUILD_TYPES.md)

   - 두 빌드 타입의 상세 비교
   - 사용 케이스별 권장사항

2. **OTA 업데이트:** [OTA_GUIDE.md](OTA_GUIDE.md)

   - OTA 업데이트 구현 방법
   - HTTPS/MQTT/HTTP 업로드 방식
   - 안전성 확인 및 롤백

3. **빠른 시작:** [QUICK_START.md](QUICK_START.md)

   - 환경 설정
   - 빌드 및 플래시
   - 문제 해결

4. **프로젝트 README:** [README.md](README.md)
   - 프로젝트 개요
   - 하드웨어 사양
   - 아키텍처 설명

---

## 🎯 현재 상태

### M5Stack CoreS3 설정

- ✅ CPU: ESP32-S3 @ 240MHz
- ✅ Flash: 16MB
- ✅ PSRAM: 8MB (Quad mode) ⚠️
- ✅ 파티션: OTA / Single App 선택 가능
- ✅ 빌드 스크립트: PowerShell 자동화

### 빌드 시스템

- ✅ ESP-IDF v5.5.1 호환
- ✅ 자동 환경 감지
- ✅ 빌드 타입 선택 (-BuildType ota|single)
- ✅ 플래시 및 모니터링 통합
- ✅ 클린 빌드 지원

---

## 🚨 주의 사항

### PSRAM 설정 (중요!)

M5Stack CoreS3는 **Quad mode PSRAM**을 사용합니다.

- ✅ `CONFIG_SPIRAM_MODE_QUAD=y` (올바름)
- ❌ `CONFIG_SPIRAM_MODE_OCT=y` (크래시 발생!)

현재 `sdkconfig.defaults`에 올바르게 설정되어 있습니다.

### 빌드 타입 전환

빌드 타입을 변경할 때는 항상 클린 빌드를 수행하세요:

```powershell
.\build.ps1 -BuildType single -Clean
```

---

## 📞 다음 단계

1. **빌드 테스트:**

   ```powershell
   .\build.ps1 -BuildType single
   ```

2. **플래시 및 테스트:**

   ```powershell
   .\build.ps1 -BuildType single -Flash -Monitor -Port COM3
   ```

3. **OTA 버전으로 전환 테스트:**
   ```powershell
   .\build.ps1 -BuildType ota -Clean -Flash -Port COM3
   ```

---

**작성일:** 2025-12-13  
**ESP-IDF 버전:** v5.5.1  
**타겟:** M5Stack CoreS3 (ESP32-S3)
