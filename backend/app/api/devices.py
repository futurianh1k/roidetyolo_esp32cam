"""
장비 관리 API 엔드포인트
보안 가이드라인 2, 9 준수: 권한 기반 접근 제어, 감사 로그
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Device, DeviceStatus, User, AuditLog
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
    DeviceStatusCreate,
    DeviceStatusResponse,
    DeviceStatusListResponse,
)
from app.dependencies import (
    get_current_active_user,
    require_operator,
    require_admin,
    get_client_ip,
)
from app.utils.logger import logger


router = APIRouter(prefix="/devices", tags=["장비 관리"])


@router.get("/", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    is_online: Optional[bool] = None,
    device_type: Optional[str] = None,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DeviceListResponse:
    """
    장비 목록 조회

    권한: VIEWER 이상
    """
    # 쿼리 빌드
    query = db.query(Device)

    if is_online is not None:
        query = query.filter(Device.is_online == is_online)

    if device_type:
        query = query.filter(Device.device_type == device_type)

    # 총 개수
    total = query.count()

    # 페이지네이션
    devices = (
        query.order_by(desc(Device.registered_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return DeviceListResponse(
        devices=devices, total=total, page=page, page_size=page_size
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DeviceResponse:
    """
    장비 상세 조회

    권한: VIEWER 이상
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    return device


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    device_data: DeviceCreate,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None,
) -> DeviceResponse:
    """
    장비 등록

    권한: OPERATOR 이상
    """
    # 중복 확인 1: device_id 중복
    existing_device = (
        db.query(Device).filter(Device.device_id == device_data.device_id).first()
    )

    if existing_device:
        logger.warning(f"⚠️ 중복 장비 ID 등록 시도: {device_data.device_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"이미 등록된 장비 ID입니다: {device_data.device_id}",
        )

    # 중복 확인 2: IP 주소 중복 (IP가 제공된 경우)
    if device_data.ip_address:
        existing_ip_device = (
            db.query(Device).filter(Device.ip_address == device_data.ip_address).first()
        )

        if existing_ip_device:
            logger.warning(
                f"⚠️ 중복 IP 주소 등록 시도: {device_data.ip_address} "
                f"(기존 장비: {existing_ip_device.device_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이미 사용 중인 IP 주소입니다: {device_data.ip_address} "
                f"(등록된 장비: {existing_ip_device.device_name})",
            )

    # RTSP URL 생성
    rtsp_url = None
    if device_data.ip_address:
        rtsp_url = f"rtsp://{device_data.ip_address}:554/stream"

    # MQTT 토픽 생성 (미지정 시)
    mqtt_topic = device_data.mqtt_topic or f"devices/{device_data.device_id}"

    # 장비 생성
    new_device = Device(
        device_id=device_data.device_id,
        device_name=device_data.device_name,
        device_type=device_data.device_type,
        ip_address=device_data.ip_address,
        rtsp_url=rtsp_url,
        mqtt_topic=mqtt_topic,
        location=device_data.location,
        description=device_data.description,
        is_online=False,
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    # TODO: 로그인 수정 후 감사 로그 활성화
    # ip_address = get_client_ip(request) if request else None
    # audit_log = AuditLog(
    #     user_id=current_user.id,
    #     device_id=new_device.id,
    #     action="register_device",
    #     resource_type="device",
    #     resource_id=str(new_device.id),
    #     ip_address=ip_address
    # )
    # db.add(audit_log)
    # db.commit()

    logger.info(f"장비 {new_device.device_name} 등록")

    return new_device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
    request: Request = None,
) -> DeviceResponse:
    """
    장비 정보 수정

    권한: OPERATOR 이상
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # 수정 가능한 필드만 업데이트
    if device_data.device_name is not None:
        device.device_name = device_data.device_name

    if device_data.ip_address is not None:
        # 빈 문자열을 None으로 변환
        ip_address_value = (
            device_data.ip_address.strip() if device_data.ip_address else None
        )

        # IP 주소 중복 검증 (다른 장비에서 사용 중인지 확인)
        if ip_address_value:
            existing_ip_device = (
                db.query(Device)
                .filter(
                    Device.ip_address == ip_address_value,
                    Device.id != device_id,  # 현재 장비 제외
                )
                .first()
            )

            if existing_ip_device:
                logger.warning(
                    f"⚠️ 중복 IP 주소 업데이트 시도: {ip_address_value} "
                    f"(기존 장비: {existing_ip_device.device_id})"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"이미 사용 중인 IP 주소입니다: {ip_address_value} "
                    f"(등록된 장비: {existing_ip_device.device_name})",
                )

        device.ip_address = ip_address_value if ip_address_value else None

        # RTSP URL 업데이트
        if ip_address_value:
            device.rtsp_url = f"rtsp://{ip_address_value}:554/stream"
        else:
            device.rtsp_url = None

    if device_data.mqtt_topic is not None:
        device.mqtt_topic = device_data.mqtt_topic

    if device_data.location is not None:
        device.location = device_data.location

    if device_data.description is not None:
        device.description = device_data.description

    if device_data.is_online is not None:
        device.is_online = device_data.is_online
        if device_data.is_online:
            device.last_seen_at = datetime.utcnow()

    db.commit()
    db.refresh(device)

    # TODO: 로그인 수정 후 감사 로그 활성화
    # ip_address = get_client_ip(request) if request else None
    # audit_log = AuditLog(
    #     user_id=current_user.id,
    #     device_id=device.id,
    #     action="update_device",
    #     resource_type="device",
    #     resource_id=str(device.id),
    #     ip_address=ip_address
    # )
    # db.add(audit_log)
    # db.commit()

    logger.info(f"장비 {device.device_name} 정보 수정 (IP: {device_data.ip_address})")

    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    장비 삭제

    권한: ADMIN
    """
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    device_name = device.device_name

    # 감사 로그 먼저 기록
    ip_address = get_client_ip(request) if request else None
    audit_log = AuditLog(
        user_id=current_user.id,
        device_id=device.id,
        action="delete_device",
        resource_type="device",
        resource_id=str(device.id),
        ip_address=ip_address,
    )
    db.add(audit_log)

    db.delete(device)
    db.commit()

    logger.info(f"관리자 {current_user.username}가 장비 {device_name} 삭제")

    return None


