# ASR 통합 배포 체크리스트

## 개요

이 문서는 RK3588 ASR 서버와 백엔드를 통합하는 전체 배포 프로세스를 설명합니다.

## 아키텍처

```
ESP32 Device (마이크음음 캡처)
    ↓ [WebSocket Binary PCM]
RK3588 ASR Server (음성인식)
    ↓ [HTTP POST JSON]
Backend API (결과 수신 및 저장)
    ↓ [WebSocket Broadcast]
Web Frontend (실시간 표시)
```

## 1️⃣ RK3588 ASR 서버 설정

### 1.1 환경 준비

```bash
# RK3588 디바이스에 접속
ssh user@rk3588-ip

# Python 3.10+ 설치 확인
python3 --version

# 필요한 패키지 설치
cd ~/roidetyolo_esp32cam/backend/rk3588asr
pip install -r requirements_api.txt
```

### 1.2 환경 변수 설정

ASR 서버에서 백엔드 결과 전송을 위해 환경 변수 설정:

```bash
# .env 파일 또는 시작 스크립트에서 설정
export BACKEND_URL="http://backend-server-ip:8000"
# 예: export BACKEND_URL="http://192.168.1.100:8000"
```

### 1.3 ASR 서버 시작

```bash
# 단일 실행
python3 asr_api_server.py

# 또는 백그라운드 실행 (권장)
nohup python3 asr_api_server.py > asr_server.log 2>&1 &
```

**확인사항:**

- ✅ 모델 로딩 완료 (약 4-5초)
- ✅ WebSocket 엔드포인트 등록:
  - `/ws/asr/{session_id}` (Base64 JSON)
  - `/ws/audio/{session_id}` (Binary PCM)
- ✅ HTTP 헬스 체크: `GET http://rk3588-ip:8001/health`

```bash
# 헬스 체크 테스트
curl http://192.168.1.50:8001/health
# 응답 예:
# {"status": "healthy", "asr_server": {"model_loaded": true, ...}}
```

## 2️⃣ 백엔드 설정

### 2.1 환경 변수 설정

`backend/.env` 파일:

```bash
# 기본 설정
APP_NAME=CoreS3 Management System
DEBUG=False
ENVIRONMENT=production

# 서버
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://frontend-ip:3000,http://rk3588-ip:8001

# ASR 서버 연결
BACKEND_URL=http://your-backend-ip:8000
# ASR 서버 주소 (선택: 직접 조회가 필요한 경우)
ASR_SERVER_HOST=192.168.1.50
ASR_SERVER_PORT=8001

# 데이터베이스, MQTT 등 기존 설정...
```

### 2.2 새 엔드포인트 확인

백엔드가 다음 엔드포인트를 제공해야 합니다:

| 메서드 | 경로                               | 설명                        |
| ------ | ---------------------------------- | --------------------------- |
| POST   | `/asr/result`                      | ASR 서버가 인식 결과를 전송 |
| GET    | `/asr/health`                      | ASR 서버 헬스 체크          |
| POST   | `/asr/devices/{id}/session/start`  | 음성인식 세션 시작          |
| POST   | `/asr/devices/{id}/session/stop`   | 음성인식 세션 종료          |
| GET    | `/asr/devices/{id}/session/status` | 세션 상태 조회              |

### 2.3 백엔드 시작

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**확인사항:**

- ✅ `/asr/health` 엔드포인트 응답
- ✅ 데이터베이스 연결 성공
- ✅ WebSocket 준비 완료

## 3️⃣ ESP32 펌웨어 업데이트

### 3.1 ASR 서버 주소 설정

`firmware/include/config.h`:

```cpp
// ASR 서버 설정
#define ASR_SERVER_HOST "192.168.1.50"  // RK3588 IP
#define ASR_SERVER_PORT 8001
#define ASR_WS_PATH "/ws/audio"  // 새 엔드포인트 사용

// WebSocket URL 생성: ws://192.168.1.50:8001/ws/audio/{session_id}
```

### 3.2 오디오 스트리밍 구현

`firmware/src/audio_module.cpp`:

```cpp
// 기존 /ws/asr 엔드포인트 대신 /ws/audio 사용
// 메시지 포맷: 16-bit PCM 바이너리 데이터 (Base64 아님)

void audio_stream_to_asr() {
    // 마이크에서 PCM 샘플 읽기
    uint16_t buffer[SAMPLE_BUFFER_SIZE];

    // WebSocket으로 바이너리 PCM 전송
    websocket.sendBinary((uint8_t*)buffer, sizeof(buffer));
}
```

### 3.3 펌웨어 컴파일 및 업로드

```bash
cd firmware
pio run -t upload  # ESP32-S3 등 기본 타겟
# 또는
pio run -e esp32-s3 -t upload
```

## 4️⃣ 통합 테스트

### 4.1 ASR 서버 테스트

```bash
# Python 테스트 클라이언트 실행
cd backend/rk3588asr
python test_websocket_client.py

# 또는 curl로 기본 엔드포인트 테스트
curl -X GET http://192.168.1.50:8001/health
```

### 4.2 백엔드 결과 수신 테스트

```bash
# ASR 서버에서 백엔드로 결과 전송 테스트
curl -X POST http://192.168.1.100:8000/asr/result \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "device_name": "CoreS3-01",
    "session_id": "test-session-001",
    "text": "테스트 음성입니다",
    "timestamp": "2025-12-08 10:30:45",
    "duration": 2.3,
    "is_emergency": false,
    "emergency_keywords": []
  }'

# 응답 예:
# {
#   "status": "success",
#   "message": "음성인식 결과가 저장되었습니다",
#   "device_id": 1,
#   "text": "테스트 음성입니다",
#   "is_emergency": false,
#   "broadcasted_count": 2
# }
```

