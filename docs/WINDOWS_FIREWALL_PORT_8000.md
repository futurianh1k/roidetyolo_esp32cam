# Windows 방화벽 포트 8000 허용 가이드

## 방법 1: PowerShell (관리자 권한) - 권장

### 1단계: PowerShell을 관리자 권한으로 실행

1. **시작 메뉴**에서 "PowerShell" 검색
2. **Windows PowerShell**을 **우클릭**
3. **관리자 권한으로 실행** 선택

### 2단계: 인바운드 규칙 추가

```powershell
# 포트 8000 인바운드 규칙 추가 (TCP)
New-NetFirewallRule -DisplayName "Backend Server Port 8000" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any
```

### 3단계: 규칙 확인

```powershell
# 방화벽 규칙 확인
Get-NetFirewallRule -DisplayName "Backend Server Port 8000"
```

### 4단계: 규칙 삭제 (필요시)

```powershell
# 규칙 삭제
Remove-NetFirewallRule -DisplayName "Backend Server Port 8000"
```

---

## 방법 2: GUI (Windows 방화벽 고급 보안)

### 1단계: Windows 방화벽 고급 보안 열기

1. **시작 메뉴**에서 "방화벽" 검색
2. **Windows Defender 방화벽 고급 보안** 선택
3. 또는 `wf.msc` 실행

### 2단계: 인바운드 규칙 추가

1. 왼쪽 메뉴에서 **인바운드 규칙** 클릭
2. 오른쪽 **새 규칙...** 클릭
3. **규칙 종류 선택**:
   - **포트** 선택 → **다음**
4. **프로토콜 및 포트**:
   - **TCP** 선택
   - **특정 로컬 포트** 선택
   - 포트 번호: **8000** 입력 → **다음**
5. **작업**:
   - **연결 허용** 선택 → **다음**
6. **프로필**:
   - **도메인**, **개인**, **공용** 모두 체크 → **다음**
7. **이름**:
   - 이름: **Backend Server Port 8000**
   - 설명: **ESP32 장비가 백엔드 서버에 접근하기 위한 포트** → **마침**

---

## 방법 3: 명령 프롬프트 (CMD) - 관리자 권한

```cmd
netsh advfirewall firewall add rule name="Backend Server Port 8000" dir=in action=allow protocol=TCP localport=8000
```

**규칙 확인:**
```cmd
netsh advfirewall firewall show rule name="Backend Server Port 8000"
```

**규칙 삭제:**
```cmd
netsh advfirewall firewall delete rule name="Backend Server Port 8000"
```

---

## 백엔드 서버 바인딩 확인

### 방법 1: 코드 확인

`backend/app/main.py` 또는 서버 시작 스크립트에서:

```python
# 올바른 설정 (0.0.0.0으로 바인딩)
uvicorn.run(app, host="0.0.0.0", port=8000)

# 또는
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

**주의:** `host="127.0.0.1"` 또는 `host="localhost"`는 로컬에서만 접근 가능합니다.

### 방법 2: 실행 중인 서버 확인

**PowerShell에서:**
```powershell
# 포트 8000을 사용하는 프로세스 확인
netstat -ano | findstr :8000
```

**출력 예시:**
```
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       12345
TCP    [::]:8000              [::]:0                 LISTENING       12345
```

- `0.0.0.0:8000` 또는 `[::]:8000`이 보이면 올바르게 바인딩됨
- `127.0.0.1:8000`만 보이면 로컬에서만 접근 가능

### 방법 3: 서버 시작 명령 확인

백엔드 서버를 시작할 때:

```bash
# 올바른 명령 (모든 네트워크 인터페이스에서 접근 가능)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 잘못된 명령 (로컬에서만 접근 가능)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
python -m uvicorn app.main:app --reload --host localhost --port 8000
```

---

## 테스트

### 1. 로컬에서 테스트

```powershell
# PowerShell에서
Test-NetConnection -ComputerName localhost -Port 8000

# 또는 브라우저에서
http://localhost:8000/docs
```

### 2. 다른 장치에서 테스트

ESP32와 같은 네트워크의 다른 컴퓨터에서:

```powershell
# 백엔드 서버 IP로 테스트 (예: 10.10.11.18)
Test-NetConnection -ComputerName 10.10.11.18 -Port 8000

# 또는 브라우저에서
http://10.10.11.18:8000/docs
```

### 3. ESP32에서 테스트

ESP32 로그에서 다음 메시지 확인:

```
✅ HTTP GET 성공
✅ Audio playback started
```

---

## 문제 해결

### 문제 1: 방화벽 규칙 추가 후에도 연결 안 됨

**해결:**
1. Windows 방화벽이 활성화되어 있는지 확인
2. 백엔드 서버가 실제로 실행 중인지 확인
3. 다른 방화벽 소프트웨어(예: 바이러스 백신) 확인

### 문제 2: 포트가 이미 사용 중

**해결:**
```powershell
# 포트 8000을 사용하는 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료 (PID 확인 후)
taskkill /PID <PID번호> /F
```

### 문제 3: 서버는 실행 중이지만 ESP32에서 접근 불가

**확인 사항:**
1. 백엔드 서버가 `0.0.0.0`으로 바인딩되어 있는지 확인
2. ESP32와 백엔드 서버가 같은 네트워크에 있는지 확인
3. 백엔드 서버의 IP 주소가 올바른지 확인 (`ipconfig`로 확인)

---

## 빠른 확인 스크립트

PowerShell 스크립트로 한 번에 확인:

```powershell
# 방화벽 규칙 확인
Write-Host "=== 방화벽 규칙 확인 ===" -ForegroundColor Yellow
Get-NetFirewallRule -DisplayName "Backend Server Port 8000" | Format-Table

# 포트 8000 사용 확인
Write-Host "`n=== 포트 8000 사용 확인 ===" -ForegroundColor Yellow
netstat -ano | findstr :8000

# 로컬 연결 테스트
Write-Host "`n=== 로컬 연결 테스트 ===" -ForegroundColor Yellow
Test-NetConnection -ComputerName localhost -Port 8000
```

---

**작성일:** 2025-12-10  
**적용 환경:** Windows 10/11


