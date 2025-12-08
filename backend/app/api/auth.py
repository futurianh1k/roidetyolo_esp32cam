"""
인증 API 엔드포인트
보안 가이드라인 1 준수: 인증/세션/토큰 관리
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RefreshToken, AuditLog
from app.schemas import (
    LoginRequest, 
    TokenResponse, 
    RefreshTokenRequest,
    UserCreate,
    UserResponse
)
from app.security import (
    verify_password,
    get_password_hash,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_token_type,
)
from app.dependencies import get_current_user, get_client_ip
from app.utils.logger import logger
from app.config import settings


router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    request: Request = None
) -> UserResponse:
    """
    사용자 등록
    
    보안 고려사항:
    - 비밀번호 강도 검증
    - BCrypt 해싱
    - 중복 확인
    """
    # 중복 확인
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자명 또는 이메일입니다"
        )
    
    # 비밀번호 강도 검증
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # 비밀번호 해싱 (BCrypt)
    password_hash = get_password_hash(user_data.password)
    
    # 사용자 생성
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 감사 로그 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=new_user.id,
        action="user_register",
        resource_type="user",
        resource_id=str(new_user.id),
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"새 사용자 등록: {new_user.username} (ID: {new_user.id})")
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None
) -> TokenResponse:
    """
    로그인
    
    보안 고려사항:
    - 비밀번호 검증
    - JWT 토큰 발급
    - Refresh 토큰 해시 저장
    """
    # 사용자 조회
    user = db.query(User).filter(User.username == login_data.username).first()
    
    # 사용자 없거나 비밀번호 불일치 (보안: 동일한 에러 메시지)
    if not user or not verify_password(login_data.password, user.password_hash):
        logger.warning(f"로그인 실패: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 비활성 사용자 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    
    # 토큰 생성
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user.id})
    
    # Refresh 토큰 해시 저장 (보안 가이드라인 1-2)
    token_hash = hash_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    
    # 마지막 로그인 시간 업데이트
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # 감사 로그 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"로그인 성공: {user.username} (ID: {user.id})")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    토큰 갱신
    
    보안 고려사항:
    - Refresh 토큰 검증
    - 기존 토큰 무효화
    - 새 토큰 발급
    """
    # Refresh 토큰 디코딩
    payload = decode_token(refresh_data.refresh_token)
    
    if payload is None or not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다"
        )
    
    # Refresh 토큰 해시 확인
    token_hash = hash_token(refresh_data.refresh_token)
    db_token = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 토큰입니다"
        )
    
    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 사용자입니다"
        )
    
    # 기존 토큰 무효화 (보안 가이드라인 1-2)
    db_token.revoked = True
    
    # 새 토큰 발급
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value
    }
    
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token({"sub": user.id})
    
    # 새 Refresh 토큰 저장
    new_token_hash = hash_token(new_refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=expires_at
    )
    db.add(new_db_refresh_token)
    db.commit()
    
    logger.info(f"토큰 갱신: {user.username} (ID: {user.id})")
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
) -> dict:
    """
    로그아웃
    
    보안 고려사항:
    - Refresh 토큰 무효화
    """
    # Refresh 토큰 해시 확인 및 무효화
    token_hash = hash_token(refresh_data.refresh_token)
    db_token = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.token_hash == token_hash
    ).first()
    
    if db_token:
        db_token.revoked = True
        db.commit()
    
    # 감사 로그 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=current_user.id,
        action="user_logout",
        resource_type="user",
        resource_id=str(current_user.id),
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"로그아웃: {current_user.username} (ID: {current_user.id})")
    
    return {"message": "로그아웃되었습니다"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    현재 사용자 정보 조회
    """
    return current_user

