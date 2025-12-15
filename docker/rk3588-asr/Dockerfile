# ============================================================
# ASR 서버 Dockerfile (RK3588 전용)
# 대상: Rockchip RK3588 보드 (Orange Pi 5, Rock 5B 등)
# Python: 3.10
# ============================================================

FROM ubuntu:22.04

# 환경 변수
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Seoul
ENV DEBIAN_FRONTEND=noninteractive

# 시간대 설정
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    libsndfile1 \
    libportaudio2 \
    portaudio19-dev \
    libasound2-dev \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 3.10을 기본으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# pip 업그레이드
RUN python -m pip install --upgrade pip setuptools wheel

# 작업 디렉토리
WORKDIR /app

# RKNN Toolkit2 설치 (RK3588 NPU 지원)
# 참고: https://github.com/rockchip-linux/rknn-toolkit2
# 실제 환경에서는 적절한 wheel 파일 복사 필요
RUN pip install --no-cache-dir \
    numpy>=1.24.0,<2.0.0 \
    opencv-python-headless>=4.8.0

# RKNN 런타임 (호스트에서 마운트하거나 빌드 시 복사)
# COPY rknn_toolkit2*.whl /tmp/
# RUN pip install /tmp/rknn_toolkit2*.whl

# 의존성 설치
COPY backend/rk3588asr/requirements_api.txt /app/requirements_api.txt

# 기본 요구사항 설치
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    websockets==12.0 \
    python-multipart==0.0.6 \
    pydantic>=2.5.0 \
    python-jose[cryptography]==3.3.0 \
    aiofiles>=23.2.1 \
    httpx>=0.25.0

# 오디오 처리 패키지
RUN pip install --no-cache-dir \
    sounddevice>=0.4.6 \
    soundfile>=0.12.1 \
    librosa>=0.10.1 \
    webrtcvad>=2.0.10 || true

# 소스 코드 복사
COPY backend/rk3588asr /app/rk3588asr

# 모델 디렉토리 생성
RUN mkdir -p /app/models /app/logs

# 환경 변수
ENV ASR_MODEL_PATH=/app/models
ENV ASR_SERVER_PORT=8081
ENV ASR_SERVER_HOST=0.0.0.0

# 포트 노출
EXPOSE 8081

# 작업 디렉토리
WORKDIR /app/rk3588asr

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# 시작 스크립트
COPY docker/rk3588-asr/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
