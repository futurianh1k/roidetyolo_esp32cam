#!/bin/bash
# ============================================================
# 웹앱 Docker 빌드 스크립트
# ============================================================

set -e

echo "=========================================="
echo "Building WebApp Docker Images..."
echo "=========================================="

# .env 파일 확인
if [ ! -f .env ]; then
    echo "Creating .env from env.example..."
    cp env.example .env
fi

# 빌드
docker-compose build --no-cache

echo "=========================================="
echo "Build Complete!"
echo ""
echo "Run: docker-compose up -d"
echo "=========================================="
