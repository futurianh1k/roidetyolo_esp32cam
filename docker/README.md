# Docker 배포 가이드

이 프로젝트는 세 가지 Docker 환경으로 분리되어 배포됩니다.

## 🏗️ 구조

```
docker/
├── webapp/                    # 1. 프론트엔드 + 백엔드 (일반 PC/클라우드)
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── yolo-jetson/              # 2. YOLO 검출 서버 (Jetson 장비)
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── rk3588-asr/               # 3. ASR 서버 (RK3588 장비)
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 1️⃣ 웹앱 (프론트엔드 + 백엔드)

**대상**: 일반 PC, 클라우드 서버 (x86_64/amd64)

### 빌드 및 실행

```bash
cd docker/webapp

# .env 파일 설정
cp .env.example .env
# .env 파일 편집 (DB 정보 등)

# 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

### 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

---

## 2️⃣ YOLO 검출 서버 (Jetson)

**대상**: NVIDIA Jetson 장비 (Orin, Xavier, Nano 등)
**요구사항**: JetPack 5.x 이상, Python 3.10

### 사전 준비 (Jetson에서)

```bash
# Docker + NVIDIA Container Runtime 확인
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# NVIDIA 런타임 확인
docker info | grep -i nvidia
```

### 빌드 및 실행

```bash
cd docker/yolo-jetson

# .env 파일 설정
cp .env.example .env

# 빌드 (시간이 오래 걸릴 수 있음)
docker-compose build

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f yolo
```

### 접속

- **Streamlit UI**: http://<jetson-ip>:8501
- **Image Receiver API**: http://<jetson-ip>:8082

### GPU 확인

```bash
# 컨테이너 내부에서 GPU 확인
docker exec -it yolo-detector nvidia-smi
docker exec -it yolo-detector python -c "import torch; print(torch.cuda.is_available())"
```

---

## 3️⃣ ASR 서버 (RK3588)

**대상**: Rockchip RK3588 보드 (Orange Pi 5, Rock 5B 등)
**요구사항**: Ubuntu 22.04, RKNN Toolkit

### 사전 준비 (RK3588에서)

```bash
# Docker 설치
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# NPU 드라이버 확인
ls /dev/dri/
# renderD128 또는 renderD129 존재해야 함
```

### 빌드 및 실행

```bash
cd docker/rk3588-asr

# .env 파일 설정
cp .env.example .env

# 빌드
docker-compose build

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f asr
```

### 접속

- **ASR API**: http://<rk3588-ip>:8081
- **WebSocket**: ws://<rk3588-ip>:8081/ws/asr/{device_id}

---

## 🔧 공통 명령어

```bash
# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f [서비스명]

# 재시작
docker-compose restart [서비스명]

# 중지
docker-compose down

# 볼륨 포함 완전 삭제
docker-compose down -v

# 이미지 재빌드
docker-compose build --no-cache
```

---

## 📋 환경 변수

### 공통

| 변수 | 설명   | 기본값       |
| ---- | ------ | ------------ |
| `TZ` | 시간대 | `Asia/Seoul` |

### 백엔드

| 변수               | 설명           | 예시                                     |
| ------------------ | -------------- | ---------------------------------------- |
| `DATABASE_URL`     | DB 연결 문자열 | `mysql+pymysql://user:pass@host:3306/db` |
| `SECRET_KEY`       | JWT 시크릿     | 랜덤 문자열                              |
| `MQTT_BROKER_HOST` | MQTT 브로커    | `mosquitto`                              |

### YOLO

| 변수             | 설명           | 기본값                   |
| ---------------- | -------------- | ------------------------ |
| `YOLO_MODEL`     | 모델 파일      | `yolov8n.pt`             |
| `YOLO_FORCE_CPU` | CPU 강제 사용  | `false`                  |
| `STORAGE_PATH`   | 결과 저장 경로 | `/app/detection_results` |

---

## 🔗 참고 자료

- [NVIDIA Jetson Containers](https://github.com/dusty-nv/jetson-containers)
- [L4T ML Container](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-ml)
- [Rockchip RKNN](https://github.com/rockchip-linux/rknn-toolkit2)
