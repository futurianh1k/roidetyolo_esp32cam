"""
인증 의존성
보안 가이드라인 2 준수: 권한 검증
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.security import decode_token, verify_token_type
from app.schemas.auth import TokenPayload


# Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 로그인한 사용자 가져오기
    
    Args:
        credentials: Bearer 토큰
        db: 데이터베이스 세션
    
    Returns:
        User: 현재 사용자
    
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증에 실패했습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # 토큰 타입 검증
    if not verify_token_type(payload, "access"):
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # 활성 사용자 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 활성 사용자 가져오기
    
    Args:
        current_user: 현재 사용자
    
    Returns:
        User: 활성 사용자
    
    Raises:
        HTTPException: 비활성 사용자인 경우
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    return current_user


def require_role(required_role: UserRole):
    """
    특정 역할 요구 데코레이터
    보안 가이드라인 2: 권한 기반 접근 제어
    
    Args:
        required_role: 필요한 역할
    
    Returns:
        함수: 의존성 함수
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # 역할 우선순위: ADMIN > OPERATOR > VIEWER
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.OPERATOR: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="권한이 없습니다"
            )
        
        return current_user
    
    return role_checker


# 역할별 의존성
require_admin = require_role(UserRole.ADMIN)
require_operator = require_role(UserRole.OPERATOR)


def get_client_ip(request: Request) -> str:
    """
    클라이언트 IP 주소 가져오기
    
    Args:
        request: FastAPI Request 객체
    
    Returns:
        str: IP 주소
    """
    # X-Forwarded-For 헤더 확인 (프록시 뒤에 있는 경우)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # X-Real-IP 헤더 확인
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 직접 연결
    return request.client.host if request.client else "unknown"