### 4.3 WebSocket 브로드캐스트 테스트

```bash
# 웹 브라우저 개발자 도구에서 WebSocket 구독 확인
# 또는 테스트 클라이언트 사용

# 원격 테스트:
# 1. 웹 UI에서 음성인식 세션 시작
# 2. ESP32에서 음성 녹음
# 3. ASR 서버에서 인식
# 4. 백엔드로 결과 전송 (POST /asr/result)
# 5. 웹 UI에서 실시간 표시 확인
```

## 5️⃣ 응급 상황 감지 테스트

```bash
# 응급 키워드 포함 결과 전송
curl -X POST http://192.168.1.100:8000/asr/result \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "device_name": "CoreS3-01",
    "session_id": "emergency-test",
    "text": "119 화재입니다",
    "timestamp": "2025-12-08 10:31:00",
    "duration": 1.5,
    "is_emergency": true,
    "emergency_keywords": ["119", "화재"]
  }'

# 웹 UI에서 응급 경고 표시 확인
```

## 6️⃣ 프로덕션 배포

### 6.1 보안 설정

```bash
# 1. CORS 설정 조정
CORS_ORIGINS=https://your-domain.com

# 2. SECRET_KEY 변경 (최소 32자)
SECRET_KEY=your-very-long-random-secret-key-min-32-chars

# 3. DEBUG 비활성화
DEBUG=False

# 4. TLS/SSL 설정 (필요시)
```

### 6.2 모니터링

```bash
# 로그 모니터링
tail -f backend/logs/app.log
tail -f rk3588asr/asr_server.log

# 포트 확인
netstat -tuln | grep -E "8000|8001"

# 프로세스 확인
ps aux | grep -E "uvicorn|asr_api_server"
```

### 6.3 자동 시작 설정

**백엔드 (Linux systemd):**

```bash
# /etc/systemd/system/cores3-backend.service
[Unit]
Description=CoreS3 Backend API
After=network.target

[Service]
Type=simple
User=cores3
WorkingDirectory=/home/cores3/roidetyolo_esp32cam/backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**ASR 서버 (RK3588):**

```bash
# /etc/systemd/system/asr-server.service
[Unit]
Description=RK3588 ASR Server
After=network.target

[Service]
Type=simple
User=asr
WorkingDirectory=/home/asr/roidetyolo_esp32cam/backend/rk3588asr
Environment="BACKEND_URL=http://backend-ip:8000"
ExecStart=/usr/bin/python3 asr_api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**활성화:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable cores3-backend.service asr-server.service
sudo systemctl start cores3-backend.service asr-server.service
sudo systemctl status cores3-backend.service asr-server.service
```

## 7️⃣ 트러블슈팅

### ASR 서버가 결과를 전송하지 않음

```bash
# 1. 백엔드 연결 확인
curl -I http://backend-ip:8000

# 2. 방화벽 확인
sudo ufw status
# 포트 8000, 8001 허용 필요

# 3. 환경 변수 확인
echo $BACKEND_URL

# 4. 로그 확인
tail -100 asr_server.log | grep -i "backend\|error"
```

### WebSocket 브로드캐스트가 작동하지 않음

```bash
# 1. WebSocket 구독 확인
curl http://backend-ip:8000/asr/sessions

# 2. 활성 연결 확인
netstat -tuln | grep 8000

# 3. 백엔드 로그 확인
tail -100 backend/logs/app.log | grep -i "broadcast\|websocket"
```

### ESP32가 음성을 전송하지 않음

```bash
# 1. 마이크 초기화 확인 (펌웨어 로그)
# Serial Monitor에서: "마이크 초기화 완료" 확인

# 2. ASR 서버 주소 확인
# 펌웨어 config.h에서 ASR_SERVER_HOST 확인

# 3. 네트워크 연결 확인
# 펌웨어 로그에서 WiFi 연결 확인
```

## 8️⃣ 성능 최적화

### 오디오 버퍼 크기 조정

ASR 서버 `asr_api_server.py`:

```python
# 음성 청크 크기 (바이트)
AUDIO_CHUNK_SIZE = 4096  # 기본값, 필요시 8192로 증가

# VAD 타임아웃 (초)
VAD_TIMEOUT = 3.0  # 침묵 시간 제한
```

### 동시 세션 수 제한

```python
# demo_vad_final.py
MAX_CONCURRENT_SESSIONS = 10  # 동시 세션 수 제한
```

## 체크리스트

- [ ] RK3588 ASR 서버 시작됨 (포트 8001)
- [ ] 백엔드 서버 시작됨 (포트 8000)
- [ ] 환경 변수 설정: `BACKEND_URL`
- [ ] `/asr/result` 엔드포인트 테스트 성공
- [ ] ESP32 펌웨어 업데이트: ASR 서버 주소 설정
- [ ] WebSocket 구독 확인
- [ ] 웹 UI에서 음성인식 결과 표시 확인
- [ ] 응급 상황 감지 테스트
- [ ] 프로덕션 보안 설정 완료
- [ ] 자동 시작 스크립트 설정 완료
- [ ] 로그 모니터링 설정 완료

---

**작성일**: 2025-12-08
**버전**: 1.0
**상태**: 배포 준비 완료 ✅
