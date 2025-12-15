# ============================================================
# YOLO 검출 서버 Dockerfile (Jetson 전용)
# 대상: NVIDIA Jetson (Orin, Xavier, Nano)
# 요구사항: JetPack 5.x 이상
# Python: 3.10
# ============================================================

# NVIDIA L4T ML 컨테이너 사용 (JetPack 5.x / L4T R35.x 기준)
# 참고: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-ml
FROM nvcr.io/nvidia/l4t-ml:r35.2.1-py3

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
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python 3.10을 기본으로 설정
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# pip 업그레이드
RUN python -m pip install --upgrade pip setuptools wheel

# 작업 디렉토리
WORKDIR /app

# PyTorch (Jetson 전용 wheel)
# 참고: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048
# JetPack 5.x용 PyTorch 2.0.0+nv23.05
RUN pip install --no-cache-dir \
    https://developer.download.nvidia.com/compute/redist/jp/v51/pytorch/torch-2.0.0+nv23.05-cp310-cp310-linux_aarch64.whl

# torchvision (PyTorch 버전과 호환)
RUN pip install --no-cache-dir \
    https://developer.download.nvidia.com/compute/redist/jp/v51/pytorch/torchvision-0.15.1+nvpyg23.05-cp310-cp310-linux_aarch64.whl || \
    pip install --no-cache-dir torchvision==0.15.1

# 의존성 설치
COPY backend/yolodetect/requirements.txt /app/requirements_yolo.txt
COPY backend/yolodetect/requirements_jetson.txt /app/requirements_jetson.txt

# 기본 요구사항 설치 (torch 제외)
RUN pip install --no-cache-dir -r requirements_yolo.txt || true

# MediaPipe (aarch64용 빌드 필요할 수 있음)
RUN pip install --no-cache-dir mediapipe || \
    echo "MediaPipe installation failed - may need manual build for aarch64"

# 추가 패키지
RUN pip install --no-cache-dir \
    streamlit>=1.28.0 \
    streamlit-image-coordinates>=0.1.0 \
    ultralytics>=8.0.0 \
    opencv-python>=4.8.0 \
    requests>=2.31.0 \
    Pillow>=10.0.0 \
    flask>=2.0.0 \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    python-multipart>=0.0.6

# 소스 코드 복사
COPY backend/yolodetect /app/yolodetect

# 모델 디렉토리 생성
RUN mkdir -p /app/models /app/detection_results

# YOLO 모델 다운로드 (또는 복사)
# 모델 파일이 있으면 복사, 없으면 실행 시 다운로드
COPY backend/yolodetect/yolov8n.pt /app/models/ 2>/dev/null || true

# 환경 변수
ENV YOLO_MODEL=/app/models/yolov8n.pt
ENV STORAGE_PATH=/app/detection_results
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# 포트 노출
EXPOSE 8501 8082

# 작업 디렉토리
WORKDIR /app/yolodetect

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 시작 스크립트
COPY docker/yolo-jetson/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
