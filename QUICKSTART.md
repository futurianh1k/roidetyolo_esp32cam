# Core S3 Management System - 빠른 시작 가이드

이 문서는 전체 시스템을 빠르게 설치하고 실행하는 방법을 안내합니다.

## 📋 시스템 구성

```
┌──────────────┐
│   Core S3    │ ← WiFi/MQTT
│   Device      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Backend    │ ← HTTP/WebSocket
│   (FastAPI)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Frontend   │ ← 웹 브라우저
│   (Next.js)  │
└──────────────┘
```

## 🚀 1단계: 백엔드 설정 (5분)

### 1.1 의존성 설치

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 1.2 MySQL 데이터베이스 설정

**Windows (PowerShell):**

```powershell
# MySQL 접속
mysql -u root -p

# MySQL 프롬프트에서 실행:
# CREATE DATABASE cores3_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# exit;

# 또는 SQL 파일 실행
Get-Content setup.sql | mysql -u root -p
```

**Linux/Mac:**

```bash
# MySQL 접속
mysql -u root -p

# 데이터베이스 생성
CREATE DATABASE cores3_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;

# 또는 SQL 파일 실행
mysql -u root -p < setup.sql
```

### 1.3 환경 변수 설정

`.env` 파일 생성:

```env
# 필수 설정
SECRET_KEY=change-this-to-a-random-32-character-string
DB_PASSWORD=your-mysql-password
DB_NAME=cores3_management

# 선택 설정
DEBUG=True
MQTT_BROKER_HOST=localhost
```

### 1.4 데이터베이스 초기화

```bash
python init_db.py
```

출력:

```
초기 관리자 계정이 생성되었습니다:
  사용자명: admin
  비밀번호: Admin123!
  이메일: admin@example.com
```

### 1.5 MQTT 브로커 설치 (선택)

**Ubuntu:**

```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

**Windows:**

1. [Mosquitto 다운로드](https://mosquitto.org/download/)
2. 설치 후 실행

### 1.6 백엔드 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

확인: http://localhost:8000/docs

---

## 🎨 2단계: 프론트엔드 설정 (3분)

### 2.1 의존성 설치

```bash
cd frontend
npm install
```

### 2.2 환경 변수 설정

`.env.local` 파일 생성:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 2.3 프론트엔드 서버 실행

```bash
npm run dev
```

확인: http://localhost:3000

---

## 📱 3단계: Core S3 장비 설정 (10분)

### 3.1 PlatformIO 설치

```bash
pip install platformio
```

### 3.2 펌웨어 설정

`firmware/include/config.h` 파일 수정:

```cpp
// WiFi 설정
#define WIFI_SSID "YOUR_WIFI_NAME"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// MQTT 설정 (백엔드 서버 IP)
#define MQTT_BROKER "192.168.1.100"  // 백엔드 서버의 실제 IP

// 장비 설정
#define DEVICE_ID "core_s3_001"
#define DEVICE_NAME "Office Camera"
#define DEVICE_LOCATION "1F Office"
```

### 3.3 펌웨어 업로드

```bash
cd firmware

# Core S3를 USB로 연결

# 빌드 및 업로드
platformio run --target upload

# 시리얼 모니터 (선택)
platformio device monitor
```

### 3.4 장비 동작 확인

시리얼 모니터 출력:

```
=================================
Core S3 Management System
=================================
WiFi connected!
IP: 192.168.1.150
Camera OK
Audio OK
MQTT Connected!
System initialized!
=================================
```

---

## ✅ 4단계: 시스템 테스트 (5분)

### 4.1 백엔드 테스트

```bash
cd backend
python test_api.py
```

출력:

```
[1] 헬스 체크 테스트... ✅ 성공
[2] 사용자 등록 테스트... ✅ 성공
[3] 로그인 테스트... ✅ 성공
[4] 현재 사용자 정보 조회... ✅ 성공
테스트 결과: 4/4 성공
```

### 4.2 프론트엔드 접속

1. 브라우저에서 http://localhost:3000 접속
2. 로그인:
   - 사용자명: `admin`
   - 비밀번호: `Admin123!`
3. 대시보드 확인

### 4.3 장비 등록

**방법 1: API를 통한 등록**

```bash
# 로그인하여 토큰 받기
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'

