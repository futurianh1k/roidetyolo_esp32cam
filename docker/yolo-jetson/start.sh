#!/bin/bash
# ============================================================
# YOLO 서버 시작 스크립트
# ============================================================

set -e

echo "=========================================="
echo "YOLO Detection Server Starting..."
echo "=========================================="

# GPU 확인
echo "Checking GPU availability..."
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')" || true

# 모델 확인/다운로드
if [ ! -f "${YOLO_MODEL:-/app/models/yolov8n.pt}" ]; then
    echo "Downloading YOLO model..."
    python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
    mv yolov8n.pt /app/models/ 2>/dev/null || true
fi

# Image Receiver (백그라운드 실행)
echo "Starting Image Receiver on port 8082..."
python image_receiver.py &
IMAGE_RECEIVER_PID=$!

# Streamlit 앱 실행
echo "Starting Streamlit on port 8501..."
streamlit run streamlit_app_v2.py \
    --server.port=${STREAMLIT_SERVER_PORT:-8501} \
    --server.address=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0} \
    --server.headless=true \
    --browser.gatherUsageStats=false &
STREAMLIT_PID=$!

# 종료 핸들러
cleanup() {
    echo "Shutting down..."
    kill $IMAGE_RECEIVER_PID 2>/dev/null || true
    kill $STREAMLIT_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# 프로세스 대기
wait $STREAMLIT_PID
