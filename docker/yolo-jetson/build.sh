#!/bin/bash
# ============================================================
# YOLO (Jetson) Docker 빌드 스크립트
# ============================================================

set -e

echo "=========================================="
echo "Building YOLO Docker Image for Jetson..."
echo "=========================================="

# Jetson 확인
if [ ! -f /etc/nv_tegra_release ]; then
    echo "Warning: This doesn't appear to be a Jetson device."
    echo "The build may fail on non-Jetson hardware."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# .env 파일 확인
if [ ! -f .env ]; then
    echo "Creating .env from env.example..."
    cp env.example .env
fi

# NVIDIA Container Runtime 확인
if ! docker info 2>/dev/null | grep -q nvidia; then
    echo "Warning: NVIDIA Container Runtime not detected."
    echo "Please install nvidia-docker2:"
    echo "  sudo apt-get install -y nvidia-docker2"
    echo "  sudo systemctl restart docker"
fi

# 빌드 (시간이 오래 걸림)
echo "Building... This may take 30+ minutes."
docker-compose build

echo "=========================================="
echo "Build Complete!"
echo ""
echo "Run: docker-compose up -d"
echo "=========================================="
