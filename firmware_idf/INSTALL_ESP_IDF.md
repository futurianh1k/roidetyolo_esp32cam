# ESP-IDF 설치 가이드

**작성일:** 2025-12-10

---

## 문제 상황

빌드 스크립트 실행 시 다음 오류가 발생하는 경우:

```
ERROR: ESP-IDF Python virtual environment not found
```

이는 ESP-IDF 설치가 완전하지 않거나 Python 가상 환경이 설정되지 않았음을 의미합니다.

---

## 해결 방법

### 방법 1: ESP-IDF 설치 스크립트 실행 (권장)

**1. ESP-IDF 프레임워크 디렉토리로 이동:**

```powershell
cd E:\esp32\Espressif\frameworks\esp-idf-v5.5.1
```

**2. 설치 스크립트 실행:**

```powershell
.\install.bat esp32,esp32s3
```

또는 모든 칩 지원:

```powershell
.\install.bat
```

**3. 설치 완료 후 빌드 스크립트 실행:**

```powershell
cd D:\cursorworks\roidetyolo_esp32cam\firmware_idf
.\build.ps1
```

---

### 방법 2: ESP-IDF 설치 프로그램 사용

**1. ESP-IDF 설치 프로그램 다운로드:**

- https://dl.espressif.com/dl/esp-idf/ 에서 최신 설치 프로그램 다운로드

**2. 설치 프로그램 실행:**

- 설치 경로: `E:\esp32\Espressif` 선택
- ESP-IDF 버전: v5.5.1 선택
- 칩 지원: ESP32, ESP32-S3 선택

**3. 설치 완료 후 빌드 스크립트 실행**

---

### 방법 3: 수동 설치

**1. Python 가상 환경 확인:**

```powershell
# Python 가상 환경 경로 확인
Test-Path "E:\esp32\Espressif\python_env\idf5.5_py3.13_env\Scripts\python.exe"
```

**2. 가상 환경이 없으면 설치 스크립트 실행:**

```powershell
cd E:\esp32\Espressif\frameworks\esp-idf-v5.5.1
.\install.bat esp32,esp32s3
```

---

## 설치 확인

**1. Python 가상 환경 확인:**

```powershell
Test-Path "E:\esp32\Espressif\python_env\idf5.5_py3.13_env\Scripts\python.exe"
```

**2. ESP-IDF 환경 설정:**

```powershell
cd E:\esp32\Espressif\frameworks\esp-idf-v5.5.1
.\export.ps1
```

**3. idf.py 확인:**

```powershell
idf.py --version
```

성공하면 ESP-IDF 버전이 출력됩니다.

---

## 문제 해결

### 문제 1: Python 버전 불일치

**증상:**

```
Python version mismatch
```

**해결:**

- ESP-IDF v5.5.1은 Python 3.8 이상 필요
- Python 3.13이 설치되어 있지만 가상 환경이 설정되지 않았을 수 있음
- 설치 스크립트를 다시 실행

### 문제 2: 가상 환경 경로 오류

**증상:**

```
Python virtual environment not found
```

**해결:**

1. `E:\esp32\Espressif\python_env\` 디렉토리 확인
2. 가상 환경이 없으면 설치 스크립트 실행
3. 경로가 다르면 `export.ps1` 수정 필요

### 문제 3: 네트워크 오류

**증상:**

```
Failed to download...
```

**해결:**

- 방화벽 설정 확인
- 프록시 설정 확인
- 인터넷 연결 확인

---

## 참고 자료

- **ESP-IDF 설치 가이드:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/
- **Windows 설치:** https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/windows-setup.html

---

**작성자:** AI Assistant  
**마지막 업데이트:** 2025-12-10
