# ESP-IDF 빌드 빠른 시작 가이드

## 1단계: 환경 확인

```powershell
cd firmware_idf
.\check_build_env.ps1
```

모든 항목이 ✅이면 다음 단계로 진행합니다.

## 2단계: 빌드

### 방법 1: 빌드 스크립트 사용 (권장)

```powershell
.\build.ps1
```

### 방법 2: 수동 빌드

```powershell
# ESP-IDF 환경 설정 (새 터미널마다 필요)
C:\Espressif\frameworks\esp-idf-v5.4\export.ps1

# 타겟 설정
idf.py set-target esp32s3

# 빌드
idf.py build
```

## 3단계: 플래시 및 모니터링

```powershell
# 플래시 + 모니터링 (한 번에)
.\build.ps1 -Flash -Monitor -Port COM3

# 또는 수동으로
idf.py -p COM3 flash monitor
```

## 빌드 옵션

```powershell
# 클린 빌드
.\build.ps1 -Clean

# 플래시만
.\build.ps1 -Flash -Port COM3

# 모니터링만
.\build.ps1 -Monitor -Port COM3
```

## 문제 해결

빌드 오류 발생 시:

1. **환경 확인:**
   ```powershell
   .\check_build_env.ps1
   ```

2. **상세 빌드 로그:**
   ```powershell
   idf.py build -v
   ```

3. **클린 빌드:**
   ```powershell
   idf.py fullclean
   idf.py build
   ```

## 참고

- 상세 가이드: `BUILD_GUIDE.md`
- ESP-IDF 문서: https://docs.espressif.com/projects/esp-idf/

