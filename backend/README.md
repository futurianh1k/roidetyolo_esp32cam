# Core S3 Management System - Backend

Core S3 장비 관리 시스템의 백엔드 API 서버입니다.

## 기술 스택

- **Framework**: FastAPI 0.104.1
- **Database**: MySQL (SQLAlchemy ORM)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: BCrypt (passlib)
- **Communication**: MQTT (paho-mqtt), WebSocket
- **Media**: RTSP, Audio Processing

## 주요 기능

### 1. 인증 및 사용자 관리
- ✅ JWT 기반 인증 (Access Token + Refresh Token)
- ✅ BCrypt 비밀번호 해싱
- ✅ 역할 기반 접근 제어 (ADMIN, OPERATOR, VIEWER)
- ✅ 사용자 CRUD 관리

### 2. 장비 관리
- ✅ 장비 등록/수정/삭제
- ✅ 장비 상태 모니터링 (배터리, 메모리, 온도 등)
- ✅ 실시간 온라인/오프라인 상태 추적

### 3. 장비 제어
- ✅ 카메라 제어 (시작/일시정지/종료)
- ✅ 마이크 제어 (시작/일시정지/종료)
- ✅ 스피커 제어 (재생/정지)
- ✅ 디스플레이 제어 (텍스트/이모티콘 표시)

### 4. 실시간 통신
- ✅ MQTT 양방향 통신 (장비 ↔ 서버)
- ✅ WebSocket 실시간 상태 업데이트
- ✅ 장비별 구독 시스템

### 5. 오디오 파일 관리
- ✅ 오디오 파일 업로드 (mp3, wav, ogg)
- ✅ 파일 형식 및 크기 검증
- ✅ 안전한 파일 저장 (경로 공격 방지)

### 6. 보안
- ✅ ISMS-P 수준 보안 가이드라인 준수
- ✅ 모든 관리자 액션 감사 로그 기록
- ✅ 민감정보 로그 필터링
- ✅ 입력 검증 및 출력 인코딩

## API 엔드포인트

### 인증 (`/auth`)
- `POST /auth/register` - 사용자 등록
- `POST /auth/login` - 로그인
- `POST /auth/refresh` - 토큰 갱신
- `POST /auth/logout` - 로그아웃
- `GET /auth/me` - 현재 사용자 정보

### 사용자 관리 (`/users`)
- `GET /users/` - 사용자 목록 (ADMIN)
- `GET /users/{user_id}` - 사용자 상세 (ADMIN)
- `POST /users/` - 사용자 생성 (ADMIN)
- `PUT /users/{user_id}` - 사용자 수정 (ADMIN)
- `DELETE /users/{user_id}` - 사용자 삭제 (ADMIN)
- `PUT /users/me/password` - 비밀번호 변경

### 장비 관리 (`/devices`)
- `GET /devices/` - 장비 목록
- `GET /devices/{device_id}` - 장비 상세
- `POST /devices/` - 장비 등록 (OPERATOR)
- `PUT /devices/{device_id}` - 장비 수정 (OPERATOR)
- `DELETE /devices/{device_id}` - 장비 삭제 (ADMIN)
- `POST /devices/{device_id}/status` - 상태 기록
- `GET /devices/{device_id}/status` - 상태 이력
- `GET /devices/{device_id}/status/latest` - 최신 상태

### 장비 제어 (`/control`)
- `POST /control/devices/{device_id}/camera` - 카메라 제어
- `POST /control/devices/{device_id}/microphone` - 마이크 제어
- `POST /control/devices/{device_id}/speaker` - 스피커 제어
- `POST /control/devices/{device_id}/display` - 디스플레이 제어

### 오디오 파일 (`/audio`)
- `POST /audio/upload` - 오디오 파일 업로드
- `GET /audio/list` - 파일 목록
- `GET /audio/{filename}` - 파일 다운로드
- `DELETE /audio/{filename}` - 파일 삭제

### WebSocket (`/ws`)
- `WebSocket /ws?token=<access_token>` - 실시간 연결

## 설치 및 실행

### 1. 의존성 설치

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 `.env`로 복사하고 수정:

```env
# Security (반드시 변경!)
SECRET_KEY=your-secret-key-min-32-chars

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=cores3_management

# MQTT Broker
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883

# CORS
CORS_ORIGINS=http://localhost:3000
```

### 3. 데이터베이스 생성

