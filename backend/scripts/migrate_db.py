#!/usr/bin/env python3
"""
DB 마이그레이션 스크립트 (통합)

사용법:
    cd backend
    python scripts/migrate_db.py           # 마이그레이션 실행
    python scripts/migrate_db.py --check   # 상태만 확인
    python scripts/migrate_db.py --create-tables  # 새 테이블 생성

마이그레이션 내용:
1. devices 테이블에 status_report_interval 컬럼 추가
2. alarm_history 테이블 생성
"""

import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.database import engine, Base
from app.config import settings

# 모든 모델 임포트 (테이블 생성에 필요)
from app.models import (
    User,
    Device,
    DeviceStatus,
    AuditLog,
    ASRResult,
    EmergencyAlert,
    AlarmHistory,
)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """컬럼 존재 여부 확인"""
    inspector = inspect(engine)
    try:
        columns = [col["name"] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def check_table_exists(table_name: str) -> bool:
    """테이블 존재 여부 확인"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def migrate():
    """마이그레이션 실행"""
    print(f"Database: {settings.DB_NAME}@{settings.DB_HOST}")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. devices 테이블에 status_report_interval 컬럼 추가
        print("\n[1] devices.status_report_interval 컬럼")
        if check_column_exists("devices", "status_report_interval"):
            print("    ✓ 이미 존재함")
        else:
            print("    → 추가 중...")
            alter_sql = text(
                """
                ALTER TABLE devices 
                ADD COLUMN status_report_interval INT NOT NULL DEFAULT 60 
                COMMENT '상태 보고 주기 (초), 기본값 60초'
            """
            )
            conn.execute(alter_sql)
            conn.commit()
            print("    ✓ 추가 완료")

        # 2. alarm_history 테이블 생성
        print("\n[2] alarm_history 테이블")
        if check_table_exists("alarm_history"):
            print("    ✓ 이미 존재함")
        else:
            print("    → 생성 중...")
            create_sql = text(
                """
                CREATE TABLE alarm_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id INT NOT NULL,
                    alarm_type VARCHAR(20) NOT NULL COMMENT 'sound, text, recorded',
                    alarm_subtype VARCHAR(50) COMMENT 'beep, alert, emergency 등',
                    content TEXT COMMENT 'TTS 텍스트 또는 파일 경로',
                    triggered_by VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT 'system, admin, user, schedule',
                    triggered_user_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parameters TEXT COMMENT 'JSON 형태의 추가 파라미터',
                    status VARCHAR(20) DEFAULT 'sent' COMMENT 'sent, delivered, failed',
                    
                    INDEX idx_device_id (device_id),
                    INDEX idx_alarm_type (alarm_type),
                    INDEX idx_created_at (created_at),
                    
                    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
                    FOREIGN KEY (triggered_user_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='알람 발송 이력'
            """
            )
            conn.execute(create_sql)
            conn.commit()
            print("    ✓ 생성 완료")

    print("\n" + "=" * 60)
    print("마이그레이션 완료!")


def check_status():
    """현재 DB 스키마 상태 확인"""
    print(f"Database: {settings.DB_NAME}@{settings.DB_HOST}")
    print("=" * 60)

    inspector = inspect(engine)

    # devices 테이블 확인
    print("\n[devices] 테이블:")
    if check_table_exists("devices"):
        has_interval = check_column_exists("devices", "status_report_interval")
        print(f"    status_report_interval: {'✓ 있음' if has_interval else '✗ 없음'}")
    else:
        print("    ✗ 테이블 없음")

    # alarm_history 테이블 확인
    print("\n[alarm_history] 테이블:")
    if check_table_exists("alarm_history"):
        print("    ✓ 존재함")
        for col in inspector.get_columns("alarm_history"):
            print(f"      - {col['name']}: {col['type']}")
    else:
        print("    ✗ 없음")

    print("\n" + "=" * 60)


def create_tables():
    """SQLAlchemy 모델 기반으로 새 테이블 생성"""
    print(f"Database: {settings.DB_NAME}@{settings.DB_HOST}")
    print("=" * 60)
    print("\nSQLAlchemy 모델 기반 테이블 생성...")

    Base.metadata.create_all(bind=engine)

    print("✓ 완료")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            check_status()
        elif sys.argv[1] == "--create-tables":
            create_tables()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python migrate_db.py [--check|--create-tables]")
    else:
        migrate()
