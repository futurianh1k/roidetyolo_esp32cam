# 오디오 재생 실패 문제 해결 가이드

**문제:** ESP32 장비에서 MP3 파일 재생 시 "connection refused" 오류 발생

---

## 🔍 문제 원인

ESP32 장비가 `localhost:8000`에 연결을 시도하여 실패합니다.

```
[113301][E][WiFiClient.cpp:275] connect(): socket error on fd 49, errno: 104, "Connection reset by peer"
[113311][D][HTTPClient.cpp:1163] connect(): failed connect to localhost:8000
```

**이유:**
- ESP32 장비에서 `localhost`는 장비 자신을 의미합니다
- 백엔드 서버의 실제 IP 주소를 사용해야 합니다

---

## ✅ 해결 방법

### 방법 1: .env 파일에 BACKEND_HOST 설정 (권장)

**1. 백엔드 서버의 IP 주소 확인**

Windows PowerShell:
```powershell
ipconfig
# IPv4 주소 확인 (예: 192.168.1.100 또는 10.10.11.1)
```

Linux/Mac:
```bash
ifconfig
# 또는
ip addr show
```

**2. .env 파일 수정**

`backend/.env` 파일을 열고 다음 설정 추가/수정:

```env
# Backend Server (장비가 접근할 수 있는 백엔드 주소)
# ESP32 장비와 같은 네트워크의 IP 주소 사용
BACKEND_HOST=192.168.1.100  # 실제 백엔드 서버 IP로 변경
BACKEND_PORT=8000
```

**예시:**
- 백엔드 서버 IP: `192.168.1.100`
- ESP32 장비 IP: `10.10.11.18`
- 같은 네트워크라면: `BACKEND_HOST=192.168.1.100`
- 다른 서브넷이라면: 백엔드 서버의 실제 IP 사용

**3. 백엔드 서버 재시작**

```bash
cd backend
# 서버 재시작
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### 방법 2: 자동 감지 기능 사용 (개발 중)

코드가 자동으로 Request의 Host 헤더를 사용하여 백엔드 IP를 감지합니다.

**동작 방식:**
1. `.env`의 `BACKEND_HOST`가 `localhost`인 경우
2. Request의 Host 헤더에서 호스트명 추출
3. 장비 IP와 같은 서브넷 기반으로 추론

**주의:** 이 방법은 완벽하지 않을 수 있으므로, 방법 1을 권장합니다.

---

## 🧪 테스트

**1. 백엔드 서버에서 오디오 파일 URL 확인**

로그에서 다음 메시지 확인:
```
오디오 파일 URL 생성: http://192.168.1.100:8000/audio/xxx.mp3
```

**2. ESP32 장비에서 접근 가능한지 확인**

브라우저나 curl로 테스트:
```bash
# 백엔드 서버에서
curl http://192.168.1.100:8000/audio/xxx.mp3

# ESP32와 같은 네트워크의 다른 장비에서
curl http://192.168.1.100:8000/audio/xxx.mp3
```

**3. ESP32 장비에서 재생 테스트**

프론트엔드에서 MP3 파일 업로드 후 재생 버튼 클릭

---

## 🔧 추가 확인 사항

### 1. 방화벽 설정

백엔드 서버의 방화벽에서 포트 8000이 열려있는지 확인:

**Windows:**
```powershell
# 방화벽 규칙 확인
netsh advfirewall firewall show rule name="Python" dir=in
```

**Linux:**
```bash
# UFW 사용 시
sudo ufw allow 8000/tcp

# 또는 iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### 2. 네트워크 연결 확인

ESP32 장비와 백엔드 서버가 같은 네트워크에 있는지 확인:

```bash
# 백엔드 서버에서 ESP32 장비 ping 테스트
ping 10.10.11.18

# ESP32 장비에서 백엔드 서버 ping 테스트 (펌웨어에 ping 기능이 있다면)
```

### 3. 백엔드 서버 바인딩 확인

백엔드 서버가 `0.0.0.0`에 바인딩되어 있는지 확인:

```python
# backend/app/main.py 또는 실행 명령
uvicorn.run(app, host="0.0.0.0", port=8000)  # ✅ 모든 인터페이스에서 접근 가능
# uvicorn.run(app, host="127.0.0.1", port=8000)  # ❌ localhost만 접근 가능
```

---

## 📝 설정 예시

### 시나리오 1: 같은 네트워크

```
백엔드 서버: 192.168.1.100
ESP32 장비: 192.168.1.18
```

`.env` 설정:
```env
BACKEND_HOST=192.168.1.100
BACKEND_PORT=8000
```

### 시나리오 2: 다른 서브넷 (라우터/게이트웨이 필요)

```
백엔드 서버: 192.168.1.100
ESP32 장비: 10.10.11.18
```

`.env` 설정:
```env
BACKEND_HOST=192.168.1.100  # 라우터를 통해 접근 가능해야 함
BACKEND_PORT=8000
```

### 시나리오 3: 개발 환경 (localhost)

개발 중에는 프론트엔드만 사용하는 경우:
```env
BACKEND_HOST=localhost  # 프론트엔드는 localhost 사용 가능
BACKEND_PORT=8000
```

**주의:** ESP32 장비를 사용하는 경우 반드시 실제 IP 주소를 설정해야 합니다.

---

## 🐛 문제 해결 체크리스트

- [ ] `.env` 파일에 `BACKEND_HOST`가 실제 IP 주소로 설정되어 있는가?
- [ ] 백엔드 서버가 `0.0.0.0:8000`에 바인딩되어 있는가?
- [ ] 방화벽에서 포트 8000이 열려있는가?
- [ ] ESP32 장비와 백엔드 서버가 같은 네트워크에 있는가?
- [ ] 백엔드 서버를 재시작했는가?
- [ ] 생성된 오디오 URL이 `localhost`가 아닌 실제 IP를 사용하는가?

---

## 📚 관련 문서

- `backend/env.example` - 환경 변수 예시
- `backend/app/api/control.py` - 스피커 제어 API
- `backend/app/config.py` - 설정 파일

---

**작성일:** 2025-12-10  
**관련 이슈:** ESP32 오디오 재생 실패