```bash
# MySQL 접속
mysql -u root -p

# 데이터베이스 생성
CREATE DATABASE cores3_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 또는 SQL 스크립트 실행
mysql -u root -p < setup.sql

# Python으로 초기화 (초기 관리자 계정 생성)
python init_db.py
```

**초기 관리자 계정:**
- 사용자명: `admin`
- 비밀번호: `Admin123!`
- ⚠️ 로그인 후 반드시 변경하세요!

### 4. MQTT 브로커 설치 (선택사항)

```bash
# Mosquitto 설치 (Ubuntu)
sudo apt install mosquitto mosquitto-clients

# 서비스 시작
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Windows - Mosquitto 다운로드
# https://mosquitto.org/download/
```

### 5. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

서버 접속: http://localhost:8000

API 문서: http://localhost:8000/docs

### 6. 테스트

```bash
python test_api.py
```

## 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 앱
│   ├── config.py              # 설정
│   ├── database.py            # DB 연결
│   ├── models/                # SQLAlchemy 모델
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   ├── device.py
│   │   ├── device_status.py
│   │   └── audit_log.py
│   ├── schemas/               # Pydantic 스키마
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── device.py
│   │   └── control.py
│   ├── api/                   # API 라우터
│   │   ├── auth.py           # 인증
│   │   ├── users.py          # 사용자 관리
│   │   ├── devices.py        # 장비 관리
│   │   ├── control.py        # 장비 제어
│   │   ├── audio.py          # 오디오 파일
│   │   └── websocket.py      # WebSocket
│   ├── services/              # 비즈니스 로직
│   │   ├── mqtt_service.py   # MQTT 통신
│   │   ├── websocket_service.py
│   │   └── audio_service.py
│   ├── security/              # 보안 모듈
│   │   ├── password.py       # BCrypt
│   │   └── jwt.py            # JWT
│   ├── dependencies/          # 의존성
│   │   └── auth.py           # 인증 의존성
│   └── utils/                 # 유틸리티
│       ├── logger.py
│       └── validators.py
├── init_db.py                 # DB 초기화
├── test_api.py                # API 테스트
├── setup.sql                  # DB 스키마
├── requirements.txt
├── SETUP_GUIDE.md             # 상세 설치 가이드
└── README.md
```

## MQTT 통신 프로토콜

### 토픽 구조

```
devices/{device_id}/control/camera      # 카메라 제어
devices/{device_id}/control/microphone  # 마이크 제어
devices/{device_id}/control/speaker     # 스피커 제어
devices/{device_id}/control/display     # 디스플레이 제어
devices/{device_id}/status              # 상태 보고
devices/{device_id}/response            # 명령 응답
```

### 메시지 형식 (JSON)

```json
{
  "command": "camera",
  "action": "start",
  "timestamp": 1234567890,
  "request_id": "uuid"
}
```

## WebSocket 통신

### 연결

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws?token=${accessToken}`);
```

### 메시지 타입

```json
// 장비 구독
{
  "type": "subscribe_device",
  "device_id": 1
}

// 상태 업데이트 (서버 → 클라이언트)
{
  "type": "device_status",
  "device_id": 1,
  "status": { ... }
}

// Ping-Pong
{
  "type": "ping"
}
```

## 개발 가이드

### 새 API 추가

1. `app/schemas/`에 Pydantic 스키마 정의
2. `app/api/`에 라우터 생성
3. `app/main.py`에 라우터 등록

### 권한 제어

```python
from app.dependencies import require_admin, require_operator

@router.get("/admin-only")
async def admin_only(current_user: User = Depends(require_admin)):
    # 관리자만 접근 가능
    pass
```

### 감사 로그 기록

```python
from app.models import AuditLog
from app.dependencies import get_client_ip

audit_log = AuditLog(
    user_id=current_user.id,
    device_id=device.id,
    action="action_name",
    resource_type="device",
    resource_id=str(device.id),
    ip_address=get_client_ip(request)
)
db.add(audit_log)
db.commit()
```

## 보안 체크리스트

운영 환경 배포 전:

- [ ] `SECRET_KEY` 변경 (최소 32자)
- [ ] `DEBUG=False` 설정
- [ ] 초기 관리자 비밀번호 변경
- [ ] CORS 설정 검토
- [ ] HTTPS 설정 (리버스 프록시)
- [ ] MQTT TLS 설정
- [ ] 방화벽 설정
- [ ] 정기 백업 설정

## 참고 문서

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- MQTT: https://mqtt.org/
- Core S3: https://docs.m5stack.com/en/core/CoreS3

## 라이선스

MIT License
