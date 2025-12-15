"""
DB 마이그레이션: 카메라 스트림 전송 설정 컬럼 추가

devices 테이블에 다음 컬럼을 추가합니다:
- camera_sink_url: 영상 sink URL
- camera_stream_mode: 전송 방식
- camera_frame_interval_ms: 프레임 전송 주기

사용법:
    python scripts/migrate_add_camera_sink_settings.py

또는 직접 SQL 실행:
    MySQL: scripts/migrate_add_camera_sink_settings_mysql.sql
    SQLite: scripts/migrate_add_camera_sink_settings_sqlite.sql
"""

import os
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, get_db


def check_column_exists(connection, table_name: str, column_name: str) -> bool:
    """컬럼 존재 여부 확인"""
    try:
        # MySQL
        result = connection.execute(
            text(f"SHOW COLUMNS FROM {table_name} LIKE :column"),
            {"column": column_name},
        )
        return result.fetchone() is not None
    except Exception:
        try:
            # SQLite
            result = connection.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            return column_name in columns
        except Exception as e:
            print(f"컬럼 확인 실패: {e}")
            return False


def migrate():
    """마이그레이션 실행"""
    print("=" * 60)
    print("DB 마이그레이션: 카메라 스트림 전송 설정 컬럼 추가")
    print("=" * 60)

    with engine.connect() as connection:
        # 트랜잭션 시작
        trans = connection.begin()

        try:
            # 1. camera_sink_url 컬럼 추가
            if not check_column_exists(connection, "devices", "camera_sink_url"):
                print("✅ camera_sink_url 컬럼 추가 중...")
                try:
                    # MySQL
                    connection.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN camera_sink_url VARCHAR(500) DEFAULT NULL"
                        )
                    )
                except Exception:
                    # SQLite
                    connection.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN camera_sink_url TEXT DEFAULT NULL"
                        )
                    )
                print("   ✓ camera_sink_url 추가 완료")
            else:
                print("⏭️  camera_sink_url 컬럼이 이미 존재합니다")

            # 2. camera_stream_mode 컬럼 추가
            if not check_column_exists(connection, "devices", "camera_stream_mode"):
                print("✅ camera_stream_mode 컬럼 추가 중...")
                try:
                    # MySQL
                    connection.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN camera_stream_mode VARCHAR(50) DEFAULT 'mjpeg_stills'"
                        )
                    )
                except Exception:
                    # SQLite
                    connection.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN camera_stream_mode TEXT DEFAULT 'mjpeg_stills'"
                        )
                    )
                print("   ✓ camera_stream_mode 추가 완료")
            else:
                print("⏭️  camera_stream_mode 컬럼이 이미 존재합니다")

            # 3. camera_frame_interval_ms 컬럼 추가
            if not check_column_exists(
                connection, "devices", "camera_frame_interval_ms"
            ):
                print("✅ camera_frame_interval_ms 컬럼 추가 중...")
                try:
                    # MySQL
                    connection.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN camera_frame_interval_ms INT DEFAULT 1000 NOT NULL"
                        )
                    )
                except Exception:
                    # SQLite
                    connection.execute(
                        text(
                            "ALTER TABLE devices ADD COLUMN camera_frame_interval_ms INTEGER DEFAULT 1000"
                        )
                    )
                print("   ✓ camera_frame_interval_ms 추가 완료")
            else:
                print("⏭️  camera_frame_interval_ms 컬럼이 이미 존재합니다")

            # 트랜잭션 커밋
            trans.commit()
            print("\n✅ 마이그레이션 완료!")

        except Exception as e:
            trans.rollback()
            print(f"\n❌ 마이그레이션 실패: {e}")
            raise


def print_sql_scripts():
    """SQL 스크립트 출력"""
    print("\n" + "=" * 60)
    print("수동 실행용 SQL 스크립트")
    print("=" * 60)

    print("\n--- MySQL ---")
    print(
        """
ALTER TABLE devices 
    ADD COLUMN camera_sink_url VARCHAR(500) DEFAULT NULL,
    ADD COLUMN camera_stream_mode VARCHAR(50) DEFAULT 'mjpeg_stills',
    ADD COLUMN camera_frame_interval_ms INT DEFAULT 1000 NOT NULL;
"""
    )

    print("\n--- SQLite ---")
    print(
        """
ALTER TABLE devices ADD COLUMN camera_sink_url TEXT DEFAULT NULL;
ALTER TABLE devices ADD COLUMN camera_stream_mode TEXT DEFAULT 'mjpeg_stills';
ALTER TABLE devices ADD COLUMN camera_frame_interval_ms INTEGER DEFAULT 1000;
"""
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="카메라 스트림 설정 컬럼 마이그레이션")
    parser.add_argument("--sql-only", action="store_true", help="SQL 스크립트만 출력")
    args = parser.parse_args()

    if args.sql_only:
        print_sql_scripts()
    else:
        migrate()
        print_sql_scripts()