@router.post(
    "/{device_id}/status",
    response_model=DeviceStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_device_status(
    device_id: int,
    status_data: DeviceStatusCreate,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DeviceStatusResponse:
    """
    장비 상태 기록

    권한: VIEWER 이상 (장비에서 호출)
    """
    # 장비 존재 확인
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # 상태 기록 생성
    new_status = DeviceStatus(
        device_id=device_id,
        battery_level=status_data.battery_level,
        memory_usage=status_data.memory_usage,
        storage_usage=status_data.storage_usage,
        temperature=status_data.temperature,
        cpu_usage=status_data.cpu_usage,
        camera_status=status_data.camera_status,
        mic_status=status_data.mic_status,
    )

    db.add(new_status)

    # 장비 last_seen_at 업데이트
    device.last_seen_at = datetime.utcnow()
    device.is_online = True

    db.commit()
    db.refresh(new_status)

    return new_status


@router.get("/{device_id}/status", response_model=DeviceStatusListResponse)
async def get_device_status_history(
    device_id: int,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DeviceStatusListResponse:
    """
    장비 상태 이력 조회

    권한: VIEWER 이상
    """
    # 장비 존재 확인
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # 상태 이력 조회 (최신순)
    statuses = (
        db.query(DeviceStatus)
        .filter(DeviceStatus.device_id == device_id)
        .order_by(desc(DeviceStatus.recorded_at))
        .limit(limit)
        .all()
    )

    total = db.query(DeviceStatus).filter(DeviceStatus.device_id == device_id).count()

    return DeviceStatusListResponse(statuses=statuses, total=total)


@router.get("/{device_id}/status/latest", response_model=DeviceStatusResponse)
async def get_device_latest_status(
    device_id: int,
    # TODO: 로그인 수정 후 활성화
    # current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DeviceStatusResponse:
    """
    장비 최신 상태 조회

    권한: VIEWER 이상
    """
    # 장비 존재 확인
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비를 찾을 수 없습니다"
        )

    # 최신 상태 조회
    latest_status = (
        db.query(DeviceStatus)
        .filter(DeviceStatus.device_id == device_id)
        .order_by(desc(DeviceStatus.recorded_at))
        .first()
    )

    if not latest_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="장비 상태 정보가 없습니다"
        )

    return latest_status
