#!/bin/bash
# ============================================================
# 백엔드 시작 스크립트
# 1. DB 연결 대기
# 2. 테이블 생성 및 초기화
# 3. 서버 시작
# ============================================================

set -e

echo "=========================================="
echo "Backend Server Starting..."
echo "=========================================="

# DB 연결 대기 (최대 60초)
echo "Waiting for database connection..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    python -c "
from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('Database connected!')
    exit(0)
except Exception as e:
    print(f'Waiting... ({e})')
    exit(1)
" && break

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Retry $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Could not connect to database after $MAX_RETRIES retries"
    exit 1
fi

# 테이블 생성 및 초기화
echo "Initializing database tables..."
python -c "
from app.database import engine, Base
from app.models import *  # 모든 모델 import
from init_db import init_database

# 테이블 생성
print('Creating tables...')
Base.metadata.create_all(bind=engine)
print('Tables created!')

# 초기 관리자 계정 생성
print('Creating initial admin account...')
init_database()
print('Database initialization complete!')
"

if [ $? -ne 0 ]; then
    echo "WARNING: Database initialization had issues, but continuing..."
fi

echo "=========================================="
echo "Starting Uvicorn server..."
echo "=========================================="

# 서버 시작
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
