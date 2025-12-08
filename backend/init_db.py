"""
데이터베이스 초기화 스크립트
초기 관리자 계정 생성
"""
import sys
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, SessionLocal, Base
from app.models import User, UserRole
from app.security import get_password_hash
from app.utils.logger import logger


def init_database():
    """데이터베이스 초기화"""
    try:
        # 모든 테이블 생성
        logger.info("데이터베이스 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
        
        # 초기 관리자 계정 생성
        db = SessionLocal()
        try:
            # 기존 관리자 확인
            existing_admin = db.query(User).filter(User.username == "admin").first()
            
            if not existing_admin:
                logger.info("초기 관리자 계정 생성 중...")
                
                # 기본 관리자 계정
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=get_password_hash("Admin123!"),  # 초기 비밀번호
                    role=UserRole.ADMIN,
                    is_active=True
                )
                
                db.add(admin_user)
                db.commit()
                
                logger.info("=" * 60)
                logger.info("초기 관리자 계정이 생성되었습니다:")
                logger.info(f"  사용자명: admin")
                logger.info(f"  비밀번호: Admin123!")
                logger.info(f"  이메일: admin@example.com")
                logger.info("보안을 위해 로그인 후 반드시 비밀번호를 변경하세요!")
                logger.info("=" * 60)
            else:
                logger.info("관리자 계정이 이미 존재합니다.")
        
        finally:
            db.close()
        
        logger.info("데이터베이스 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

