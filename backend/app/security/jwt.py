"""
JWT 토큰 처리
보안 가이드라인 1-2 준수: JWT 토큰 관리
참고: python-jose 라이브러리 사용
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import hashlib

from app.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Access Token 생성
    
    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간 (기본값: 15분)
    
    Returns:
        str: JWT Access Token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Refresh Token 생성
    
    Args:
        data: 토큰에 포함할 데이터
    
    Returns:
        str: JWT Refresh Token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT 토큰 디코딩
    
    Args:
        token: JWT 토큰
    
    Returns:
        Optional[Dict]: 디코딩된 페이로드 또는 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """
    토큰 해시 생성 (DB 저장용)
    보안 가이드라인 1-2: Refresh Token은 해시로 저장
    
    Args:
        token: 원본 토큰
    
    Returns:
        str: SHA-256 해시
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    토큰 타입 검증
    
    Args:
        payload: 디코딩된 토큰 페이로드
        expected_type: 기대하는 토큰 타입 ("access" 또는 "refresh")
    
    Returns:
        bool: 토큰 타입 일치 여부
    """
    return payload.get("type") == expected_type

