# Core S3 Management System - 백엔드 설치 가이드

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [Windows 설치](#windows-설치)
3. [Ubuntu 설치](#ubuntu-설치)
4. [데이터베이스 설정](#데이터베이스-설정)
5. [애플리케이션 실행](#애플리케이션-실행)
6. [테스트](#테스트)

---

## 사전 요구사항

- Python 3.9 이상
- MySQL 5.7 이상 또는 MariaDB 10.3 이상
- pip (Python 패키지 관리자)

---

## Windows 설치

### 1. Python 설치

Python 공식 웹사이트에서 다운로드: https://www.python.org/downloads/

설치 시 "Add Python to PATH" 옵션을 반드시 체크하세요.

### 2. MySQL 설치

MySQL Community Server 다운로드: https://dev.mysql.com/downloads/mysql/

또는 XAMPP 사용: https://www.apachefriends.org/

### 3. 프로젝트 설정

```powershell
# 프로젝트 디렉토리로 이동
cd D:\cursorworks\roidetyolo_esp32cam\backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
.\venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`env.example`을 `.env`로 복사하고 수정:

```powershell
copy env.example .env
notepad .env
```

필수 설정 항목:
- `SECRET_KEY`: 최소 32자 이상의 랜덤 문자열
- `DB_PASSWORD`: MySQL root 비밀번호
- `DB_NAME`: cores3_management

### 5. 데이터베이스 초기화

```powershell
# MySQL에 접속하여 setup.sql 실행
mysql -u root -p < setup.sql

# 또는 MySQL Workbench에서 setup.sql 파일을 열어 실행

# Python 스크립트로 초기화 (초기 관리자 계정 생성)
python init_db.py
```

### 6. 서버 실행

```powershell
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

---

## Ubuntu 설치

### 1. Python 및 MySQL 설치

```bash
# 시스템 패키지 업데이트
sudo apt update
sudo apt upgrade -y

# Python 및 필수 패키지 설치
sudo apt install python3 python3-pip python3-venv -y

# MySQL 설치
sudo apt install mysql-server -y

# MySQL 보안 설정
sudo mysql_secure_installation
```

### 2. 프로젝트 설정

```bash
# 프로젝트 디렉토리로 이동
cd /path/to/roidetyolo_esp32cam/backend

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# env.example을 .env로 복사
cp env.example .env

# 편집
nano .env
```

필수 설정 항목:
- `SECRET_KEY`: 최소 32자 이상의 랜덤 문자열 생성
  ```bash
  # 랜덤 키 생성
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- `DB_PASSWORD`: MySQL 비밀번호
- `DB_NAME`: cores3_management

### 4. 데이터베이스 초기화

```bash
# MySQL에 접속
sudo mysql -u root -p

# 또는 setup.sql 실행
sudo mysql -u root -p < setup.sql

# Python 스크립트로 초기화
python3 init_db.py
```

### 5. 서버 실행

```bash
# 개발 모드
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드 (백그라운드)
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 > server.log 2>&1 &
```

### 6. 방화벽 설정 (선택사항)

```bash
# UFW 방화벽 설정
sudo ufw allow 8000/tcp
sudo ufw reload
```

---

## 데이터베이스 설정

### MySQL 데이터베이스 수동 생성

```sql
-- MySQL 접속
mysql -u root -p

-- 데이터베이스 생성
CREATE DATABASE cores3_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 생성 (선택사항)
CREATE USER 'cores3user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON cores3_management.* TO 'cores3user'@'localhost';
FLUSH PRIVILEGES;

-- 확인
SHOW DATABASES;
USE cores3_management;
```

### 초기 관리자 계정

`init_db.py` 스크립트 실행 후 생성되는 초기 계정:

- **사용자명**: admin
- **비밀번호**: Admin123!
- **이메일**: admin@example.com
- **역할**: ADMIN

⚠️ **보안 경고**: 로그인 후 반드시 비밀번호를 변경하세요!

---

## 애플리케이션 실행

### 개발 환경

```bash
# Windows
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ubuntu
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 환경

```bash
# Gunicorn + Uvicorn Workers 사용 (Ubuntu)
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --daemon
```

### Systemd 서비스 등록 (Ubuntu)

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/cores3-backend.service
```

내용:

```ini
[Unit]
Description=Core S3 Management Backend
After=network.target mysql.service

[Service]
Type=notify
User=your_username
Group=your_username
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/venv/bin"
ExecStart=/path/to/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

서비스 시작:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cores3-backend
sudo systemctl start cores3-backend
sudo systemctl status cores3-backend
```

---

## 테스트

### 1. API 문서 확인

브라우저에서:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. 자동 테스트 실행

```bash
# 서버가 실행 중인 상태에서
python test_api.py
```

### 3. 수동 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 로그인
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}'

# 현재 사용자 정보 (토큰 필요)
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 문제 해결

### MySQL 연결 오류

```bash
# MySQL 서비스 확인
# Windows
net start MySQL80

# Ubuntu
sudo systemctl status mysql
sudo systemctl start mysql
```

### 포트 충돌

다른 포트 사용:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

`.env` 파일의 `PORT` 설정도 변경하세요.

### 의존성 설치 오류

```bash
# pip 업그레이드
pip install --upgrade pip

# 개별 설치
pip install fastapi uvicorn sqlalchemy pymysql
```

### 로그 확인

```bash
# 실시간 로그 확인 (Ubuntu)
tail -f logs/app.log

# Windows
type logs\app.log
```

---

## 보안 체크리스트

운영 환경 배포 전 확인사항:

- [ ] `.env` 파일의 `SECRET_KEY` 변경 (최소 32자)
- [ ] `DEBUG=False` 설정
- [ ] MySQL root 비밀번호 강화
- [ ] 초기 관리자 비밀번호 변경
- [ ] CORS 설정 (`CORS_ORIGINS`) 제한
- [ ] HTTPS 설정 (Nginx/Apache 리버스 프록시)
- [ ] 방화벽 설정 (필요한 포트만 개방)
- [ ] 정기 백업 설정

---

## 다음 단계

1. 프론트엔드 설정
2. MQTT 브로커 설정
3. Core S3 장비 연동
4. RTSP 스트리밍 설정

---

## 지원

문제가 발생하면:
1. `logs/app.log` 파일 확인
2. `python test_api.py` 실행하여 문제 진단
3. API 문서 (http://localhost:8000/docs) 참조

