#!/usr/bin/env python3
"""
DB 마이그레이션 스크립트: status_report_interval 컬럼 추가

사용법:
    cd backend
    python scripts/migrate_add_report_interval.py

또는:
    python scripts/migrate_add_report_interval.py --check  # 상태만 확인
"""

import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.database import engine
from app.config import settings


def check_column_exists(connection, table_name: str, column_name: str) -> bool:
    """컬럼 존재 여부 확인"""
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """마이그레이션 실행"""
    print(f"Database: {settings.DB_NAME}@{settings.DB_HOST}")
    print("-" * 50)

    with engine.connect() as conn:
        # 1. devices 테이블에 status_report_interval 컬럼 추가
        table_name = "devices"
        column_name = "status_report_interval"

        if check_column_exists(conn, table_name, column_name):
            print(f"✓ Column '{column_name}' already exists in '{table_name}'")
        else:
            print(f"Adding column '{column_name}' to '{table_name}'...")

            # MySQL ALTER TABLE
            alter_sql = text(
                """
                ALTER TABLE devices 
                ADD COLUMN status_report_interval INT NOT NULL DEFAULT 60 
                COMMENT '상태 보고 주기 (초), 기본값 60초'
            """
            )

            conn.execute(alter_sql)
            conn.commit()
            print(f"✓ Column '{column_name}' added successfully")

    print("-" * 50)
    print("Migration completed!")


def check_status():
    """현재 DB 스키마 상태 확인"""
    print(f"Database: {settings.DB_NAME}@{settings.DB_HOST}")
    print("-" * 50)

    inspector = inspect(engine)

    # devices 테이블 컬럼 출력
    print("\n[devices] Table Columns:")
    for col in inspector.get_columns("devices"):
        nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
        default = f"DEFAULT {col.get('default', 'None')}" if col.get("default") else ""
        print(f"  - {col['name']}: {col['type']} {nullable} {default}")

    print("-" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_status()
    else:
        migrate()
