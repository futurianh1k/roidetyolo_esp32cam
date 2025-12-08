# Core S3 Management System

M5Stack Core S3 장비를 원격으로 관리하고 제어하는 완전한 IoT 시스템입니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 프로젝트 개요

이 시스템은 M5Stack Core S3 장비의 카메라, 마이크, 스피커, 디스플레이를 원격으로 제어하고 실시간으로 모니터링할 수 있는 완전한 IoT 관리 솔루션입니다.

### 주요 기능

- 🎥 **카메라 스트리밍**: RTSP를 통한 실시간 영상 스트리밍
- 🎤 **오디오 제어**: 마이크 녹음 및 스피커 원격 재생
- 📱 **디스플레이 제어**: 텍스트 및 이모티콘 표시
- 📡 **실시간 통신**: MQTT와 WebSocket을 통한 양방향 통신
- 📊 **상태 모니터링**: 배터리, 메모리, 온도 등 실시간 모니터링
- 🔐 **보안**: JWT 인증, 역할 기반 접근 제어, 감사 로그
- 🎨 **웹 인터페이스**: Next.js 기반 현대적인 UI/UX

## 🏗️ 시스템 아키텍처

```
┌──────────────┐         MQTT/WebSocket        ┌──────────────┐
│              │◄────────────────────────────►│              │
│   Core S3    │         RTSP Stream           │   Backend    │
│   Device     │──────────────────────────────►│   (FastAPI)  │
│              │                                │              │
│  - Camera    │                                │  - REST API  │
│  - Mic       │                                │  - MQTT      │
│  - Speaker   │                                │  - WebSocket │
│  - Display   │                                │              │
└──────────────┘                                └──────┬───────┘
                                                       │
                                                       │ HTTP/WS
                                                       │
                                                ┌──────▼───────┐
                                                │              │
                                                │  Frontend    │
                                                │  (Next.js)   │
                                                │              │
                                                └──────┬───────┘
                                                       │
                                                ┌──────▼───────┐
                                                │    MySQL     │
                                                └──────────────┘
```

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.9+
- Node.js 18+
- MySQL 5.7+
- PlatformIO
- M5Stack Core S3 장비

### 설치 (10분 완료)

**빠른 시작 가이드:** [QUICKSTART.md](QUICKSTART.md)

```bash
# 1. 백엔드 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. 프론트엔드 설정
cd ../frontend
npm install
npm run dev

# 3. 펌웨어 업로드
cd ../firmware
platformio run --target upload
```

**초기 관리자 계정:**
- 사용자명: `admin`
- 비밀번호: `Admin123!`

**접속:**
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000/docs

## 📁 프로젝트 구조

```
roidetyolo_esp32cam/
├── backend/                 ✅ FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 엔드포인트
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── services/       # MQTT, WebSocket, Audio
│   │   ├── security/       # 인증/보안
│   │   └── ...
│   ├── init_db.py          # DB 초기화
│   ├── test_api.py         # API 테스트
│   └── README.md
│
├── frontend/               ✅ Next.js 프론트엔드
│   ├── src/
│   │   ├── app/           # 페이지 (App Router)
│   │   ├── components/    # React 컴포넌트
│   │   ├── lib/           # API, WebSocket
│   │   └── store/         # 상태 관리
│   └── README.md
│
├── firmware/              ✅ Core S3 펌웨어 (Arduino)
│   ├── include/          # 헤더 파일
│   ├── src/              # 소스 코드
│   ├── platformio.ini    # PlatformIO 설정
│   └── README.md
│
├── README.md             # 이 파일
├── QUICKSTART.md         # 빠른 시작 가이드
└── .gitignore
```

## 🎯 주요 기능

### 백엔드 (FastAPI)
- ✅ JWT 기반 인증/권한 시스템
- ✅ 사용자 및 장비 관리 API
- ✅ MQTT 양방향 통신
- ✅ WebSocket 실시간 업데이트
- ✅ 장비 제어 API (카메라, 마이크, 스피커, 디스플레이)
- ✅ 오디오 파일 관리
- ✅ 감사 로그 및 보안

### 프론트엔드 (Next.js)
- ✅ 로그인/인증 UI
- ✅ 대시보드 (장비 목록, 통계)
- ✅ 장비 상세 페이지
- ✅ 실시간 상태 모니터링
- ✅ 장비 원격 제어 UI
- ✅ 반응형 디자인

### 펌웨어 (Arduino/ESP32)
- ✅ WiFi 연결
- ✅ MQTT 통신
- ✅ 카메라 제어 (OV2640)
- ✅ 오디오 입출력 (I2S)
- ✅ LCD 디스플레이 제어
- ✅ 상태 보고
- ✅ 버튼 제어

