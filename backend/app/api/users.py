"""
사용자 관리 API 엔드포인트
보안 가이드라인 2, 9 준수: 권한 기반 접근 제어, 감사 로그
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, UserRole, AuditLog
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    UserListResponse,
)
from app.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
)
from app.dependencies import (
    get_current_active_user,
    require_admin,
    get_client_ip,
)
from app.utils.logger import logger


router = APIRouter(prefix="/users", tags=["사용자 관리"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> UserListResponse:
    """
    사용자 목록 조회 (관리자 전용)
    
    권한: ADMIN
    """
    # 쿼리 빌드
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # 총 개수
    total = query.count()
    
    # 페이지네이션
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    사용자 상세 조회 (관리자 전용)
    
    권한: ADMIN
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    request: Request = None
) -> UserResponse:
    """
    사용자 생성 (관리자 전용)
    
    권한: ADMIN
    보안: 비밀번호 강도 검증, BCrypt 해싱
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
    
    # 사용자 생성
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 감사 로그 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=current_user.id,
        action="create_user",
        resource_type="user",
        resource_id=str(new_user.id),
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"관리자 {current_user.username}가 사용자 {new_user.username} 생성")
    
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    request: Request = None
) -> UserResponse:
    """
    사용자 정보 수정 (관리자 전용)
    
    권한: ADMIN
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 수정 가능한 필드만 업데이트
    if user_data.email is not None:
        # 이메일 중복 확인
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일입니다"
            )
        user.email = user_data.email
    
    if user_data.role is not None:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    # 감사 로그 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update_user",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"관리자 {current_user.username}가 사용자 {user.username} 정보 수정")
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    사용자 삭제 (관리자 전용)
    
    권한: ADMIN
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신을 삭제할 수 없습니다"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    username = user.username
    
    # 감사 로그 먼저 기록 (삭제 전)
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=current_user.id,
        action="delete_user",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip_address
    )
    db.add(audit_log)
    
    db.delete(user)
    db.commit()
    
    logger.info(f"관리자 {current_user.username}가 사용자 {username} 삭제")
    
    return None


@router.put("/me/password", response_model=dict)
async def change_own_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    본인 비밀번호 변경
    
    보안: 기존 비밀번호 검증 → 새 비밀번호 정책 검증 → 해시 저장
    """
    # 기존 비밀번호 확인
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )
    
    # 새 비밀번호와 현재 비밀번호가 동일한지 확인
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호는 현재 비밀번호와 달라야 합니다"
        )
    
    # 새 비밀번호 강도 검증
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # 비밀번호 업데이트
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    # 감사 로그 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=current_user.id,
        action="change_password",
        resource_type="user",
        resource_id=str(current_user.id),
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"사용자 {current_user.username}가 비밀번호 변경")
    
    return {"message": "비밀번호가 성공적으로 변경되었습니다"}

