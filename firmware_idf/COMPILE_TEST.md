# ESP-IDF 컴파일 테스트 가이드

**작성일:** 2025-12-10

---

## 빠른 시작

### 1단계: 환경 확인

```powershell
cd firmware_idf
.\check_build_env.ps1
```

모든 항목이 ✅이면 다음 단계로 진행합니다.

### 2단계: 빌드

```powershell
.\build.ps1
```

---

## 상세 가이드

### 방법 1: 빌드 스크립트 사용 (권장)

**기본 빌드:**
```powershell
cd firmware_idf
.\build.ps1
```

**옵션:**
```powershell
# 클린 빌드
.\build.ps1 -Clean

# 빌드 + 플래시
.\build.ps1 -Flash -Port COM3

# 빌드 + 플래시 + 모니터링
.\build.ps1 -Flash -Monitor -Port COM3

# ESP-IDF 경로 지정
.\build.ps1 -IdfPath "C:\Espressif\frameworks\esp-idf-v5.4"
```

### 방법 2: 수동 빌드

**1. ESP-IDF 환경 설정 (새 터미널마다 필요)**

PowerShell에서:
```powershell
C:\Espressif\frameworks\esp-idf-v5.4\export.ps1
```

또는 CMD에서:
```cmd
C:\Espressif\frameworks\esp-idf-v5.4\export.bat
```

**2. 프로젝트 디렉토리로 이동**
```powershell
cd D:\cursorworks\roidetyolo_esp32cam\firmware_idf
```

**3. 타겟 설정**
```powershell
idf.py set-target esp32s3
```

**4. 빌드**
```powershell
idf.py build
```

**5. 빌드 결과 확인**
- 성공 시: `build/cores3-management.bin` 생성
- 실패 시: 오류 메시지 확인

---

## 빌드 오류 해결

### 오류 1: ESP-IDF 환경 변수 미설정

**증상:**
```
'idf.py' is not recognized
```

**해결:**
```powershell
C:\Espressif\frameworks\esp-idf-v5.4\export.ps1
```

### 오류 2: 컴포넌트 누락

**증상:**
```
Component 'xxx' not found
```

**해결:**
```powershell
# 컴포넌트 매니저 업데이트
idf.py reconfigure
```

### 오류 3: CMake 오류

**증상:**
```
CMake Error: ...
```

**해결:**
```powershell
# 클린 빌드
idf.py fullclean
idf.py build
```

### 오류 4: 컴파일 오류

**확인 사항:**
1. 모든 헤더 파일 경로 확인
2. `CMakeLists.txt`의 `INCLUDE_DIRS` 확인
3. 컴포넌트 의존성 확인 (`REQUIRES`)

**해결:**
```powershell
# 상세 빌드 로그
idf.py build -v 2>&1 | Select-String "error"
```

---

## 빌드 성공 확인

빌드 성공 시 다음 파일들이 생성됩니다:

```
firmware_idf/build/
├── cores3-management.bin          # 메인 펌웨어
├── bootloader/
│   └── bootloader.bin            # 부트로더
└── partition_table/
    └── partition-table.bin       # 파티션 테이블
```

**빌드 크기 확인:**
```powershell
idf.py size
```

---

## 플래시 및 모니터링

### 플래시

```powershell
# 포트 자동 감지
idf.py flash

# 포트 지정
idf.py -p COM3 flash
```

### 모니터링

```powershell
# 모니터링만
idf.py -p COM3 monitor

# 플래시 + 모니터링 (한 번에)
idf.py -p COM3 flash monitor
```

**모니터 종료:** `Ctrl+]`

---

## 빌드 옵션

### 병렬 빌드 (빠른 빌드)

```powershell
# CPU 코어 수만큼 병렬 빌드
idf.py -j$(nproc) build
```

### 상세 빌드 로그

```powershell
idf.py build -v
```

### 빌드 정보

```powershell
# 빌드 크기 정보
idf.py size

# 컴포넌트별 크기
idf.py size-components
```

---

## 메뉴 설정

### 메뉴 설정 열기

```powershell
idf.py menuconfig
```

### 주요 설정 항목

- **Serial flasher config**: 플래시 포트, 속도
- **Partition Table**: 파티션 테이블 선택
- **Component config**:
  - **ESP32S3-Specific**: PSRAM, CPU 주파수
  - **WiFi**: WiFi 설정
  - **Camera**: 카메라 설정

---

## 문제 해결 체크리스트

빌드 전:
- [ ] ESP-IDF v5.4 이상 설치됨
- [ ] 환경 변수 설정됨 (`idf.py --version` 확인)
- [ ] Python 3.8 이상 설치됨
- [ ] 프로젝트 디렉토리 구조 확인
- [ ] `CMakeLists.txt` 파일 존재

빌드 후:
- [ ] `build/` 디렉토리 생성됨
- [ ] `build/cores3-management.bin` 파일 생성됨
- [ ] 빌드 오류 없음
- [ ] 경고만 있고 오류는 없음

---

## 참고 자료

- **상세 가이드:** `BUILD_GUIDE.md`
- **빠른 시작:** `QUICK_START.md`
- **ESP-IDF 문서:** https://docs.espressif.com/projects/esp-idf/

---

**작성자:** AI Assistant  
**마지막 업데이트:** 2025-12-10