# 장비 등록 (토큰 사용)
curl -X POST http://localhost:8000/devices/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "core_s3_001",
    "device_name": "Office Camera",
    "device_type": "CoreS3",
    "ip_address": "192.168.1.150",
    "location": "1F Office"
  }'
```

**방법 2: 프론트엔드에서 확인**

대시보드에서 장비가 자동으로 등록되어 표시됩니다.

### 4.4 장비 제어 테스트

프론트엔드에서:

1. 장비 카드 클릭
2. "카메라 시작" 버튼 클릭
3. Core S3 화면에서 "Camera ON" 메시지 확인
4. 백엔드 로그에서 MQTT 메시지 확인

---

## 📊 시스템 상태 확인

### 백엔드 상태

```bash
curl http://localhost:8000/health
```

출력:

```json
{
  "status": "healthy",
  "environment": "development",
  "mqtt_connected": true
}
```

### 프론트엔드 상태

브라우저 개발자 도구 (F12):

- Console: 에러 메시지 확인
- Network: API 요청/응답 확인

### 장비 상태

시리얼 모니터 출력:

```
WiFi connected!
MQTT connected!
Status reported successfully
```

---

## 🎯 전체 시스템 흐름

### 1. 장비 → 백엔드 (상태 보고)

```
Core S3 → MQTT → Backend
10초마다 상태 정보 전송
(배터리, 메모리, 온도 등)
```

### 2. 프론트엔드 → 백엔드 (제어 명령)

```
Frontend → HTTP API → Backend → MQTT → Core S3
카메라/마이크 제어 명령 전송
```

### 3. 백엔드 → 프론트엔드 (실시간 업데이트)

```
Backend → WebSocket → Frontend
장비 상태 실시간 업데이트
```

---

## 🐛 문제 해결

### Backend

**MySQL 연결 실패:**

```bash
# MySQL 상태 확인
sudo systemctl status mysql

# MySQL 재시작
sudo systemctl restart mysql
```

**MQTT 연결 실패:**

```bash
# Mosquitto 상태 확인
sudo systemctl status mosquitto

# 방화벽 포트 확인
sudo ufw allow 1883
```

### Frontend

**API 연결 실패:**

```bash
# 백엔드 실행 여부 확인
curl http://localhost:8000/health

# .env.local 파일 확인
cat .env.local
```

**npm install 오류:**

```bash
# npm 캐시 삭제
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Firmware

**Upload 실패:**

```bash
# USB 연결 확인
platformio device list

# 드라이버 설치 (Windows)
# CH340 또는 CP210x 드라이버 설치
```

**WiFi 연결 실패:**

- SSID와 비밀번호 확인
- 2.4GHz WiFi 사용 확인 (5GHz 미지원)
- 라우터 재시작

---

## 📝 다음 단계

### 1. 보안 강화

- [ ] SECRET_KEY 변경
- [ ] admin 비밀번호 변경
- [ ] HTTPS 설정 (Nginx)
- [ ] MQTT TLS 설정

### 2. 프로덕션 배포

- [ ] 환경 변수 설정
- [ ] 데이터베이스 백업
- [ ] 로그 모니터링
- [ ] 방화벽 설정

### 3. 기능 확장

- [ ] RTSP 스트리밍 완성
- [ ] 오디오 파일 업로드
- [ ] 녹화 기능
- [ ] 알림 시스템

---

## 📚 추가 문서

- [백엔드 README](backend/README.md)
- [백엔드 설치 가이드](backend/SETUP_GUIDE.md)
- [API 문서](backend/API_DOCUMENTATION.md)
- [펌웨어 README](firmware/README.md)
- [프론트엔드 README](frontend/README.md)

---

## 💬 지원

문제가 발생하면:

1. 각 모듈의 README 참조
2. 로그 파일 확인
3. 시리얼 모니터 확인
4. API 문서 참조

---

## 🎉 축하합니다!

모든 설정이 완료되었습니다! 이제 Core S3 장비를 원격으로 관리할 수 있습니다.

**다음을 확인해보세요:**

- ✅ 대시보드에서 장비 목록 확인
- ✅ 실시간 상태 모니터링
- ✅ 카메라/마이크 원격 제어
- ✅ 디스플레이 텍스트 표시
