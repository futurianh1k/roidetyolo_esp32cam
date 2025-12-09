# ASR 시스템 배포 가이드

**버전**: 1.0.0  
**작성일**: 2025-12-08  
**플랫폼**: Windows / Ubuntu

---

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [설치 가이드 - Windows](#설치-가이드---windows)
3. [설치 가이드 - Ubuntu](#설치-가이드---ubuntu)
4. [RK3588 ASR 서버 설정](#rk3588-asr-서버-설정)
5. [네트워크 설정](#네트워크-설정)
6. [서비스 등록 및 자동 시작](#서비스-등록-및-자동-시작)
7. [모니터링 및 로깅](#모니터링-및-로깅)
8. [트러블슈팅](#트러블슈팅)

---

## 💻 시스템 요구사항

### 하드웨어

| 컴포넌트        | 최소 사양 | 권장 사양                  |
| --------------- | --------- | -------------------------- |
| **RK3588 보드** | -         | Orange Pi 5 Plus / Rock 5B |
| **RAM**         | 4GB       | 8GB 이상                   |
| **저장공간**    | 10GB      | 20GB 이상 (SSD 권장)       |
| **네트워크**    | 100Mbps   | 1Gbps                      |

### 소프트웨어

| 컴포넌트         | 버전                             |
| ---------------- | -------------------------------- |
| **Python**       | 3.8 이상                         |
| **Node.js**      | 18.x 이상                        |
| **MQTT Broker**  | Mosquitto 2.0+                   |
| **OS (RK3588)**  | Ubuntu 22.04 ARM64               |
| **OS (개발 PC)** | Windows 10/11 또는 Ubuntu 20.04+ |

---

## 🪟 설치 가이드 - Windows

### 1. Python 가상환경 설정

```powershell
# 프로젝트 디렉토리로 이동
cd D:\cursorworks\roidetyolo_esp32cam

# 가상환경 생성 (venv)
python -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 실행 정책 오류 시
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. 백엔드 의존성 설치

```powershell
# 백엔드 디렉토리로 이동
cd backend

# 기본 의존성 설치
pip install -r requirements.txt

# 추가 라이브러리
pip install fastapi uvicorn[standard] paho-mqtt sqlalchemy
```

### 3. 프론트엔드 설정

```powershell
# 프론트엔드 디렉토리로 이동
cd ../frontend

# Node.js 의존성 설치
npm install

# 또는 yarn 사용
yarn install
```

### 4. MQTT Broker 설치 (Mosquitto)

**다운로드**:

- https://mosquitto.org/download/

**설치 후 서비스 시작**:

```powershell
# 서비스 시작
net start mosquitto

# 서비스 상태 확인
sc query mosquitto
```

**설정 파일** (`C:\Program Files\mosquitto\mosquitto.conf`):

```conf
# 기본 설정
listener 1883
allow_anonymous true

# 로그 설정
log_dest file C:/Program Files/mosquitto/mosquitto.log
log_type all
```

### 5. 환경변수 설정

**`.env` 파일 생성** (`backend/.env`):

```env
# 데이터베이스
DATABASE_URL=sqlite:///./device_management.db

# MQTT 설정
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# ASR 서버 설정
ASR_SERVER_URL=http://192.168.1.100:8001

# JWT 설정
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 6. 데이터베이스 초기화

```powershell
cd backend

# Alembic 마이그레이션
alembic upgrade head

# 또는 직접 실행
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### 7. 서버 실행

**백엔드 (Terminal 1)**:

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**프론트엔드 (Terminal 2)**:

```powershell
cd frontend
npm run dev
# 또는
yarn dev
```

**접속 URL**:

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

---

## 🐧 설치 가이드 - Ubuntu

### 1. 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Python 및 pip 설치

```bash
# Python 3.10 설치
sudo apt install -y python3.10 python3.10-venv python3-pip

# 버전 확인
python3 --version
```

### 3. Node.js 및 npm 설치

```bash
# NodeSource 리포지토리 추가
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Node.js 설치
sudo apt install -y nodejs

# 버전 확인
node --version
npm --version
```

### 4. MQTT Broker 설치 (Mosquitto)

```bash
# Mosquitto 설치
sudo apt install -y mosquitto mosquitto-clients

# 서비스 시작
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# 상태 확인
sudo systemctl status mosquitto
```

**설정 파일** (`/etc/mosquitto/mosquitto.conf`):

```conf
listener 1883
allow_anonymous true
log_dest file /var/log/mosquitto/mosquitto.log
```

### 5. 프로젝트 클론 및 설정

```bash
# 프로젝트 디렉토리
cd /opt
sudo git clone https://github.com/your-repo/roidetyolo_esp32cam.git
cd roidetyolo_esp32cam

# 소유권 변경
sudo chown -R $USER:$USER .
```

### 6. Python 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
cd backend
pip install -r requirements.txt
```

### 7. 프론트엔드 빌드

```bash
cd frontend

# 의존성 설치
npm install

# 프로덕션 빌드
npm run build
```

### 8. 환경변수 설정

```bash
# .env 파일 생성
cd /opt/roidetyolo_esp32cam/backend
nano .env
```

**내용**:

```env
DATABASE_URL=sqlite:////opt/roidetyolo_esp32cam/backend/device_management.db
MQTT_BROKER=localhost
MQTT_PORT=1883
ASR_SERVER_URL=http://192.168.1.100:8001
SECRET_KEY=$(openssl rand -hex 32)
```

### 9. 데이터베이스 초기화

```bash
cd /opt/roidetyolo_esp32cam/backend
source ../venv/bin/activate
alembic upgrade head
```

---

## 🎯 RK3588 ASR 서버 설정

### 1. RK3588 보드 준비

**OS 설치**: Ubuntu 22.04 ARM64

**SSH 접속**:

```bash
ssh user@192.168.1.100
```

### 2. Sherpa-ONNX 설치

```bash
# 의존성 설치
sudo apt install -y python3-pip python3-dev

# Sherpa-ONNX 설치 (RK3588 버전)
pip3 install sherpa-onnx -f https://k2-fsa.github.io/sherpa/onnx/rk-npu.html
```

### 3. 음성인식 모델 다운로드

```bash
# 모델 디렉토리 생성
mkdir -p ~/asr_models
cd ~/asr_models

# Sense-Voice 모델 다운로드
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-rk3588-30-seconds-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2

# 압축 해제
tar -xjf sherpa-onnx-rk3588-30-seconds-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
```

### 4. ASR API 서버 배포

```bash
# 프로젝트 디렉토리 생성
mkdir -p ~/asr_server
cd ~/asr_server

# 파일 복사 (로컬 PC에서)
scp -r backend/rk3588asr/* user@192.168.1.100:~/asr_server/

# 모델 심볼릭 링크
cd ~/asr_server
ln -s ~/asr_models/sherpa-onnx-rk3588-30-seconds-sense-voice-zh-en-ja-ko-yue-2024-07-17 models
```

### 5. Python 의존성 설치

```bash
cd ~/asr_server

# 기본 의존성
pip3 install -r requirements.txt

# API 서버 의존성
pip3 install -r requirements_api.txt
```

### 6. SSL 인증서 생성 (선택적)

```bash
# 자체 서명 인증서
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
```

### 7. ASR 서버 실행

```bash
# 기본 실행
python3 asr_api_server.py

# NPU 4코어 사용 (권장)
taskset 0x0F python3 asr_api_server.py --host 0.0.0.0 --port 8001
```

### 8. 서비스 등록 (systemd)

**서비스 파일 생성** (`/etc/systemd/system/asr-server.service`):

```ini
[Unit]
Description=ASR WebSocket API Server
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/asr_server
Environment="PATH=/home/user/.local/bin:/usr/local/bin:/usr/bin"
ExecStart=/usr/bin/taskset 0x0F /usr/bin/python3 asr_api_server.py --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 시작**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable asr-server
sudo systemctl start asr-server
sudo systemctl status asr-server
```

---

## 🌐 네트워크 설정

### 포트 포워딩

| 서비스     | 포트 | 프로토콜 | 설명              |
| ---------- | ---- | -------- | ----------------- |
| 프론트엔드 | 3000 | HTTP     | Next.js 개발 서버 |
| 백엔드 API | 8000 | HTTP     | FastAPI 서버      |
| ASR 서버   | 8001 | HTTP/WS  | 음성인식 API      |
| MQTT       | 1883 | TCP      | MQTT 브로커       |
| Gradio UI  | 7860 | HTTPS    | ASR 테스트 UI     |

### 방화벽 설정 (Ubuntu)

```bash
# UFW 방화벽 설정
sudo ufw allow 8000/tcp  # 백엔드
sudo ufw allow 8001/tcp  # ASR 서버
sudo ufw allow 1883/tcp  # MQTT
sudo ufw allow 7860/tcp  # Gradio
sudo ufw enable
```

### 방화벽 설정 (Windows)

```powershell
# PowerShell (관리자 권한)
New-NetFirewallRule -DisplayName "FastAPI Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "ASR Server" -Direction Inbound -LocalPort 8001 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "MQTT Broker" -Direction Inbound -LocalPort 1883 -Protocol TCP -Action Allow
```

---

## 🔄 서비스 등록 및 자동 시작

### Ubuntu (systemd)

**백엔드 서비스** (`/etc/systemd/system/backend.service`):

```ini
[Unit]
Description=FastAPI Backend Server
After=network.target postgresql.service

[Service]
Type=simple
User=user
WorkingDirectory=/opt/roidetyolo_esp32cam/backend
Environment="PATH=/opt/roidetyolo_esp32cam/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/opt/roidetyolo_esp32cam/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**프론트엔드 서비스** (`/etc/systemd/system/frontend.service`):

```ini
[Unit]
Description=Next.js Frontend Server
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/opt/roidetyolo_esp32cam/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 시작**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable backend frontend
sudo systemctl start backend frontend
```

### Windows (NSSM - Non-Sucking Service Manager)

**NSSM 설치**:

1. https://nssm.cc/download 에서 다운로드
2. `nssm.exe`를 `C:\Windows\System32`에 복사

**백엔드 서비스 등록**:

```powershell
# 관리자 권한 PowerShell
nssm install FastAPIBackend "D:\cursorworks\roidetyolo_esp32cam\venv\Scripts\python.exe" `
  "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
nssm set FastAPIBackend AppDirectory "D:\cursorworks\roidetyolo_esp32cam\backend"
nssm set FastAPIBackend DisplayName "FastAPI Backend Server"
nssm start FastAPIBackend
```

---

## 📊 모니터링 및 로깅

### 로그 위치

| 서비스   | Windows                                    | Ubuntu                     |
| -------- | ------------------------------------------ | -------------------------- |
| 백엔드   | `backend/logs/app.log`                     | `/var/log/backend/app.log` |
| ASR 서버 | `~/asr_server/logs/`                       | `/var/log/asr/`            |
| MQTT     | `C:\Program Files\mosquitto\mosquitto.log` | `/var/log/mosquitto/`      |
| Nginx    | -                                          | `/var/log/nginx/`          |

### 로그 확인

**Ubuntu**:

```bash
# 실시간 로그 확인
sudo journalctl -u backend -f
sudo journalctl -u asr-server -f

# 최근 100줄
sudo journalctl -u backend -n 100
```

**Windows**:

```powershell
# 이벤트 뷰어
eventvwr.msc

# 로그 파일 직접 확인
Get-Content -Path "D:\cursorworks\roidetyelo_esp32cam\backend\logs\app.log" -Tail 50 -Wait
```

### 모니터링 도구

**Prometheus + Grafana** (선택적):

```bash
# Prometheus 설치
sudo apt install prometheus

# Grafana 설치
sudo apt install grafana
```

---

## 🔧 트러블슈팅

### 1. 백엔드 서버가 시작되지 않음

**증상**:

```
uvicorn.error - ERROR - Error loading ASGI app
```

**해결**:

```bash
# 의존성 재설치
pip install --upgrade -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 환경변수 확인
cat .env
```

### 2. ASR 서버 모델 로딩 실패

**증상**:

```
❌ 모델 로딩 실패: [Errno 2] No such file or directory
```

**해결**:

```bash
# 모델 경로 확인
ls -la ~/asr_server/models/

# demo_vad_final.py 수정
nano demo_vad_final.py
# MODEL_DIR 경로를 절대 경로로 수정
```

### 3. MQTT 연결 실패

**증상**:

```
Connection refused [Errno 111]
```

**해결**:

```bash
# Mosquitto 상태 확인
sudo systemctl status mosquitto

# 방화벽 확인
sudo ufw status

# 포트 리스닝 확인
sudo netstat -tulpn | grep 1883
```

### 4. WebSocket 연결 끊김

**증상**:

```
🔌 WebSocket 연결 끊김: uuid-xxxx
```

**해결**:

- 네트워크 안정성 확인
- Nginx 타임아웃 설정 증가
- CoreS3 펌웨어 재시작

### 5. 메모리 부족

**증상**:

```
MemoryError: Unable to allocate array
```

**해결**:

```bash
# 스왑 메모리 추가 (Ubuntu)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Sherpa-ONNX 설치 가이드](https://k2-fsa.github.io/sherpa/onnx/install/)
- [Mosquitto 설정 가이드](https://mosquitto.org/man/mosquitto-conf-5.html)
- [systemd 서비스 가이드](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

**문서 버전**: 1.0.0  
**최종 수정**: 2025-12-08