## 📊 API 엔드포인트

### 인증
- `POST /auth/register` - 사용자 등록
- `POST /auth/login` - 로그인
- `POST /auth/refresh` - 토큰 갱신
- `POST /auth/logout` - 로그아웃
- `GET /auth/me` - 현재 사용자 정보

### 장비 관리
- `GET /devices/` - 장비 목록
- `POST /devices/` - 장비 등록
- `PUT /devices/{id}` - 장비 수정
- `GET /devices/{id}/status/latest` - 최신 상태

### 장비 제어
- `POST /control/devices/{id}/camera` - 카메라 제어
- `POST /control/devices/{id}/microphone` - 마이크 제어
- `POST /control/devices/{id}/speaker` - 스피커 제어
- `POST /control/devices/{id}/display` - 디스플레이 제어

전체 API 문서: [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)

## 🔐 보안

이 시스템은 **한국 개인정보보호법 및 ISMS-P** 수준의 보안 가이드라인을 준수합니다:

- ✅ BCrypt 비밀번호 해싱 (rounds=12)
- ✅ JWT Access Token (15분) + Refresh Token (7일)
- ✅ 역할 기반 접근 제어 (ADMIN, OPERATOR, VIEWER)
- ✅ 모든 관리자 액션 감사 로그 기록
- ✅ 민감정보 로그 필터링
- ✅ 입력 검증 및 출력 인코딩
- ✅ SQL Injection 방지 (ORM 사용)
- ✅ 파일 업로드 검증 (화이트리스트, 크기 제한)

## 📸 스크린샷

### 로그인 페이지
![Login](docs/screenshots/login.png)

### 대시보드
![Dashboard](docs/screenshots/dashboard.png)

### 장비 제어
![Device Control](docs/screenshots/device-control.png)

## 🛠️ 개발 가이드

### 백엔드 개발
상세 가이드: [backend/README.md](backend/README.md)
- FastAPI 구조
- 새 API 추가
- 보안 가이드라인
- 테스트 방법

### 프론트엔드 개발
상세 가이드: [frontend/README.md](frontend/README.md)
- Next.js App Router
- 컴포넌트 개발
- API 연동
- 스타일링

### 펌웨어 개발
상세 가이드: [firmware/README.md](firmware/README.md)
- PlatformIO 사용법
- 모듈 구조
- MQTT 통신
- 디버깅

## 🧪 테스트

### 백엔드 테스트
```bash
cd backend
python test_api.py
```

### 프론트엔드 테스트
```bash
cd frontend
npm run test
```

### 펌웨어 테스트
```bash
cd firmware
platformio test
```

## 📝 문서

- [빠른 시작 가이드](QUICKSTART.md)
- [백엔드 README](backend/README.md)
- [백엔드 설치 가이드](backend/SETUP_GUIDE.md)
- [API 문서](backend/API_DOCUMENTATION.md)
- [펌웨어 README](firmware/README.md)
- [프론트엔드 README](frontend/README.md)

## 🚧 로드맵

### 완료된 기능
- [x] 백엔드 인증/권한 시스템
- [x] 사용자 및 장비 관리 API
- [x] MQTT 통신 서비스
- [x] WebSocket 실시간 통신
- [x] 장비 제어 API
- [x] 오디오 파일 관리
- [x] Core S3 펌웨어 기본 구현
- [x] 프론트엔드 UI/UX

### 진행 중인 기능
- [ ] RTSP 스트리밍 완성
- [ ] 백엔드/프론트엔드 테스트 코드

### 향후 계획
- [ ] OTA 펌웨어 업데이트
- [ ] 녹화 및 저장 기능
- [ ] 모션 감지
- [ ] 알림 시스템
- [ ] 모바일 앱

## 🤝 기여

기여를 환영합니다! Pull Request를 보내주세요.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 참고 자료

- [M5Stack Core S3](https://docs.m5stack.com/en/core/CoreS3)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [PlatformIO](https://platformio.org/)
- [MQTT](https://mqtt.org/)
- [ESP32 Camera](https://github.com/espressif/esp32-camera)

## 💬 지원

문제가 발생하면:
1. [빠른 시작 가이드](QUICKSTART.md) 참조
2. 각 모듈의 README 확인
3. [API 문서](backend/API_DOCUMENTATION.md) 확인
4. Issue 등록

## 👨‍💻 개발자

이 프로젝트는 한국 개인정보보호법 및 ISMS-P 보안 가이드라인을 준수하여 개발되었습니다.

---

**Made with ❤️ for IoT**
