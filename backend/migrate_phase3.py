"""
Phase 3 데이터베이스 마이그레이션 스크립트
ASR 결과 및 응급 상황 알림 테이블 생성

주의: 기존 데이터는 보존됩니다.

사용법:
    python migrate_phase3.py

PowerShell에서도 이 스크립트를 사용하는 것을 권장합니다.
"""
import sys
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect, text
from app.database import engine, Base, SessionLocal
from app.models import ASRResult, EmergencyAlert
from app.utils.logger import logger


def check_table_exists(table_name: str) -> bool:
    """테이블이 존재하는지 확인"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_tables_if_not_exists():
    """테이블이 없으면 생성"""
    try:
        # ASR 결과 테이블 확인
        if not check_table_exists("asr_results"):
            logger.info("asr_results 테이블 생성 중...")
            ASRResult.__table__.create(bind=engine, checkfirst=True)
            logger.info("✅ asr_results 테이블 생성 완료")
        else:
            logger.info("ℹ️  asr_results 테이블이 이미 존재합니다.")
        
        # 응급 상황 알림 테이블 확인
        if not check_table_exists("emergency_alerts"):
            logger.info("emergency_alerts 테이블 생성 중...")
            EmergencyAlert.__table__.create(bind=engine, checkfirst=True)
            logger.info("✅ emergency_alerts 테이블 생성 완료")
        else:
            logger.info("ℹ️  emergency_alerts 테이블이 이미 존재합니다.")
        
        # 인덱스 확인 및 생성
        inspector = inspect(engine)
        
        # asr_results 인덱스 확인
        asr_indexes = [idx['name'] for idx in inspector.get_indexes('asr_results')] if check_table_exists("asr_results") else []
        
        if 'idx_device_created' not in asr_indexes:
            logger.info("asr_results 인덱스 생성 중...")
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_device_created 
                    ON asr_results(device_id, created_at)
                """))
                conn.commit()
            logger.info("✅ idx_device_created 인덱스 생성 완료")
        
        if 'idx_emergency_created' not in asr_indexes:
            logger.info("asr_results 응급 상황 인덱스 생성 중...")
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_emergency_created 
                    ON asr_results(is_emergency, created_at)
                """))
                conn.commit()
            logger.info("✅ idx_emergency_created 인덱스 생성 완료")
        
        # emergency_alerts 인덱스 확인
        if check_table_exists("emergency_alerts"):
            alert_indexes = [idx['name'] for idx in inspector.get_indexes('emergency_alerts')]
            
            if 'idx_device_priority_created' not in alert_indexes:
                logger.info("emergency_alerts 장비/우선순위 인덱스 생성 중...")
                with engine.connect() as conn:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_device_priority_created 
                        ON emergency_alerts(device_id, priority, created_at)
                    """))
                    conn.commit()
                logger.info("✅ idx_device_priority_created 인덱스 생성 완료")
            
            if 'idx_status_created' not in alert_indexes:
                logger.info("emergency_alerts 상태 인덱스 생성 중...")
                with engine.connect() as conn:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_status_created 
                        ON emergency_alerts(status, created_at)
                    """))
                    conn.commit()
                logger.info("✅ idx_status_created 인덱스 생성 완료")
        
        logger.info("=" * 60)
        logger.info("✅ Phase 3 마이그레이션 완료!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def verify_migration():
    """마이그레이션 검증"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("=" * 60)
        logger.info("마이그레이션 검증 결과:")
        logger.info("=" * 60)
        
        # 테이블 확인
        if "asr_results" in tables:
            logger.info("✅ asr_results 테이블 존재")
            columns = [col['name'] for col in inspector.get_columns('asr_results')]
            logger.info(f"   컬럼: {', '.join(columns)}")
        else:
            logger.error("❌ asr_results 테이블 없음")
        
        if "emergency_alerts" in tables:
            logger.info("✅ emergency_alerts 테이블 존재")
            columns = [col['name'] for col in inspector.get_columns('emergency_alerts')]
            logger.info(f"   컬럼: {', '.join(columns)}")
        else:
            logger.error("❌ emergency_alerts 테이블 없음")
        
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"검증 실패: {e}")
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Phase 3 데이터베이스 마이그레이션 시작")
    logger.info("=" * 60)
    
    success = create_tables_if_not_exists()
    
    if success:
        verify_migration()
    
    sys.exit(0 if success else 1)

