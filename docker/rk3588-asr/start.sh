#!/bin/bash
# ============================================================
# ASR 서버 시작 스크립트 (RK3588)
# ============================================================

set -e

echo "=========================================="
echo "ASR Server Starting (RK3588)..."
echo "=========================================="

# NPU 확인
echo "Checking NPU availability..."
if [ -e /dev/dri/renderD128 ] || [ -e /dev/dri/renderD129 ]; then
    echo "NPU device found!"
    ls -la /dev/dri/
else
    echo "Warning: NPU device not found. Running in CPU mode."
fi

# RKNN 확인
python -c "
try:
    from rknnlite.api import RKNNLite
    print('RKNN Lite loaded successfully')
except ImportError:
    print('Warning: RKNN Lite not available')
" || true

# 모델 확인
if [ -d "${ASR_MODEL_PATH:-/app/models}" ]; then
    echo "Model directory: ${ASR_MODEL_PATH:-/app/models}"
    ls -la ${ASR_MODEL_PATH:-/app/models}/ || echo "No models found"
fi

# ASR API 서버 실행
echo "Starting ASR API Server on port ${ASR_SERVER_PORT:-8081}..."
exec python asr_api_server.py \
    --host ${ASR_SERVER_HOST:-0.0.0.0} \
    --port ${ASR_SERVER_PORT:-8081}
