#!/bin/bash
# ============================================================
# ASR (RK3588) Docker 빌드 스크립트
# ============================================================

set -e

echo "=========================================="
echo "Building ASR Docker Image for RK3588..."
echo "=========================================="

# RK3588 확인
if [ ! -e /dev/dri/renderD128 ] && [ ! -e /dev/dri/renderD129 ]; then
    echo "Warning: RK3588 NPU device not found."
    echo "The container will run in CPU mode."
fi

# .env 파일 확인
if [ ! -f .env ]; then
    echo "Creating .env from env.example..."
    cp env.example .env
fi

# 모델 디렉토리 확인
if [ ! -d ./models ]; then
    echo "Creating models directory..."
    mkdir -p ./models
    echo "Please copy your RKNN models to ./models/"
fi

# 빌드
docker-compose build

echo "=========================================="
echo "Build Complete!"
echo ""
echo "Before running, ensure:"
echo "1. RKNN models are in ./models/"
echo "2. librknnrt.so is available at /usr/lib/aarch64-linux-gnu/"
echo ""
echo "Run: docker-compose up -d"
echo "=========================================="
