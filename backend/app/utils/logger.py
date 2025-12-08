"""
로깅 유틸리티
보안 가이드라인 5 준수: 민감정보 로그 제외
"""
import logging
import sys
from pathlib import Path
from typing import Any

from app.config import settings


# 민감 정보 키워드 (로그에서 필터링)
SENSITIVE_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token",
    "secret", "api_key", "authorization", "cookie", "jwt"
}


class SensitiveDataFilter(logging.Filter):
    """민감 정보 필터링 로그 필터"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """로그 레코드에서 민감 정보 마스킹"""
        # 메시지 필터링
        if hasattr(record, 'msg'):
            msg_lower = str(record.msg).lower()
            for key in SENSITIVE_KEYS:
                if key in msg_lower:
                    record.msg = f"[FILTERED] 민감정보 포함된 로그"
                    break
        
        return True


def setup_logger(name: str = "app") -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
    
    Returns:
        logging.Logger: 설정된 로거
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (프로덕션 환경)
    if settings.ENVIRONMENT == "production":
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(file_handler)
    
    return logger


# 전역 로거 인스턴스
logger = setup_logger()


def log_audit(user_id: int, action: str, resource_type: str = None, 
               resource_id: str = None, ip_address: str = None) -> None:
    """
    감사 로그 기록 (보안 가이드라인 준수)
    
    Args:
        user_id: 사용자 ID
        action: 수행한 작업
        resource_type: 리소스 타입
        resource_id: 리소스 ID
        ip_address: IP 주소
    """
    logger.info(
        f"AUDIT: user_id={user_id}, action={action}, "
        f"resource_type={resource_type}, resource_id={resource_id}, "
        f"ip={ip_address}"
    )

